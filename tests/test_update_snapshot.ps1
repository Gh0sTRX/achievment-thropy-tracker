$ErrorActionPreference='Stop'
$helper=Join-Path $PSScriptRoot '../scripts/apply_update.ps1'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Resolve-Path $helper),[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
# Load actual production functions without running the updater entry point.
foreach ($name in @('Get-InstallInventory','Assert-SnapshotMatches','Save-InstallSnapshot','Restore-InstallSnapshot')) {
    $definition=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name},$true)
    . ([ScriptBlock]::Create($definition.Extent.Text))
}
$root=Join-Path ([IO.Path]::GetTempPath()) ('atlas-rollback-'+[Guid]::NewGuid())
New-Item -ItemType Directory -Path $root | Out-Null
$passed=0
function Assert($Condition,[string]$Message) { if (!$Condition) { throw $Message } }
function Expect-Failure([ScriptBlock]$Action) {
    $failed=$false
    try { & $Action } catch { $failed=$true }
    Assert $failed 'Expected operation to fail'
}
function Fixture([string]$Name) {
    $directory=Join-Path $root $Name
    New-Item -ItemType Directory -Path (Join-Path $directory 'install/nested') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $directory 'install/empty') | Out-Null
    Set-Content -LiteralPath (Join-Path $directory 'install/old.exe') -Value 'original'
    Set-Content -LiteralPath (Join-Path $directory 'install/nested/.hidden') -Value 'hidden-original'
    return $directory
}
try {
    $case=Fixture 'exact [paths]'
    $install=Join-Path $case 'install'; $backup=Join-Path $case 'backup'
    $inventory=Save-InstallSnapshot $install $backup
    Set-Content -LiteralPath (Join-Path $install 'old.exe') -Value 'changed'
    Remove-Item -LiteralPath (Join-Path $install 'nested') -Recurse -Force
    Set-Content -LiteralPath (Join-Path $install 'nested') -Value 'type-replaced'
    New-Item -ItemType Directory -Path (Join-Path $install 'new/deep') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $install 'new/deep/orphan.dll') -Value 'new-only'
    Restore-InstallSnapshot $install $backup $inventory
    Assert-SnapshotMatches $install $inventory
    Assert (!(Test-Path -LiteralPath (Join-Path $install 'new'))) 'New-version files survived rollback'
    $passed++

    $case=Fixture 'damaged-backup';$install=Join-Path $case 'install';$backup=Join-Path $case 'backup'
    $inventory=Save-InstallSnapshot $install $backup
    Set-Content -LiteralPath (Join-Path $backup 'old.exe') -Value 'corrupt'
    Set-Content -LiteralPath (Join-Path $install 'keep.txt') -Value 'do-not-delete'
    Expect-Failure { Restore-InstallSnapshot $install $backup $inventory }
    Assert (Test-Path -LiteralPath (Join-Path $install 'keep.txt')) 'Failed backup verification mutated installation'
    $passed++

    $case=Fixture 'unsafe-backup';$install=Join-Path $case 'install'
    Expect-Failure { Save-InstallSnapshot $install (Join-Path $install 'backup') }
    $backup=Join-Path $case 'backup';Save-InstallSnapshot $install $backup | Out-Null
    Expect-Failure { Save-InstallSnapshot $install $backup }
    $passed++

    $case=Fixture 'linked-install';$install=Join-Path $case 'install'
    $outside=Join-Path $case 'outside';New-Item -ItemType Directory -Path $outside | Out-Null
    $link=Join-Path $install 'linked'
    $kind=if ([Environment]::OSVersion.Platform -eq 'Win32NT') {'Junction'} else {'SymbolicLink'}
    New-Item -ItemType $kind -Path $link -Target $outside | Out-Null
    Expect-Failure { Save-InstallSnapshot $install (Join-Path $case 'backup') }
    Assert (!(Test-Path -LiteralPath (Join-Path $case 'backup'))) 'Linked installation created a backup'
    Remove-Item -LiteralPath $link -Force
    $passed++

    # Execute the real helper, replacing OS/process boundaries only.
    foreach ($scenario in @('exit-failure','launch-exception','deleted-install','corrupt-recovery','success')) {
        $case=Fixture $scenario;$script:install=Join-Path $case 'install';$backup=Join-Path $case 'previous-version'
        Move-Item -LiteralPath (Join-Path $install 'old.exe') -Destination (Join-Path $install 'AchievementAtlas.exe')
        Set-Content -LiteralPath (Join-Path $install 'unins000.exe') -Value 'uninstaller'
        $original=@(Get-InstallInventory $install)
        $script:plan=@{install_dir=$install;backup=$backup;exe=(Join-Path $install 'AchievementAtlas.exe');installer=(Join-Path $case 'setup.exe');ready=(Join-Path $case 'ready');log=(Join-Path $case 'update.log');verify_report=(Join-Path $case 'verify.json');manifest='manifest';bundle='bundle';mode='development';data_dir=(Join-Path $case 'custom data');parent_pid=99999999;version='test'}
        Set-Content -LiteralPath $plan.installer -Value 'fake-installer'
        $plan.sha256=(Get-FileHash -LiteralPath $plan.installer -Algorithm SHA256).Hash.ToLower()
        $planPath=Join-Path $case 'plan.json';$plan | ConvertTo-Json | Set-Content -LiteralPath $planPath -Encoding UTF8
        $global:AtlasRecoveryTest=@{plan=$plan;install=$install;restarts=0;scenario=$scenario;hooks=@{}}
        $copiedHelper=Join-Path $case 'apply-update.ps1';Copy-Item -LiteralPath $helper -Destination $copiedHelper
        function New-Item { param($Path,$ItemType,[switch]$Force) if ($Path -like 'HKCU:*') { return };Microsoft.PowerShell.Management\New-Item @PSBoundParameters }
        function New-ItemProperty { param($Path,$Name,$Value,$PropertyType,[switch]$Force) $global:AtlasRecoveryTest.hooks[$Name]=$Value }
        function Get-ItemPropertyValue { param($Path,$Name) return $global:AtlasRecoveryTest.hooks[$Name] }
        function Remove-ItemProperty { param($Path,$Name,$ErrorAction) $global:AtlasRecoveryTest.hooks.Remove($Name) }
        function Wait-Process { param($Id,$Timeout,$ErrorAction) }
        function Get-Process { param($Id,$ErrorAction) }
        function Start-Process {
            param($FilePath,$ArgumentList,[switch]$Wait,[switch]$PassThru)
            if ($ArgumentList -and $ArgumentList[0] -eq '--verify-dev-update') {
                @{verified=$true;sha256=$global:AtlasRecoveryTest.plan.sha256} | ConvertTo-Json | Set-Content -LiteralPath $global:AtlasRecoveryTest.plan.verify_report
                return [PSCustomObject]@{ExitCode=0}
            }
            if ($FilePath -eq $global:AtlasRecoveryTest.plan.installer) {
                Set-Content -LiteralPath (Join-Path $global:AtlasRecoveryTest.install 'AchievementAtlas.exe') -Value 'new-version'
                Set-Content -LiteralPath (Join-Path $global:AtlasRecoveryTest.install 'orphan.dll') -Value 'new-only'
                if ($global:AtlasRecoveryTest.scenario -eq 'deleted-install') { Remove-Item -LiteralPath $global:AtlasRecoveryTest.install -Recurse -Force }
                if ($global:AtlasRecoveryTest.scenario -eq 'launch-exception') { throw 'Simulated installer launch failure' }
                if ($global:AtlasRecoveryTest.scenario -eq 'corrupt-recovery') { Set-Content -LiteralPath (Join-Path $global:AtlasRecoveryTest.plan.backup 'AchievementAtlas.exe') -Value 'corrupt' }
                return [PSCustomObject]@{ExitCode=$(if ($global:AtlasRecoveryTest.scenario -eq 'success') {0} else {5})}
            }
            if ($ArgumentList.Count -ne 2 -or $ArgumentList[0] -ne '--data-dir' -or $ArgumentList[1] -ne ('"'+$global:AtlasRecoveryTest.plan.data_dir+'"')) { throw 'Restart lost custom data directory' }
            $global:AtlasRecoveryTest.restarts++
        }
        & $copiedHelper -PlanPath $planPath
        if ($scenario -eq 'corrupt-recovery') {
            Assert ($global:AtlasRecoveryTest.restarts -eq 0) 'Restarted mixed application after rollback failed'
            Assert ((Get-Content -LiteralPath $plan.log -Raw).Contains('ROLLBACK FAILED')) 'Missing recovery diagnostics'
        } elseif ($scenario -eq 'success') {
            Assert ($global:AtlasRecoveryTest.restarts -eq 1) 'Successful update did not restart'
            Assert ((Get-Content -LiteralPath $plan.exe -Raw).Trim() -eq 'new-version') 'Successful update was rolled back'
        } else {
            Assert-SnapshotMatches $install $original
            Assert ($global:AtlasRecoveryTest.restarts -eq 1) 'Verified old application did not restart'
        }
        $passed++
    }
    Write-Output "Updater snapshot: $passed scenarios passed"
} finally {
    Remove-Variable AtlasRecoveryTest -Scope Global -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $root -Recurse -Force
}
