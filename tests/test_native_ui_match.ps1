$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Resolve-Path "$PSScriptRoot/test_windows_self_update.ps1"),[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'Native self-update test parser failed' }
$definition=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-NativeControlLabel'},$true)
if (!$definition) { throw 'Native label helper missing' }
. ([ScriptBlock]::Create($definition.Extent.Text))
foreach ($case in @(
    @{name='Download';enabled=$true;expected=$true},
    @{name='download';enabled=$true;expected=$true},
    @{name='';enabled=$true;expected=$false},
    @{name=$null;enabled=$true;expected=$false},
    @{name='Other';enabled=$true;expected=$false},
    @{name='Download';enabled=$false;expected=$false}
)) {
    $control=[PSCustomObject]@{Name=$case.name;IsEnabled=$case.enabled}
    if ((Test-NativeControlLabel $control 'Download') -ne $case.expected) { throw 'Native label match regression' }
}
$script:labelReads=0
$changing=New-Object PSObject -Property @{IsEnabled=$true}
$changing | Add-Member ScriptProperty Name { $script:labelReads+=1;if ($script:labelReads -eq 1) { return 'Download' };return $null }
if (!(Test-NativeControlLabel $changing 'Download') -or $script:labelReads -ne 1) { throw 'Live UIA name must be read exactly once' }
Write-Output 'Native UI labels: null/empty/disabled/case/mismatch and changing-property snapshot passed'
