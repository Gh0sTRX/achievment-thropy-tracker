param([Parameter(Mandatory=$true)][string]$TargetPath,[Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
$scanner=Join-Path $env:ProgramFiles 'Windows Defender\MpCmdRun.exe'
if (!(Test-Path $scanner)) {
    @{ scanned=$false; status='Scanner unavailable on build runner' } | ConvertTo-Json | Set-Content $Report -Encoding utf8
    exit 0
}
& $scanner -Scan -ScanType 3 -File $TargetPath -DisableRemediation *> defender-scan.log
$code=$LASTEXITCODE
if ($code -eq 0) {
    @{ scanned=$true; status='No threat reported by this scan'; exit_code=$code; file=[IO.Path]::GetFileName($TargetPath) } | ConvertTo-Json | Set-Content $Report -Encoding utf8
} elseif ($code -eq 2) {
    @{ scanned=$true; status='Threat or action required'; exit_code=$code } | ConvertTo-Json | Set-Content $Report -Encoding utf8
    throw 'Windows Defender reported a threat/action requirement; packaging stopped'
} else {
    @{ scanned=$false; status='Scan unavailable or unsuccessful; not a clean result'; exit_code=$code } | ConvertTo-Json | Set-Content $Report -Encoding utf8
}
