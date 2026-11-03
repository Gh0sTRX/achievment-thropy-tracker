param([Parameter(Mandatory=$true)][string]$PlanPath)
$ErrorActionPreference='Stop'
$plan=Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
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
    New-Item -ItemType Directory -Path $plan.backup -Force | Out-Null
    Copy-Item -Path (Join-Path $plan.install_dir '*') -Destination $plan.backup -Recurse -Force
    $args=@('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/DIR="'+$plan.install_dir+'"'),('/LOG="'+$plan.log+'"'))
    $process=Start-Process -FilePath $plan.installer -ArgumentList $args -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        Copy-Item -Path (Join-Path $plan.backup '*') -Destination $plan.install_dir -Recurse -Force
        throw ('Installer failed: '+$process.ExitCode+'; previous application files restored')
    }
    Start-Process -FilePath $plan.exe
    'Update installed: '+$plan.version | Add-Content -LiteralPath $plan.log
} catch {
    ('Update cancelled or failed: '+$_.Exception.Message) | Add-Content -LiteralPath $plan.log
    if (!(Get-Process -Id $plan.parent_pid -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath $plan.exe)) {
        Start-Process -FilePath $plan.exe
    }
}
