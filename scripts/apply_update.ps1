param([string]$PlanPath=(Join-Path $PSScriptRoot 'plan.json'),[switch]$Recover)
$ErrorActionPreference='Stop'
function Get-InstallInventory([string]$Directory) {
    $root=[IO.Path]::GetFullPath($Directory).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $rootItem=Get-Item -LiteralPath $root -Force
    $items=@($rootItem)+@(Get-ChildItem -LiteralPath $root -Recurse -Force)
    foreach ($item in $items) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Installation contains a reparse point; update cancelled' }
    }
    @($items | Where-Object { $_.FullName -ne $root } | ForEach-Object {
        $entry=@{path=$_.FullName.Substring($root.Length+1);directory=[bool]$_.PSIsContainer}
        if (!$_.PSIsContainer) { $entry.sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
        [PSCustomObject]$entry
    })
}
function Assert-SnapshotMatches([string]$Directory, $Expected) {
    $actual=@(Get-InstallInventory $Directory)
    if ($actual.Count -ne @($Expected).Count) { throw 'Installation snapshot entry count mismatch' }
    $index=@{}
    foreach ($entry in $actual) { $index[$entry.path]=$entry }
    foreach ($entry in $Expected) {
        $found=$index[$entry.path]
        if (!$found -or $found.directory -ne $entry.directory -or (!$entry.directory -and $found.sha256 -ne $entry.sha256)) { throw 'Installation snapshot content mismatch' }
    }
}
function Save-InstallSnapshot([string]$InstallDirectory,[string]$BackupDirectory) {
    $install=[IO.Path]::GetFullPath($InstallDirectory).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $backup=[IO.Path]::GetFullPath($BackupDirectory).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if ($backup -eq $install -or $backup.StartsWith($install+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Backup must be outside installation' }
    if (Test-Path -LiteralPath $backup) { throw 'Backup already exists; preserve previous recovery files' }
    $inventory=@(Get-InstallInventory $install)
    New-Item -ItemType Directory -Path $backup | Out-Null
    foreach ($item in Get-ChildItem -LiteralPath $install -Force) {
        Copy-Item -LiteralPath $item.FullName -Destination $backup -Recurse -Force
    }
    Assert-SnapshotMatches $backup $inventory
    return ,$inventory
}
function Restore-InstallSnapshot([string]$InstallDirectory,[string]$BackupDirectory,$Inventory) {
    # Verify the entire backup BEFORE deleting any installed file.
    Assert-SnapshotMatches $BackupDirectory $Inventory
    if (!(Test-Path -LiteralPath $InstallDirectory)) { New-Item -ItemType Directory -Path $InstallDirectory | Out-Null }
    $current=@(Get-InstallInventory $InstallDirectory)
    $expected=@{}
    foreach ($entry in $Inventory) { $expected[$entry.path]=$entry }
    foreach ($entry in $current | Sort-Object { $_.path.Length } -Descending) {
        $original=$expected[$entry.path]
        if (!$original -or $original.directory -ne $entry.directory) {
            Remove-Item -LiteralPath (Join-Path $InstallDirectory $entry.path) -Recurse -Force
        }
    }
    foreach ($item in Get-ChildItem -LiteralPath $BackupDirectory -Force) {
        Copy-Item -LiteralPath $item.FullName -Destination $InstallDirectory -Recurse -Force
    }
    Assert-SnapshotMatches $InstallDirectory $Inventory
}

function Write-RecoveryState($State) {
    $temporary=$script:journalPath+'.'+[Guid]::NewGuid()+'.tmp'
    $previous=$temporary+'.previous'
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($State | ConvertTo-Json -Depth 8))
    try {
        $stream=[IO.File]::Open($temporary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try { $stream.Write($bytes,0,$bytes.Length);$stream.Flush($true) } finally { $stream.Dispose() }
        if ([IO.File]::Exists($script:journalPath)) { [IO.File]::Replace($temporary,$script:journalPath,$previous) }
        else { [IO.File]::Move($temporary,$script:journalPath) }
    } finally {
        if ([IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) }
        if ([IO.File]::Exists($previous)) { [IO.File]::Delete($previous) }
    }
}
function Recovery-HookName {
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $digest=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($PlanPath))))).Replace('-','').Substring(0,16) }
    finally { $sha.Dispose() }
    return '!AchievementAtlasRecovery-'+$digest
}
function Register-RecoveryHook([string]$HelperPath=$PSCommandPath) {
    $helperFull=[IO.Path]::GetFullPath($HelperPath)
    $install=[IO.Path]::GetFullPath($plan.install_dir).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if ($helperFull.StartsWith($install+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Recovery helper must be outside installation' }
    $command='powershell.exe -NoProfile -NonInteractive -File "'+$HelperPath+'" -Recover'
    if ([IO.Path]::GetFullPath($PlanPath) -ne (Join-Path (Split-Path -Parent $HelperPath) 'plan.json')) { $command+=' -PlanPath "'+$PlanPath+'"' }
    if ($command.Length -gt 260) { throw 'Recovery command exceeds Windows RunOnce limit; installation cancelled' }
    $key='HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce'
    if (!(Test-Path -LiteralPath $key)) { New-Item -Path $key | Out-Null }
    New-ItemProperty -Path $key -Name (Recovery-HookName) -Value $command -PropertyType String -Force | Out-Null
    $actual=Get-ItemPropertyValue -Path $key -Name (Recovery-HookName)
    if ($actual -ne $command) { throw 'Windows recovery hook could not be verified' }
}
function Remove-RecoveryHook {
    $key='HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce'
    Remove-ItemProperty -Path $key -Name (Recovery-HookName) -ErrorAction SilentlyContinue
}
function Validate-RecoveryState($State) {
    if ($State.format -ne 'atlas-update-recovery-v1' -or $State.state -notin @('pending','completed','rolled_back')) { throw 'Invalid update recovery state' }
    if ($State.install_dir -ne [IO.Path]::GetFullPath($plan.install_dir) -or $State.backup -ne [IO.Path]::GetFullPath($plan.backup)) { throw 'Recovery paths differ from original plan' }
    $install=[IO.Path]::GetFullPath($plan.install_dir).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $directory=[IO.Path]::GetFullPath((Split-Path -Parent $PlanPath)).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if ([IO.Path]::GetFullPath($plan.exe) -ne (Join-Path $install 'AchievementAtlas.exe')) { throw 'Unexpected recovery executable' }
    if ($directory -eq $install -or $directory.StartsWith($install+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Recovery files must be outside installation' }
    if ([IO.Path]::GetFullPath($plan.backup) -ne (Join-Path $directory 'previous-version')) { throw 'Unexpected recovery backup location' }
    if ($plan.data_dir) {
        $data=[IO.Path]::GetFullPath($plan.data_dir).TrimEnd([IO.Path]::DirectorySeparatorChar)
        if ($data -eq $install -or $data.StartsWith($install+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'User data cannot be inside installation' }
    }
    if (@($State.inventory).Count -lt 2) { throw 'Recovery inventory is incomplete' }
    foreach ($file in @('AchievementAtlas.exe','unins000.exe')) {
        if (@($State.inventory | Where-Object {$_.path -eq $file -and !$_.directory -and $_.sha256 -match '^[A-Fa-f0-9]{64}$'}).Count -ne 1) { throw 'Required recovery executable missing from inventory' }
    }
}
function Finish-RecoveryState([string]$Status) {
    $script:recoveryState.state=$Status
    Write-RecoveryState $script:recoveryState
    try { Remove-RecoveryHook } catch { 'Recovery hook cleanup deferred' | Add-Content -LiteralPath $plan.log }
}
function Resume-InterruptedUpdate {
    $script:recoveryState=Get-Content -LiteralPath $script:journalPath -Raw -Encoding UTF8 | ConvertFrom-Json
    Validate-RecoveryState $script:recoveryState
    if ($script:recoveryState.state -ne 'pending') { Remove-RecoveryHook;return }
    $running=@(Get-Process -Name AchievementAtlas -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $plan.exe})
    if ($running.Count) { throw 'Application is running; recovery deferred without changing files' }
    Restore-InstallSnapshot $plan.install_dir $plan.backup $script:recoveryState.inventory
    Finish-RecoveryState 'rolled_back'
    'Interrupted update recovered; old files verified' | Add-Content -LiteralPath $plan.log
    Start-UpdatedApplication
}

$PlanPath=[IO.Path]::GetFullPath($PlanPath)
$script:journalPath=Join-Path (Split-Path -Parent $PlanPath) 'recovery-state.json'
$script:recoveryState=$null
$plan=Get-Content -LiteralPath $PlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
$installationStarted=$false
$installationCompleted=$false
$canRelaunch=$true
function Start-UpdatedApplication {
    if ($plan.data_dir) {
        Start-Process -FilePath $plan.exe -ArgumentList '--data-dir',('"'+$plan.data_dir+'"')
    } else {
        # Compatibility with plans made by older versions.
        Start-Process -FilePath $plan.exe
    }
}
function Verify-Installer {
    if ((Get-FileHash -LiteralPath $plan.installer -Algorithm SHA256).Hash.ToLower() -ne $plan.sha256) { throw 'Installer hash changed' }
    if ($plan.mode -eq 'development') {
        $verifyArgs=@('--verify-dev-update','--manifest',('"'+$plan.manifest+'"'),'--bundle',('"'+$plan.bundle+'"'),'--installer',('"'+$plan.installer+'"'),'--verification-report',('"'+$plan.verify_report+'"'))
        $verification=Start-Process -FilePath $plan.exe -ArgumentList $verifyArgs -Wait -PassThru
        if ($verification.ExitCode -ne 0 -or !(Test-Path -LiteralPath $plan.verify_report)) { throw 'GitHub build provenance verification failed' }
        $result=Get-Content -LiteralPath $plan.verify_report -Raw | ConvertFrom-Json
        if (!$result.verified -or $result.sha256 -ne $plan.sha256) { throw 'Development artifact identity mismatch' }
    } else {
        $signature=Get-AuthenticodeSignature -LiteralPath $plan.installer
        if ($signature.Status -ne 'Valid' -or !$signature.SignerCertificate) { throw 'Invalid installer signature' }
        $sha=[Security.Cryptography.SHA256]::Create()
        $digest=([BitConverter]::ToString($sha.ComputeHash($signature.SignerCertificate.RawData))).Replace('-','').ToLower()
        if ($digest -ne $plan.signer_sha256) { throw 'Publisher changed' }
    }
}
try {
    if ($Recover) { Resume-InterruptedUpdate;return }
    if (Test-Path -LiteralPath $script:journalPath) { throw 'Recovery state already exists; recover the previous attempt before retrying' }
    if (!(Test-Path (Join-Path $plan.install_dir 'unins000.exe'))) { throw 'Installed application not found' }
    if ([IO.Path]::GetFullPath($plan.exe) -ne (Join-Path ([IO.Path]::GetFullPath($plan.install_dir)) 'AchievementAtlas.exe')) { throw 'Unexpected application path' }
    Set-Content -LiteralPath $plan.ready -Value 'ready'
    Wait-Process -Id $plan.parent_pid -Timeout 120 -ErrorAction SilentlyContinue
    if (Get-Process -Id $plan.parent_pid -ErrorAction SilentlyContinue) { throw 'Application did not close; update cancelled' }
    Verify-Installer
    $inventory=Save-InstallSnapshot $plan.install_dir $plan.backup
    $script:recoveryState=@{format='atlas-update-recovery-v1';state='pending';install_dir=[IO.Path]::GetFullPath($plan.install_dir);backup=[IO.Path]::GetFullPath($plan.backup);inventory=$inventory}
    Validate-RecoveryState $script:recoveryState
    Write-RecoveryState $script:recoveryState
    Register-RecoveryHook
    $args=@('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/DIR="'+$plan.install_dir+'"'),('/LOG="'+$plan.log+'"'))
    $installationStarted=$true
    $process=Start-Process -FilePath $plan.installer -ArgumentList $args -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw ('Installer failed: '+$process.ExitCode)
    }
    Finish-RecoveryState 'completed'
    $installationCompleted=$true
    Start-UpdatedApplication
    'Update installed: '+$plan.version | Add-Content -LiteralPath $plan.log
} catch {
    $updateFailure=$_.Exception.Message
    if ($Recover) {
        ('RECOVERY FAILED; files retained. Backup: '+$plan.backup+'; '+$updateFailure) | Add-Content -LiteralPath $plan.log
        throw
    }
    if ($installationStarted -and !$installationCompleted) {
        try {
            Restore-InstallSnapshot $plan.install_dir $plan.backup $inventory
            Finish-RecoveryState 'rolled_back'
            'Previous application files restored and verified' | Add-Content -LiteralPath $plan.log
        } catch {
            $canRelaunch=$false
            ('ROLLBACK FAILED; application not restarted. Backup: '+$plan.backup+'; '+$_.Exception.Message) | Add-Content -LiteralPath $plan.log
        }
    }
    if (!$installationStarted -and $script:recoveryState) { try { Remove-RecoveryHook } catch { } }
    ('Update cancelled or failed: '+$updateFailure) | Add-Content -LiteralPath $plan.log
    if ($canRelaunch -and !(Get-Process -Id $plan.parent_pid -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath $plan.exe)) {
        Start-UpdatedApplication
    }
}
