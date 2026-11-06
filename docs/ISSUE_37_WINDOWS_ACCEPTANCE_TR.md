# Gerçek Windows kabulü — yalnız arşiv kopyası

6 Kasım 2026. Kullanıcı kendi Windows cihazında deneme yapabileceğini bildirdi. Bu protokol gerçek sonuç değil, rıza verilmiş deneme hazırlığıdır. İlk tur mevcut arşivi koruyan offline kullanım; ikinci tur kullanıcının kendi Xbox erişimidir.

## Doğru uygulama

PR #39'un başarılı Windows Actions koşusundan portable uygulamayı ayrı klasöre çıkar. Kaynak `da489e465b428f554341ff055c544338210a6d8e`; Windows koşusu [42136068296](https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/42136068296) başarılı. [Artifact 13465297813](https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/42136068296/artifacts/13465297813) içindeki `AchievementAtlas-0.16.1-Windows-x64-Portable.zip` dosyasını da ayrı klasöre aç; test EXE'si bunun içindedir. Paket boyutu/hash metadata'sı durum raporundadır. Sürüm etiketi hâlâ 0.16.1 olabilir; yayımlı eski binary ile PR build'ini karıştırma. Bu bir Development Release değildir ve yayıncı imzası varmış gibi sunulmaz.

Kaynak CI başarılı olmadan test binary'si hazır kabul edilmez. Mevcut Atlas'ı kapat; aynı kullanıcı mutex'i ikinci pencereyi engeller. Denemede orijinal veri klasörü seçilmez, güncelleyiciden başka kurulum başlatılmaz.

## Güvenli yerel kopya hazırlığı

Aşağıdaki PowerShell bloğu yalnız yerel test hazırlığıdır; internetten komut/binary indirmez. `settings.json`, SDK oturum dosyaları ve updater dosyalarını kopyalamaz. `library.json` ve görseller byte olarak kopyalanır. Yalnız kopyanın state dosyasında otomatik bağlı-Xbox başlangıcı ve canlı doğrulama durumu sıfırlanır; pinler/profil referansları korunur. Kopya state biçimi yeniden yazılır; asıl dosyalar değiştirilmez.

Özel bir `--data-dir` kullanıyorsan `$atlasSource` yolunu kendi gerçek veri klasörünle değiştir. Varsayılan yol aşağıdadır. Uygulama kapalı olmalıdır.

```powershell
$ErrorActionPreference = 'Stop'
if (Get-Process -Name AchievementAtlas -ErrorAction SilentlyContinue) {
    throw 'Önce açık Atlas penceresini kapat.'
}
$atlasSource = Join-Path $env:LOCALAPPDATA 'AchievementAtlas'
if (!(Test-Path -LiteralPath (Join-Path $atlasSource 'library.json'))) {
    throw 'Arşiv bulunamadı; kendi veri klasörünün yolunu doğrula.'
}
$atlasTestRoot = Join-Path $env:LOCALAPPDATA ('AchievementAtlas-QA\' + [Guid]::NewGuid())
$atlasTestData = Join-Path $atlasTestRoot 'data'
New-Item -ItemType Directory -Path $atlasTestData | Out-Null
$atlasOriginalHashes = @{}
foreach ($atlasName in @('library.json', 'state.json')) {
    $atlasFile = Join-Path $atlasSource $atlasName
    if (Test-Path -LiteralPath $atlasFile) {
        if ((Get-Item -LiteralPath $atlasFile).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw 'Veri dosyası bağlantı. Kopyayı elle doğrulayarak hazırla.'
        }
        $atlasOriginalHashes[$atlasName] = (Get-FileHash -LiteralPath $atlasFile -Algorithm SHA256).Hash
        Copy-Item -LiteralPath $atlasFile -Destination $atlasTestData
    }
}
$atlasArt = Join-Path $atlasSource 'artwork'
if (Test-Path -LiteralPath $atlasArt) {
    $atlasArtEntries = @((Get-Item -LiteralPath $atlasArt)) + @(Get-ChildItem -LiteralPath $atlasArt -Recurse -Force)
    if ($atlasArtEntries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) {
        throw 'Görsel klasörü bağlantı/junction. Kopyayı elle doğrulayarak hazırla.'
    }
    Copy-Item -LiteralPath $atlasArt -Destination $atlasTestData -Recurse
}
$atlasStatePath = Join-Path $atlasTestData 'state.json'
if (Test-Path -LiteralPath $atlasStatePath) {
    $atlasState = Get-Content -LiteralPath $atlasStatePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $atlasState | Add-Member -NotePropertyName linked_profile -NotePropertyValue $null -Force
    $atlasState | Add-Member -NotePropertyName provider_access -NotePropertyValue @{} -Force
    [IO.File]::WriteAllText($atlasStatePath, ($atlasState | ConvertTo-Json -Depth 100), (New-Object Text.UTF8Encoding($false)))
}
foreach ($atlasName in $atlasOriginalHashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $atlasSource $atlasName) -Algorithm SHA256).Hash -ne $atlasOriginalHashes[$atlasName]) {
        throw 'Asıl veri dosyası değişti; denemeyi başlatma.'
    }
}
Write-Host "Test veri klasörü: $atlasTestData"
```

