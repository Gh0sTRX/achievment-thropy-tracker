param([string]$ReportPath='self-update-test-report.json')
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
. "$PSScriptRoot/windows_download.ps1"
$root=Join-Path $env:RUNNER_TEMP ('Atlas native self update '+[Guid]::NewGuid())
New-Item -ItemType Directory -Path $root | Out-Null
$ownsData=$false;$active=$null;$install=Join-Path $root 'installed application'
$reportFull=[IO.Path]::GetFullPath($ReportPath)
# Reuse helpers without executing the separate installer matrix entry point.
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Resolve-Path "$PSScriptRoot/test_windows_upgrade.ps1"),[ref]$tokens,[ref]$errors)
foreach ($name in @('Install-Package','Start-Atlas','Stop-Atlas','Post','Get-Records','Assert-Records')) {
    $definition=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name},$true)
    . ([ScriptBlock]::Create($definition.Extent.Text))
}
try {
    # Dedicated ephemeral GitHub Windows runner only: never overwrite existing default data.
    if (!$env:GITHUB_ACTIONS -or !$env:RUNNER_TEMP) { throw 'Native self-update test requires an ephemeral GitHub Actions runner' }
    $data=Join-Path $env:LOCALAPPDATA 'AchievementAtlas'
    if (Test-Path -LiteralPath $data) { throw 'Default data directory already exists; refusing to use or delete it' }
    New-Item -ItemType Directory -Path $data | Out-Null
    $ownsData=$true
    for ($attempt=0;$attempt -lt 3;$attempt++) {
        try {
            $manifest=Invoke-RestMethod 'https://github.com/Gh0sTRX/achievment-thropy-tracker/releases/download/development/development-manifest.json' -TimeoutSec 30
            break
        } catch {
            $response=$_.Exception.Response
            $code=if ($response) {[int]$response.StatusCode} else {0}
            if ($attempt -eq 2 -or ($code -gt 0 -and $code -lt 500 -and $code -ne 429)) { throw }
            Start-Sleep -Seconds (2*($attempt+1))
        }
    }
    # After publication exercise the exact shipped 0.15.1 -> 0.16+ native updater.
    if ([Version]$manifest.version -gt [Version]'0.15.1') {
        $baselineVersion='0.15.1';$baselineHash='dba8a8c385ee261ac59970b7ac9e6d3fb10da426af39a6d6641e2b0cecbec3e4'
    } elseif ([Version]$manifest.version -gt [Version]'0.15.0') {
        $baselineVersion='0.15.0';$baselineHash='e016ac7532a77c690a1a6a5e0f4afb0cc24a4c0b4064a54ccf4a31a0205ced09'
    } else {
        $baselineVersion='0.14.1';$baselineHash='c0169c3f10bcf2b1dd2303f8f03aa081d3d04b3456d395a3e453b13ae727be7d'
    }
    $old=Join-Path $root 'published-baseline-setup.exe'
    Get-VerifiedTestInstaller ('https://github.com/Gh0sTRX/achievment-thropy-tracker/releases/download/development/AchievementAtlas-'+$baselineVersion+'-Windows-x64-Setup.exe') $old $baselineHash
    Install-Package $old $install
    $session=Start-Atlas $install $data
    $earned="GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,UnlockDate`nSelf Update Fixture,First,https://www.trueachievements.com/a456/first-achievement,20,25,1.25,,2026-01-01`n"
    $locked="GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,Unachieveable`nSelf Update Fixture,Second,https://www.trueachievements.com/a457/second-achievement,30,40,1.35,,`n"
    Post $session '/api/import' @{earned=$earned;locked=$locked;gamertag='CI synthetic fixture'} | Out-Null
    Post $session '/api/pin' @{id='ta:457';pinned=$true} | Out-Null
    $payload=Get-Records $session;$gid=$payload.library.games[0].id
    Post $session '/api/game/notes' @{game_id=$gid;notes='Upgrade fixture note'} | Out-Null
    $oldPid=$active.Id
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    function Invoke-NativeButton([string]$Name,[int]$Seconds=60,[string[]]$AcceptedStates=@()) {
        $deadline=[DateTime]::UtcNow.AddSeconds($Seconds)
        while ([DateTime]::UtcNow -lt $deadline) {
            $script:active.Refresh()
            if ($script:active.HasExited) {
                if ('installing' -in $AcceptedStates) { return }
                throw 'Native window closed before button invocation'
            }
            try {
                if ($script:active.MainWindowHandle -ne [IntPtr]::Zero) {
                    $window=[Windows.Automation.AutomationElement]::FromHandle($script:active.MainWindowHandle)
                    $elements=$window.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
                    foreach ($element in $elements) {
                        $current=$element.Current
                        if (!$current.IsEnabled -or $current.Name.IndexOf($Name,[StringComparison]::OrdinalIgnoreCase) -lt 0) { continue }
                        if ($current.IsOffscreen) {
                            $scroll=$null
                            if ($element.TryGetCurrentPattern([Windows.Automation.ScrollItemPattern]::Pattern,[ref]$scroll)) {
                                Write-Output ('Scrolling native control: '+$current.Name)
                                $scroll.ScrollIntoView()
                                Start-Sleep -Milliseconds 100
                                $current=$element.Current
                            }
                            if ($current.IsOffscreen) { continue }
                        }
                        $invoke=$null;$expand=$null
                        if ($Name -eq 'Diğer ekranlar' -and $element.TryGetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$expand)) {
                            if ($expand.Current.ExpandCollapseState -ne [Windows.Automation.ExpandCollapseState]::Expanded) { $expand.Expand() }
                            Write-Output ('Expanded native navigation: '+$current.Name)
                            return
                        }
                        if ($element.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)) {
                            Write-Output ('Invoking native button: '+$current.Name)
                            $invoke.Invoke()
                            if (!$AcceptedStates.Count) { return }
                            # A click can race the preceding check response in the
                            # shipped UI. Require the actual operation to acknowledge
                            # before advancing, otherwise reacquire and retry the UI.
                            $ackDeadline=[DateTime]::UtcNow.AddSeconds(8)
                            while ([DateTime]::UtcNow -lt $ackDeadline) {
                                $script:active.Refresh()
                                if ($script:active.HasExited -and 'installing' -in $AcceptedStates) { return }
                                $observed=$null
                                try { $observed=Invoke-RestMethod ($session.url+'/api/status') -TimeoutSec 3 } catch { }
                                if ($observed) {
                                    if ($observed.update.state -in $AcceptedStates) { return }
                                    if ($observed.update.state -in @('blocked','error','no_release')) { throw ('Actual update failed: '+$observed.update.message) }
                                }
                                Start-Sleep -Milliseconds 200
                            }
                            break
                        }
                    }
                }
            } catch {
                $cause=$_.Exception
                while ($cause.InnerException) { $cause=$cause.InnerException }
                if ($cause -isnot [Windows.Automation.ElementNotAvailableException]) { throw }
                # Reacquire the real accessibility tree after a DOM redraw. If the
                # invocation already reached the app, observe its actual state instead
                # of clicking a second time; never issue a replacement POST here.
                if ($AcceptedStates.Count) {
                    try {
                        $observed=Invoke-RestMethod ($session.url+'/api/status') -TimeoutSec 3
                        if ($observed.update.state -in $AcceptedStates) { return }
                    } catch { }
                }
            }
            Start-Sleep -Milliseconds 400
        }
        $lastStatus=$null;try { $lastStatus=Invoke-RestMethod ($session.url+'/api/status') -TimeoutSec 3 } catch { }
        throw ('Native accessible button not available: '+$Name+'; state='+$lastStatus.update.state+'; '+$lastStatus.update.message)
    }
    if ([Version]$baselineVersion -ge [Version]'0.15.0') { Invoke-NativeButton 'Diğer ekranlar' }
    Invoke-NativeButton 'Güncellemeler'
    Invoke-NativeButton 'GÜNCELLEMELERİ KONTROL ET'
    Invoke-NativeButton 'GÜNCELLEMEYİ İNDİR' 90 -AcceptedStates @('downloading','ready')
    Invoke-NativeButton 'KUR VE YENİDEN BAŞLAT' 180 -AcceptedStates @('installing')
    @{ok=$true;driver='Windows UI Automation InvokePattern';checks=@('real native navigation','real check button','real download button','verified ready state','real install button')} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $root 'buttons.json') -Encoding UTF8
    if (!$active.WaitForExit(30000)) { throw 'Old application did not exit for update' }
    $active=$null
    $exe=Join-Path $install 'AchievementAtlas.exe'
    $deadline=[DateTime]::UtcNow.AddSeconds(150);$new=$null
    while ([DateTime]::UtcNow -lt $deadline) {
        $new=Get-CimInstance Win32_Process -Filter "Name='AchievementAtlas.exe'" | Where-Object {$_.ProcessId -ne $oldPid -and $_.ExecutablePath -eq $exe -and $_.CommandLine -notlike '*--verify-dev-update*'} | Select-Object -First 1
        if ($new) { break }
        Start-Sleep -Milliseconds 500
    }
    if (!$new) { throw 'Verified update did not restart the native app' }
    $script:active=Get-Process -Id $new.ProcessId
    # Inspect the helper-restarted process; do not start a replacement ourselves.
    $newSession=$null;$deadline=[DateTime]::UtcNow.AddSeconds(60)
    while ([DateTime]::UtcNow -lt $deadline) {
        foreach ($socket in @(Get-NetTCPConnection -OwningProcess $active.Id -State Listen -ErrorAction SilentlyContinue)) {
            if ($socket.LocalAddress -ne '127.0.0.1') { continue }
            try {
                $url='http://127.0.0.1:'+$socket.LocalPort
                $status=Invoke-RestMethod ($url+'/api/data') -TimeoutSec 3
                if ($status.update.current -eq $manifest.version) { $newSession=@{url=$url};break }
            } catch { }
        }
        if ($newSession) { break }
        Start-Sleep -Milliseconds 300
    }
    if (!$newSession) { throw 'Restarted app did not report published version' }
    Assert-Records (Get-Records $newSession) $gid
    Stop-Atlas
    $plans=@(Get-ChildItem -LiteralPath (Join-Path $data 'updates') -Filter plan.json -Recurse)
    if ($plans.Count -ne 1) { throw 'Expected exactly one real update plan' }
    $plan=Get-Content -LiteralPath $plans[0].FullName -Raw | ConvertFrom-Json
    $log=Get-Content -LiteralPath $plan.log -Raw
    if (!$log.Contains('Update installed: '+$manifest.version)) { throw 'Helper did not report successful installation' }
    $proof=Get-Content -LiteralPath $plan.verify_report -Raw | ConvertFrom-Json
    if (!$proof.verified -or $proof.sha256 -ne $manifest.sha256) { throw 'Published installer provenance did not verify' }
    @{ok=$true;from=$baselineVersion;to=$manifest.version;run_id=$manifest.run_id;sha256=$proof.sha256;scope='Unmodified shipped updater; real native UI Automation buttons, GitHub metadata/download/proof, helper, installer and native restart; isolated default data directory';buttons=(Get-Content -LiteralPath (Join-Path $root 'buttons.json') -Raw | ConvertFrom-Json);records_preserved=$true} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportFull -Encoding UTF8
    Write-Output ('Native self-update passed: '+$baselineVersion+' -> '+$manifest.version)
} catch {
    if ($active) { $active.Refresh();Write-Output ('Native window at failure: '+$active.MainWindowTitle) }
    @{ok=$false;error=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath $reportFull -Encoding UTF8
    throw
} finally {
    if ($active -and !$active.HasExited) { $active.Kill();$active.WaitForExit(10000) | Out-Null }
    if (Test-Path -LiteralPath (Join-Path $install 'unins000.exe')) { Start-Process (Join-Path $install 'unins000.exe') -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -Wait | Out-Null }
    if ($ownsData) { Remove-Item -LiteralPath $data -Recurse -Force }
    Remove-Item -LiteralPath $root -Recurse -Force
}
