# Test-only bounded transport retries. Never retry or accept a checksum mismatch.
function Get-VerifiedTestInstaller([string]$Url,[string]$Destination,[string]$Sha256) {
    for ($attempt=0;$attempt -lt 3;$attempt++) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Destination -TimeoutSec 60
            break
        } catch {
            Remove-Item -LiteralPath $Destination -ErrorAction SilentlyContinue
            $response=$_.Exception.Response
            $code=if ($response) {[int]$response.StatusCode} else {0}
            if ($attempt -eq 2 -or ($code -gt 0 -and $code -lt 500 -and $code -notin @(408,429))) { throw }
            Start-Sleep -Seconds (2*($attempt+1))
        }
    }
    if ((Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLower() -ne $Sha256) {
        Remove-Item -LiteralPath $Destination -Force
        throw 'Published installer checksum mismatch; execution blocked'
    }
}
