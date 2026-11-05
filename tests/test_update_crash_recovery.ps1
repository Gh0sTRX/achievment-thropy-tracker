$ErrorActionPreference='Stop'
$helper=(Resolve-Path "$PSScriptRoot/../scripts/apply_update.ps1").Path
$root=Join-Path ([IO.Path]::GetTempPath()) ('atlas-crash-'+[Guid]::NewGuid())
New-Item -ItemType Directory -Path $root | Out-Null
$windows=[Environment]::OSVersion.Platform -eq 'Win32NT'
$shell=(Get-Process -Id $PID).Path
# Use the real registry provider in an isolated key: Windows consumes real RunOnce values at sign-in.
$registryRoot='HKCU:\Software\AchievementAtlas\Tests\Recovery-'+[Guid]::NewGuid()
$registry=$registryRoot+'\RunOnce'
$sentinel='AtlasRecoveryTest-'+[Guid]::NewGuid()
$child=$null;$hookNames=@();$passed=0
function Assert($Condition,[string]$Message) { if (!$Condition) { throw $Message } }
function Wait-Exit($Process) {
    if (!$Process.WaitForExit(30000)) { $Process.Kill();throw 'Child recovery timed out' }
    $Process.WaitForExit()
}
try {
    if ($windows) {
        if (!(Test-Path -LiteralPath $registry)) { New-Item -Path $registry -Force | Out-Null }
        New-ItemProperty -Path $registry -Name $sentinel -Value 'preserve unrelated value' -PropertyType String | Out-Null
    }
    foreach ($scenario in @('pending','missing-install','damaged-backup','running-app','corrupt-state','path-mismatch','missing-backup','completed')) {
        $case=Join-Path $root $scenario;New-Item -ItemType Directory -Path $case | Out-Null
        $install=Join-Path $case 'install';New-Item -ItemType Directory -Path $install | Out-Null
        [IO.File]::WriteAllText((Join-Path $install 'AchievementAtlas.exe'),'old-executable')
        [IO.File]::WriteAllText((Join-Path $install 'unins000.exe'),'old-uninstaller')
        $plan=@{install_dir=$install;exe=(Join-Path $install 'AchievementAtlas.exe');data_dir=(Join-Path $case 'separate data');backup=(Join-Path $case 'previous-version');installer=(Join-Path $case 'setup.exe');mode='development';sha256='';verify_report=(Join-Path $case 'verify.json');manifest='unused';bundle='unused';parent_pid=99999999;ready=(Join-Path $case 'ready');log=(Join-Path $case 'update.log');version='fixture'}
        [IO.File]::WriteAllText($plan.installer,'fake installer')
        $plan.sha256=(Get-FileHash -LiteralPath $plan.installer).Hash.ToLower()
        $planPath=Join-Path $case 'plan.json';$plan | ConvertTo-Json | Set-Content -LiteralPath $planPath -Encoding UTF8
        $sha=[Security.Cryptography.SHA256]::Create()
        $hook='!AchievementAtlasRecovery-'+([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($planPath))))).Replace('-','').Substring(0,16);$sha.Dispose()
        $hookNames+=$hook
        $copied=Join-Path $case 'apply-update.ps1'
        # Test-only diagnostic context; production helper and failure semantics are unchanged.
        $diagnosticHelper=(Get-Content -LiteralPath $helper -Raw).Replace('$updateFailure=$_.Exception.Message','$updateFailure=$_.Exception.Message+"; trace: "+$_.ScriptStackTrace')
        Set-Content -LiteralPath $copied -Value $diagnosticHelper -Encoding UTF8
        $wrapper=Join-Path $case 'driver.ps1'
        @'
