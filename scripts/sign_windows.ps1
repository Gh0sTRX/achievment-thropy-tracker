param([Parameter(Mandatory=$true)][string]$TargetPath,[Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference = 'Stop'
if (!$env:ATLAS_SIGNING_PFX) {
    @{ signed=$false; reason='No trusted code-signing certificate configured'; file=[IO.Path]::GetFileName($TargetPath) } | ConvertTo-Json | Set-Content $Report -Encoding utf8
    Write-Host 'Unsigned development build. No trusted publisher identity is claimed.'
    exit 0
}
if (!$env:ATLAS_SIGNING_PASSWORD) { throw 'Signing password is not configured' }
$tool = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe' | Sort-Object FullName -Descending | Select-Object -First 1
if (!$tool) { throw 'Windows SDK SignTool missing' }
$pfx = Join-Path $env:RUNNER_TEMP ('atlas-signing-' + [guid]::NewGuid().ToString() + '.pfx')
$cert = $null
try {
    [IO.File]::WriteAllBytes($pfx, [Convert]::FromBase64String($env:ATLAS_SIGNING_PFX))
    $password = ConvertTo-SecureString $env:ATLAS_SIGNING_PASSWORD -AsPlainText -Force
    $cert = Import-PfxCertificate -FilePath $pfx -Password $password -CertStoreLocation Cert:\CurrentUser\My | Where-Object HasPrivateKey | Select-Object -First 1
    if (!$cert) { throw 'Code-signing private key missing' }
    $eku = @($cert.EnhancedKeyUsageList | ForEach-Object { $_.ObjectId.Value })
    if ('1.3.6.1.5.5.7.3.3' -notin $eku) { throw 'Certificate is not valid for code signing' }
    $chain = New-Object Security.Cryptography.X509Certificates.X509Chain
    if (!$chain.Build($cert)) { throw 'Certificate does not chain to a trusted Windows authority' }
    & $tool.FullName sign /sha1 $cert.Thumbprint /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $TargetPath
    if ($LASTEXITCODE -ne 0) { throw 'Authenticode signing failed' }
    & $tool.FullName verify /pa /all $TargetPath
    if ($LASTEXITCODE -ne 0) { throw 'Authenticode verification failed' }
    $signature=Get-AuthenticodeSignature $TargetPath
    if ($signature.Status -ne 'Valid') { throw 'Signature is not valid' }
    @{ signed=$true; status='Valid'; file=[IO.Path]::GetFileName($TargetPath); timestamped=[bool]$signature.TimeStamperCertificate } | ConvertTo-Json | Set-Content $Report -Encoding utf8
} finally {
    Remove-Item $pfx -Force -ErrorAction SilentlyContinue
    if ($cert) { Remove-Item $cert.PSPath -DeleteKey -Force -ErrorAction SilentlyContinue }
}
