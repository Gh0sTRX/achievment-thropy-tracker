param([Parameter(Mandatory=$true)][string]$PlanPath)
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

$plan=Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
$installationStarted=$false
$installationCompleted=$false
$canRelaunch=$true
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
    if (!(Test-Path (Join-Path $plan.install_dir 'unins000.exe'))) { throw 'Installed application not found' }
    if ([IO.Path]::GetFullPath($plan.exe) -ne (Join-Path ([IO.Path]::GetFullPath($plan.install_dir)) 'AchievementAtlas.exe')) { throw 'Unexpected application path' }
    Set-Content -LiteralPath $plan.ready -Value 'ready'
    Wait-Process -Id $plan.parent_pid -Timeout 120 -ErrorAction SilentlyContinue
    if (Get-Process -Id $plan.parent_pid -ErrorAction SilentlyContinue) { throw 'Application did not close; update cancelled' }
    Verify-Installer
    $inventory=Save-InstallSnapshot $plan.install_dir $plan.backup
    $args=@('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/DIR="'+$plan.install_dir+'"'),('/LOG="'+$plan.log+'"'))
    $installationStarted=$true
    $process=Start-Process -FilePath $plan.installer -ArgumentList $args -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw ('Installer failed: '+$process.ExitCode)
    }
    $installationCompleted=$true
    Start-Process -FilePath $plan.exe
    'Update installed: '+$plan.version | Add-Content -LiteralPath $plan.log
} catch {
    $updateFailure=$_.Exception.Message
    if ($installationStarted -and !$installationCompleted) {
        try {
            Restore-InstallSnapshot $plan.install_dir $plan.backup $inventory
            'Previous application files restored and verified' | Add-Content -LiteralPath $plan.log
        } catch {
            $canRelaunch=$false
            ('ROLLBACK FAILED; application not restarted. Backup: '+$plan.backup+'; '+$_.Exception.Message) | Add-Content -LiteralPath $plan.log
        }
    }
    ('Update cancelled or failed: '+$updateFailure) | Add-Content -LiteralPath $plan.log
    if ($canRelaunch -and !(Get-Process -Id $plan.parent_pid -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath $plan.exe)) {
        Start-Process -FilePath $plan.exe
    }
}