Portable `AchievementAtlas.exe` için Windows'ta kısayol oluştur. Kısayol hedefinin sonuna `--data-dir "YUKARIDAKI-TEST-VERI-KLASORU"` ekle. Python gerekmez. Doğrudan normal masaüstü kısayolunu kullanma; orijinal klasörü açar. Çalıştırılacak EXE'nin CI'dan çıkan test kopyası olduğuna bak. Yol, hash veya dosyaları public issue'ya yapıştırma.

Hazırlık bloğu PowerShell 7 ile yalnız sentetik geçici dosyalarda çalıştırıldı: kaynak hash'leri aynı, pin ve görsel dosyası korundu, settings dosyası kopyalanmadı, otomatik resume/verified durumu yalnız kopyada sıfırlandı. Gerçek Windows PowerShell/kişisel arşiv kabulü henüz yapılmadı.

## Tur A — internet kapalı, bağlantı kurulmadan

- Ağ bağlantısını kapat ve test kısayoluyla aç.
- Oyun/kazanım sayıları, bir not ve sabit hedef mevcut mu?
- Cold War / Asphalt 9 veya kendi bilinen oyunun: doğru cihaz/edisyon, varsa yerel ikon/açıklama/tarih ve kapak görünür mü? Eksik veri için dürüst açıklama var mı?
- Oyun ara → kalan başarımlar → ayrıntı → pin → geri: kart odağı ve scroll korunuyor mu? Klavye ve varsa fiziksel gamepad ile tekrarla.
- Bir test notu/pin ekle; kapat/aç; kopyada duruyor mu?
- Test kopyasından JSON yedek indir; kopyadaki notu/pini değiştir; aynı yedeği geri yükle. Hash hatası var mı, not/pin geri geldi mi?
- Mevcut görseller aynı klasörde kaldı mı? JSON dosyasını başka yere taşımak görsel dosyalarını taşımaz.

## Tur B — kullanıcıya ait yetkili Xbox

- Ağı aç; test kopyasında Hesap & Veri → Xbox adını ve hedefi kontrol et.
- Kendi oturumunla uygulama içi erişim/test/eşitleme adımlarını kullan. SDK, cihazındaki yetkili oturumunu yenileyebilir; oturum dosyası paylaşılmaz. Kopyadaki arşiv ile farklı kullanıcıyı eşleştirme.
- Xbox 360 ve modern oyunları ayır; bir bilinen kazanım/tarih/ikon, not/pin ve cihaz/edisyonu kontrol et. Kaynağı belirsiz eşleşmeyi onaylama.
- Hata olursa yalnız hata sınıfını ve etkilenen oyun sayısını raporla. Şifre, token, NPSSO, key, XUID veya tam arşiv dosyası gönderme.
- Tekrar offline aç; önceki kazanımlar/not/pin/görseller kopyada durmalı.

Steam ve PSN gerçek kabulü ayrıca yapılır; bu Xbox turundan başarılı kabul edilmez. Başlatılan isteğin tamamlanması beklenerek durdurma denenir; gerçek rate-limit oluşturmak için tekrarlı istek gönderilmez.

## Kısa sonuç biçimi

Build run ID; offline açılış (geçti/kaldı); geri/focus/scroll (geçti/kaldı); not/pin/restore (geçti/kaldı); yerel ikon/tarih/edisyon (var/yok/hatalı); gerçek Xbox sync (geçti veya hata sınıfı); orijinal dosya hash'leri değişmedi (evet/hayır). Özel içerik ve credential ekleme. Testten sonra orijinal dosyaları yeniden hash ile kontrol et.
