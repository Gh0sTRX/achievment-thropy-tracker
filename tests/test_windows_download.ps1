$ErrorActionPreference='Stop'
. "$PSScriptRoot/windows_download.ps1"
$root=Join-Path ([IO.Path]::GetTempPath()) ('atlas-network-'+[Guid]::NewGuid())
New-Item -ItemType Directory -Path $root | Out-Null
$bytes=[Text.Encoding]::UTF8.GetBytes('test-only installer bytes')
$algorithm=[Security.Cryptography.SHA256]::Create()
$expected=([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-','').ToLower();$algorithm.Dispose()
function Invoke-WebRequest {
    param($Uri,$OutFile,$TimeoutSec,[switch]$UseBasicParsing)
    $global:downloadAttempts++
    $code=$global:downloadResponses.Dequeue()
    if ($code -ge 400) {
        $failure=[Exception]::new('Test transport failure')
        $failure | Add-Member NoteProperty Response ([PSCustomObject]@{StatusCode=$code})
        throw $failure
    }
    [IO.File]::WriteAllBytes($OutFile,$bytes)
}
function Start-Sleep { param($Seconds) $global:downloadWaits+=$Seconds }
function Assert($Condition,$Message) { if (!$Condition) { throw $Message } }
try {
    foreach ($case in @(
        @{codes=@(504,502,200);attempts=3;valid=$true;hash=$expected},
        @{codes=@(200);attempts=1;valid=$false;hash=('0'*64)},
        @{codes=@(404,200);attempts=1;valid=$false;hash=$expected},
        @{codes=@(504,504,504,200);attempts=3;valid=$false;hash=$expected}
    )) {
        $global:downloadResponses=[Collections.Generic.Queue[int]]::new();foreach($code in $case.codes){$global:downloadResponses.Enqueue($code)}
        $global:downloadAttempts=0;$global:downloadWaits=0
        $path=Join-Path $root 'setup.exe';$ok=$true
        try { Get-VerifiedTestInstaller 'https://github.com/test-only/setup.exe' $path $case.hash } catch { $ok=$false }
        Assert ($ok -eq $case.valid) 'Incorrect verified-download outcome'
        Assert ($global:downloadAttempts -eq $case.attempts) 'Retry count exceeded or wrong failures retried'
        if (!$ok) { Assert (!(Test-Path -LiteralPath $path)) 'Unsafe partial/hash-mismatched download retained' }
        Remove-Item -LiteralPath $path -ErrorAction SilentlyContinue
    }
    'Verified downloads: transient retry, checksum rejection, permanent failure and retry exhaustion passed'
} finally {
    Remove-Item -LiteralPath $root -Recurse -Force
    Remove-Variable downloadResponses,downloadAttempts,downloadWaits -Scope Global -ErrorAction SilentlyContinue
}
