param([Parameter(Mandatory=$true)][string]$SetupPath,[string]$ReportPath='upgrade-test-report.json')
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
. "$PSScriptRoot/windows_download.ps1"
if ([Environment]::OSVersion.Platform -ne 'Win32NT') { throw 'Real installer upgrade tests require Windows' }
$SetupPath=(Resolve-Path -LiteralPath $SetupPath).Path
$candidateManifest=Get-Content -LiteralPath (Join-Path (Split-Path -Parent $SetupPath) 'update-manifest.json') -Raw | ConvertFrom-Json
$expectedVersion=$candidateManifest.version
$reportFull=[IO.Path]::GetFullPath($ReportPath)
$root=Join-Path $env:RUNNER_TEMP ('Atlas upgrade matrix '+[Guid]::NewGuid())
New-Item -ItemType Directory -Path $root | Out-Null
$results=@();$active=$null;$install=$null
$testHooks=@();$runOnce='HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce'
# Use exactly the production snapshot functions. Do not execute the helper entry point.
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Resolve-Path "$PSScriptRoot/../scripts/apply_update.ps1"),[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'Update helper parse failure' }
foreach ($name in @('Get-InstallInventory','Assert-SnapshotMatches','Save-InstallSnapshot','Restore-InstallSnapshot')) {
    $definition=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name},$true)
    . ([ScriptBlock]::Create($definition.Extent.Text))
}
function Install-Package([string]$Package,[string]$Directory) {
    $p=Start-Process -FilePath $Package -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/DIR=`"$Directory`"" -PassThru
    if (!$p.WaitForExit(120000)) { $p.Kill();throw 'Installer timeout' }
    if ($p.ExitCode -ne 0) { throw "Installer exit $($p.ExitCode)" }
}
function Start-Atlas([string]$Directory,[string]$DataDirectory) {
    $script:active=Start-Process -FilePath (Join-Path $Directory 'AchievementAtlas.exe') -ArgumentList '--data-dir',"`"$DataDirectory`"" -PassThru
    $deadline=[DateTime]::UtcNow.AddSeconds(60)
    while ([DateTime]::UtcNow -lt $deadline) {
        $script:active.Refresh()
        if ($script:active.HasExited) { throw 'Installed native application exited before API startup' }
        foreach ($socket in @(Get-NetTCPConnection -OwningProcess $script:active.Id -State Listen -ErrorAction SilentlyContinue)) {
            if ($socket.LocalAddress -ne '127.0.0.1') { continue }
            $url='http://127.0.0.1:'+$socket.LocalPort
            try {
                $html=(Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 3).Content
                $match=[regex]::Match($html,'data-token="([A-Za-z0-9_-]+)"')
                if ($match.Success) { return @{url=$url;token=$match.Groups[1].Value} }
            } catch { }
        }
        Start-Sleep -Milliseconds 300
    }
    throw 'Native application local API did not become ready'
}
function Stop-Atlas {
    if (!$script:active) { return }
    # The real native window must have become visible before closing it.
    $deadline=[DateTime]::UtcNow.AddSeconds(30)
    do {
        $script:active.Refresh()
        if ($script:active.HasExited) { throw 'Native application unexpectedly closed' }
        if ($script:active.MainWindowHandle -ne [IntPtr]::Zero -and $script:active.CloseMainWindow()) { break }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    if (!$script:active.WaitForExit(30000)) { throw 'Native application did not close cleanly' }
    $script:active=$null
}
function Post($Session,[string]$Path,$Body) {
    Invoke-RestMethod -Uri ($Session.url+$Path) -Method Post -ContentType 'application/json' -Headers @{'X-Atlas-Token'=$Session.token;'Origin'=$Session.url} -Body ($Body | ConvertTo-Json -Depth 20 -Compress)
}
function Get-Records($Session) {
    # /api/data wraps the Library payload under its own library property.
    return (Invoke-RestMethod ($Session.url+'/api/data')).library
}
function Assert-Records($Payload,[string]$GameId) {
    if (@($Payload.library.achievements).Count -ne 2 -or @($Payload.library.games).Count -ne 1) { throw 'Upgrade changed record counts' }
    $earned=@($Payload.library.achievements | Where-Object {$_.id -eq 'ta:456'})
    if ($earned.Count -ne 1 -or !$earned[0].unlocked) { throw 'Earned identity/state was lost' }
    if ('ta:457' -notin $Payload.state.pins) { throw 'Pinned achievement was lost' }
    $game=$Payload.library.games[0]
    if ($game.id -ne $GameId -or $game.notes -ne 'Upgrade fixture note') { throw 'Game ID or notes changed' }
    if ($game.platform -ne 'xbox') { throw 'Platform identity changed' }
}
try {
    foreach ($baseline in @(
        @{version='0.13.0';sha='6e459970d45f04334f5d65300a8ce98261736d712e8996e01108b2dfef85e5d2'},
        @{version='0.14.1';sha='c0169c3f10bcf2b1dd2303f8f03aa081d3d04b3456d395a3e453b13ae727be7d'},
        @{version='0.15.0';sha='e016ac7532a77c690a1a6a5e0f4afb0cc24a4c0b4064a54ccf4a31a0205ced09'},
        @{version='0.15.1';sha='dba8a8c385ee261ac59970b7ac9e6d3fb10da426af39a6d6641e2b0cecbec3e4'}
    )) {
        Write-Output ('Upgrade matrix baseline '+$baseline.version)
        $case=Join-Path $root $baseline.version
        New-Item -ItemType Directory -Path $case | Out-Null
        $old=Join-Path $case 'baseline-setup.exe'
        $url='https://github.com/Gh0sTRX/achievment-thropy-tracker/releases/download/development/AchievementAtlas-'+$baseline.version+'-Windows-x64-Setup.exe'
        Get-VerifiedTestInstaller $url $old $baseline.sha
        $install=Join-Path $case 'installed application';$data=Join-Path $case 'separate user data'
        Install-Package $old $install
        $session=Start-Atlas $install $data
        $earned="GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,UnlockDate`nUpgrade Fixture,First,https://www.trueachievements.com/a456/first-achievement,20,25,1.25,,2026-01-01`n"
        $locked="GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,Unachieveable`nUpgrade Fixture,Second,https://www.trueachievements.com/a457/second-achievement,30,40,1.35,,`n"
        Post $session '/api/import' @{earned=$earned;locked=$locked;gamertag='CI synthetic fixture'} | Out-Null
        Post $session '/api/pin' @{id='ta:457';pinned=$true} | Out-Null
        $before=Get-Records $session;$gid=$before.library.games[0].id
        Post $session '/api/game/notes' @{game_id=$gid;notes='Upgrade fixture note'} | Out-Null
        Assert-Records (Get-Records $session) $gid
        if ($baseline.version -in @('0.15.0','0.15.1')) {
            # Verify the shipped Foundation navigation before promotion as well.
            Add-Type -AssemblyName UIAutomationClient
            Add-Type -AssemblyName UIAutomationTypes
            $navigationTokens=$null;$navigationErrors=$null
            $navigationAst=[Management.Automation.Language.Parser]::ParseFile((Resolve-Path "$PSScriptRoot/test_windows_self_update.ps1"),[ref]$navigationTokens,[ref]$navigationErrors)
            if ($navigationErrors.Count) { throw 'Native update navigation parser failed' }
            $navigationFunction=$navigationAst.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Invoke-NativeButton'},$true)
            . ([ScriptBlock]::Create($navigationFunction.Extent.Text))
            Invoke-NativeButton ('Di'+[char]0x011F+'er ekranlar')
            Invoke-NativeButton ('G'+[char]0x00FC+'ncellemeler')
        }
        Stop-Atlas
        # Sentinel outside the installation must survive upgrade/rollback/uninstall byte-for-byte.
        $sentinel=Join-Path $data 'profile-history-sentinel.bin'
        [IO.File]::WriteAllBytes($sentinel,[byte[]](0,1,2,255))
        $sentinelHash=(Get-FileHash -LiteralPath $sentinel).Hash
        $backup=Join-Path $case 'verified previous version'
        $inventory=Save-InstallSnapshot $install $backup
        Write-Output ('Installing candidate over '+$baseline.version)
        Install-Package $SetupPath $install
        # Real Inno upgrade followed by intentional file-tree rollback (not a simulated installer failure).
        Write-Output 'Restoring verified old installation snapshot'
        Restore-InstallSnapshot $install $backup $inventory
        $selfReport=Join-Path $case 'rolled-back-self-test.json'
        $p=Start-Process -FilePath (Join-Path $install 'AchievementAtlas.exe') -ArgumentList '--self-test','--report',"`"$selfReport`"" -Wait -PassThru
        if ($p.ExitCode -ne 0 -or (Get-Content -LiteralPath $selfReport -Raw | ConvertFrom-Json).version -ne $baseline.version) { throw 'Restored old executable self-test/version failed' }
        $session=Start-Atlas $install $data
        Assert-Records (Get-Records $session) $gid
        Stop-Atlas
        Write-Output ('Installing candidate over '+$baseline.version)
        Install-Package $SetupPath $install
        $newReport=Join-Path $case 'upgraded-self-test.json'
        $p=Start-Process -FilePath (Join-Path $install 'AchievementAtlas.exe') -ArgumentList '--self-test','--report',"`"$newReport`"" -Wait -PassThru
        if ($p.ExitCode -ne 0 -or (Get-Content -LiteralPath $newReport -Raw | ConvertFrom-Json).version -ne $expectedVersion) { throw 'Upgraded executable self-test/version failed' }
        $session=Start-Atlas $install $data
        Assert-Records (Get-Records $session) $gid
        # A real write through the new installed application followed by a restart.
        Post $session '/api/pin' @{id='ta:456';pinned=$true} | Out-Null
        Stop-Atlas
        $session=Start-Atlas $install $data
        $after=Get-Records $session;Assert-Records $after $gid
        if ('ta:456' -notin $after.state.pins) { throw 'New-version write did not survive restart' }
        Stop-Atlas
        if (!(Test-Path -LiteralPath $runOnce)) { New-Item -Path $runOnce | Out-Null }
        $recoveryHook='!AchievementAtlasRecovery-'+[Guid]::NewGuid()
        $unrelatedHook='AtlasUninstallSentinel-'+[Guid]::NewGuid()
        $testHooks+=@($recoveryHook,$unrelatedHook)
        New-ItemProperty -Path $runOnce -Name $recoveryHook -Value 'cmd.exe /c exit 0' -PropertyType String | Out-Null
        New-ItemProperty -Path $runOnce -Name $unrelatedHook -Value 'cmd.exe /c exit 0' -PropertyType String | Out-Null
        $p=Start-Process -FilePath (Join-Path $install 'unins000.exe') -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -Wait -PassThru
        if ($p.ExitCode -ne 0) { throw 'Upgrade uninstall failed' }
        if ($null -ne (Get-ItemProperty -Path $runOnce).$recoveryHook) { throw 'Uninstall left automatic recovery scheduled' }
        if ((Get-ItemPropertyValue -Path $runOnce -Name $unrelatedHook) -ne 'cmd.exe /c exit 0') { throw 'Uninstall removed unrelated RunOnce value' }
        Remove-ItemProperty -Path $runOnce -Name $unrelatedHook

        if ((Get-FileHash -LiteralPath $sentinel).Hash -ne $sentinelHash) { throw 'External user data changed' }
        if (!(Test-Path -LiteralPath (Join-Path $data 'library.json'))) { throw 'Uninstall removed user library' }
        Write-Output ('Upgrade/rollback passed: '+$baseline.version)
        $results+=@{baseline=$baseline.version;ok=$true;checks=@('pinned baseline checksum','native old application API import','real Inno in-place upgrade','verified intentional file rollback','old executable version and restart','new native restart and writes','external data survives uninstall')}
        $install=$null
    }
    @{ok=$true;scope='GitHub Windows runner, synthetic records, real published installers; no physical device or live provider accounts';cases=$results} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportFull -Encoding UTF8
} catch {
    @{ok=$false;baseline=$baseline.version;error=$_.Exception.Message;completed=$results} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportFull -Encoding UTF8
    throw
} finally {
    if ($active -and !$active.HasExited) { $active.Kill();$active.WaitForExit(10000) | Out-Null }
    if ($install -and (Test-Path -LiteralPath (Join-Path $install 'unins000.exe'))) {
        Start-Process -FilePath (Join-Path $install 'unins000.exe') -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -Wait | Out-Null
    }
    foreach ($hook in $testHooks) { Remove-ItemProperty -Path $runOnce -Name $hook -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $root -Recurse -Force
}