param([string]$Helper,[string]$Plan,[string]$RegistryPath,[switch]$Recover)
$ErrorActionPreference='Stop'
$global:testPlan=Get-Content -LiteralPath $Plan -Raw -Encoding UTF8 | ConvertFrom-Json
$global:testRoot=Split-Path -Parent $Plan
if ([Environment]::OSVersion.Platform -eq 'Win32NT') {
    $global:testRegistry=$RegistryPath
    function Map-TestRegistry($Path) {
        if ($Path -eq 'HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce') { return $global:testRegistry }
        return $Path
    }
    function Test-Path { param($LiteralPath,$Path)
        if ($PSBoundParameters.ContainsKey('LiteralPath')) { return Microsoft.PowerShell.Management\Test-Path -LiteralPath (Map-TestRegistry $LiteralPath) }
        Microsoft.PowerShell.Management\Test-Path -Path (Map-TestRegistry $Path)
    }
    function New-Item { param($Path,$ItemType,[switch]$Force)
        if ($PSBoundParameters.ContainsKey('ItemType')) { Microsoft.PowerShell.Management\New-Item -Path (Map-TestRegistry $Path) -ItemType $ItemType -Force:$Force }
        else { Microsoft.PowerShell.Management\New-Item -Path (Map-TestRegistry $Path) -Force:$Force }
    }
    function Get-Item { param($LiteralPath,[switch]$Force) Microsoft.PowerShell.Management\Get-Item -LiteralPath (Map-TestRegistry $LiteralPath) -Force:$Force }
    function New-ItemProperty { param($Path,$Name,$Value,$PropertyType,[switch]$Force) Microsoft.PowerShell.Management\New-ItemProperty -Path (Map-TestRegistry $Path) -Name $Name -Value $Value -PropertyType $PropertyType -Force:$Force }
    function Get-ItemPropertyValue { param($Path,$Name) Microsoft.PowerShell.Management\Get-ItemPropertyValue -Path (Map-TestRegistry $Path) -Name $Name }
    function Remove-ItemProperty { param($Path,$Name,$ErrorAction) Microsoft.PowerShell.Management\Remove-ItemProperty -Path (Map-TestRegistry $Path) -Name $Name -ErrorAction $ErrorAction }
} else {
    $global:testHooks=@{}
    function New-Item { param($Path,$ItemType,[switch]$Force) if ($Path -like 'HKCU:*') { return };Microsoft.PowerShell.Management\New-Item @PSBoundParameters }
    function Get-Item { param($LiteralPath,[switch]$Force)
        if ($LiteralPath -like 'HKCU:*') { $key=New-Object PSObject;$key | Add-Member ScriptMethod Flush {};$key | Add-Member ScriptMethod Dispose {};return $key }
        Microsoft.PowerShell.Management\Get-Item @PSBoundParameters
    }
    function New-ItemProperty { param($Path,$Name,$Value,$PropertyType,[switch]$Force) $global:testHooks[$Name]=$Value }
    function Get-ItemPropertyValue { param($Path,$Name) return $global:testHooks[$Name] }
    function Remove-ItemProperty { param($Path,$Name,$ErrorAction) $global:testHooks.Remove($Name) }
}
function Wait-Process { param($Id,$Timeout,$ErrorAction) }
function Get-Process {
    param($Id,$Name,$ErrorAction)
    if ($Name -and (Test-Path -LiteralPath (Join-Path $global:testRoot 'active'))) { return [PSCustomObject]@{Path=$global:testPlan.exe} }
}
function Start-Process {
    param($FilePath,$ArgumentList,[switch]$Wait,[switch]$PassThru)
    if ($ArgumentList -and $ArgumentList[0] -eq '--verify-dev-update') {
        @{verified=$true;sha256=$global:testPlan.sha256} | ConvertTo-Json | Set-Content -LiteralPath $global:testPlan.verify_report -Encoding UTF8
        return [PSCustomObject]@{ExitCode=0}
    }
    if ($FilePath -eq $global:testPlan.installer) {
        [IO.File]::WriteAllText($global:testPlan.exe,'partial-new-version')
        [IO.File]::WriteAllText((Join-Path $global:testPlan.install_dir 'new-only.dll'),'orphan')
        if (Test-Path -LiteralPath (Join-Path $global:testRoot 'complete')) { return [PSCustomObject]@{ExitCode=0} }
        [IO.File]::WriteAllText((Join-Path $global:testRoot 'crash-barrier'),'installer is modifying files')
        while ($true) { Start-Sleep -Milliseconds 200 }
    }
    if ($ArgumentList[0] -ne '--data-dir' -or $ArgumentList[1] -ne ('"'+$global:testPlan.data_dir+'"')) { throw 'Recovery lost custom data root' }
    [IO.File]::WriteAllText((Join-Path $global:testRoot 'restarted'),'restored app would launch')
}
& $Helper -PlanPath $Plan -Recover:$Recover
'@ | Set-Content -LiteralPath $wrapper -Encoding UTF8
        $args=@('-NoProfile','-NonInteractive','-File',('"'+$wrapper+'"'),'-Helper',('"'+$copied+'"'),'-Plan',('"'+$planPath+'"'),'-RegistryPath',('"'+$registry+'"'))
        if ($scenario -eq 'completed') { Set-Content -LiteralPath (Join-Path $case 'complete') -Value 'complete' }
        $child=Start-Process -FilePath $shell -ArgumentList $args -PassThru -RedirectStandardOutput (Join-Path $case 'normal.out') -RedirectStandardError (Join-Path $case 'normal.err')
        # Cache the native handle before exit; Windows PowerShell 5.1 otherwise loses ExitCode.
        $null=$child.Handle
        if ($scenario -eq 'completed') {
            Wait-Exit $child
            Assert ($child.ExitCode -eq 0) ('Completed helper failed: '+(Get-Content (Join-Path $case 'normal.err') -Raw))
        } else {
            $deadline=[DateTime]::UtcNow.AddSeconds(30)
            while (!(Test-Path -LiteralPath (Join-Path $case 'crash-barrier'))) {
                if ($child.HasExited) { throw ('Helper exited before crash barrier: '+(Get-Content (Join-Path $case 'normal.err') -Raw)+'; helper log: '+$(if(Test-Path -LiteralPath $plan.log){Get-Content -LiteralPath $plan.log -Raw}else{'not written'})) }
                if ([DateTime]::UtcNow -gt $deadline) { throw 'Crash barrier timed out' }
                Start-Sleep -Milliseconds 100
            }
            $child.Kill();Wait-Exit $child
        }
        $child=$null
        $journal=Join-Path $case 'recovery-state.json';$saved=[IO.File]::ReadAllBytes($journal)
        $state=Get-Content -LiteralPath $journal -Raw -Encoding UTF8 | ConvertFrom-Json
        Assert ($state.state -eq $(if($scenario -eq 'completed'){'completed'}else{'pending'})) 'Durable recovery state was not committed before mutation'
        if ($windows) {
            Assert ((Get-ItemPropertyValue -Path $registry -Name $sentinel) -eq 'preserve unrelated value') 'Registration overwrote unrelated RunOnce values'
            if ($scenario -ne 'completed') {
                $command=Get-ItemPropertyValue -Path $registry -Name $hook
                Assert ($command.Contains($copied) -and $command.EndsWith(' -Recover') -and !$command.Contains('ExecutionPolicy')) 'Invalid recovery RunOnce command'
            }
        }
        Remove-Item -LiteralPath (Join-Path $case 'restarted') -ErrorAction SilentlyContinue
        if ($scenario -eq 'missing-install') { Remove-Item -LiteralPath $install -Recurse -Force }
        if ($scenario -eq 'damaged-backup') { [IO.File]::WriteAllText((Join-Path $plan.backup 'AchievementAtlas.exe'),'corrupted') }
        if ($scenario -eq 'running-app') { Set-Content -LiteralPath (Join-Path $case 'active') -Value 'running' }
        if ($scenario -eq 'corrupt-state') { [IO.File]::WriteAllText($journal,'{invalid') }
        if ($scenario -eq 'path-mismatch') { $state.backup=Join-Path $case 'wrong backup';$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $journal -Encoding UTF8 }
        if ($scenario -eq 'missing-backup') { Move-Item -LiteralPath $plan.backup -Destination (Join-Path $case 'parked-backup') }
        $child=Start-Process -FilePath $shell -ArgumentList ($args+@('-Recover')) -PassThru -RedirectStandardOutput (Join-Path $case 'recover.out') -RedirectStandardError (Join-Path $case 'recover.err')
        # Cache the native handle before exit; Windows PowerShell 5.1 otherwise loses ExitCode.
        $null=$child.Handle
        Wait-Exit $child
        $refused=$scenario -in @('damaged-backup','running-app','corrupt-state','path-mismatch','missing-backup')
        Assert (($child.ExitCode -ne 0) -eq $refused) ('Unexpected recovery result: '+$scenario+' ExitCode='+$child.ExitCode+' stderr='+(Get-Content (Join-Path $case 'recover.err') -Raw)+' log='+(Get-Content -LiteralPath $plan.log -Raw))
        $child=$null
        if ($refused -or $scenario -eq 'completed') {
            Assert (!(Test-Path -LiteralPath (Join-Path $case 'restarted'))) 'Unsafe or duplicate restart'
            Assert ([IO.File]::ReadAllText($plan.exe) -eq 'partial-new-version') 'Refused/committed recovery mutated installation'
            if ($refused) {
                if ($scenario -eq 'missing-backup') { Move-Item -LiteralPath (Join-Path $case 'parked-backup') -Destination $plan.backup }
                [IO.File]::WriteAllBytes($journal,$saved)
                [IO.File]::WriteAllText((Join-Path $plan.backup 'AchievementAtlas.exe'),'old-executable')
                Remove-Item -LiteralPath (Join-Path $case 'active') -ErrorAction SilentlyContinue
                $child=Start-Process -FilePath $shell -ArgumentList ($args+@('-Recover')) -PassThru -RedirectStandardOutput (Join-Path $case 'retry.out') -RedirectStandardError (Join-Path $case 'retry.err')
                # Cache the native handle before exit; Windows PowerShell 5.1 otherwise loses ExitCode.
                $null=$child.Handle
                Wait-Exit $child;Assert ($child.ExitCode -eq 0) 'Recovery retry failed';$child=$null
            }
        }
        if ($scenario -ne 'completed') {
            Assert ([IO.File]::ReadAllText($plan.exe) -eq 'old-executable') 'Recovery did not restore old executable'
            Assert (!(Test-Path -LiteralPath (Join-Path $install 'new-only.dll'))) 'Recovery left new files behind'
            Assert ((Get-Content -LiteralPath $journal -Raw -Encoding UTF8 | ConvertFrom-Json).state -eq 'rolled_back') 'Recovery did not persist rollback completion'
        }
        # A second independent process must treat the terminal state as a no-op.
        Remove-Item -LiteralPath (Join-Path $case 'restarted') -ErrorAction SilentlyContinue
        $repeat=$args+@('-Recover')
        $child=Start-Process -FilePath $shell -ArgumentList $repeat -PassThru -RedirectStandardOutput (Join-Path $case 'again.out') -RedirectStandardError (Join-Path $case 'again.err')
        # Cache the native handle before exit; Windows PowerShell 5.1 otherwise loses ExitCode.
        $null=$child.Handle
        Wait-Exit $child;Assert ($child.ExitCode -eq 0) 'Repeated recovery failed';$child=$null
        Assert (!(Test-Path -LiteralPath (Join-Path $case 'restarted'))) 'Repeated recovery relaunched application'
        if ($windows) { Assert ($null -eq (Get-ItemProperty -Path $registry -ErrorAction Stop).$hook) 'Recovery hook was not cleaned up' }
        $passed++
    }
    Write-Output "Crash recovery: $passed fresh-process scenarios passed"
} finally {
    if ($child -and !$child.HasExited) { $child.Kill();$child.WaitForExit(10000) | Out-Null }
    if ($windows) {
        Remove-Item -LiteralPath $registryRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $root -Recurse -Force
}
