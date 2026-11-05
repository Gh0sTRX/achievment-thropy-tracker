# Achievement Atlas 0.16.0 — Game Universe ve Steam

Windows geliştirme sürümü. 0.15.1'den sonra gelen PR #11–#17 değişikliklerini içerir. Bu sürüm gerçek hesap kabul testlerinden geçmiş kararlı sürüm iddiası taşımaz.

## Yenilikler

- Tek native arayüz içinde bağımsız Game Universe rotası, yedi sekme, inline kupa ayrıntıları ve geri dönüşte kaydırma/odak koruması.
- Sade ana menü, Xbox/PSN/Steam/CSV başlangıç seçenekleri ve Ctrl+K / slash araması.
- PSN oyun bazlı kısmi hata koruması ve kupa grup metadata'sı; cihaz/edisyon ayrımı korunur.
- Resmî Steam Web API sağlayıcısı: AppID/API-name kimlikleri, gerçek locked/earned sorguları, güvenli yerel API ayarı. Puanlar Gamerscore veya PSN kupasına çevrilmez.
- Steam public metadata'sı altı saat cache'lenir; oyuncu ilerlemesi her eşitlemede yeniden sorgulanır. En fazla üç oyun işlenir; durdurma/auth/429 sonraki grubu engeller.
- Beş gerçek artwork türü, kullanıcı dosyası önceliği, açık edisyon onaylı SteamGridDB eşleşmesi ve Artwork Health.
- Native gamepad gezinmesi, erişilebilir sekmeler, reduced motion, ortak render/navigation olayları ve büyük kütüphane önbellekleri.
- CI RunOnce fixture izolasyonu, eski installer indirmelerinde sınırlı transport tekrarları; hash veya imza kontrolleri kaldırılmadı.

## Ölçülenler

175 Python testi ve önceki kaynak commit'inin Windows/native/upgrade kontrolleri geçti. 0.16.0 paketi için ayrı Windows workflow'u yayın öncesinde tamamlanmalıdır; bu dosya build kanıtı değildir.

Sentetik testte 100 oyunun cache sıcak sorgusu 201→101 API çağrısı yaptı. Üç işçili 30 oyun testinin medyanı 312,44→106,44 ms oldu. Bunlar gerçek hesabın indirme hızı değildir. Ayrıntı: STEAM_SCHEMA_CACHE_TR.md, STEAM_BOUNDED_SYNC_TR.md ve ISSUE_10_DELIVERY_AUDIT_TR.md.

## Kalan önemli eksikler

1. Gerçek Xbox/PSN/Steam hesabıyla uçtan uca kabul testi; mevcut kanıt SDK/mock testleridir.
2. 40 bin başarımlı /api/data yanıtı yaklaşık 16 MB; kısmi veri yükleme henüz yok.
3. Her oyun/edisyon için gerçek artwork kapsaması ölçülmedi; eksik CDN dosyaları olabilir.
4. Windows Authenticode sertifikası/SignPath onayı yok; indirme ve SmartScreen itibar uyarıları sürebilir.
5. Fiziksel gamepad, ekran okuyucu ve OS metin girişi için manuel Windows kabul matrisi eksik.
6. Fiziksel güç kesintisi ve gerçek Windows logon kurtarma testi eksik; süreç kesintisi/registry testleri vardır.
7. Steam DLC grupları ve diğer PC sağlayıcıları (GOG/Epic) henüz uygulanmadı.
8. Birden fazla PC sağlayıcı hesabının profil seçimi/geçmiş arayüzü tamamlanmadı.
9. Türkçe rehberlerin kaynak doğruluğu manuel kabul gerektirir; ücretli otomatik üretim varsayılan kapalıdır.
10. Üretici logo dağıtım izni doğrulanmadı; bağımsız Atlas logosu ve platform metin kimlikleri kullanılır.

Xbox/PSN sorgusu hâlâ geçerli servis erişimi gerektirir; yalnız kullanıcı adı yazılması sağlayıcı yetkilendirmesini ortadan kaldırmaz. Steam API anahtarı da cihazda ayarlanmalıdır. Gerçek parola/oturum/API anahtarını issue veya sohbette paylaşma.

Geliştirme kanalı SHA256 + GitHub/Sigstore köken doğrulaması kullanır. Bu, Windows yayıncı imzası değildir. 0.15.1 kullanıcıları uygulamadaki Diğer ekranlar → Güncellemeler yolunu kullanabilir. Eski arşivler korunur; olağan yedekleme önerilir. Main dalı değiştirilmez.


## Yayın sonrası kanıt — 5 Kasım 2026

- [Trusted Windows build ve yayın](https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/42089196768) başarılı.
- [175 test, JS, PowerShell ve native browser](https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/42089196427) başarılı.
- [Stok 0.15.1→0.16.0 native güncelleme](https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/42089180677) yayın sonrası yeniden çalıştırıldı ve başarılı oldu; job 127466984546, [rapor artifact](https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/42089180677/artifacts/13443839045).
- Kaynak `165145886d67f236021b1b551b345341eb0d7563`; installer 33.316.608 byte; SHA256 `498c7ead5cdc6e0692b9232c5b1a8a2056111b482bd91ad391bb44d79294563b`.
- Windows yayıncı imzası yok; manifest `authenticode_signed: false`. Fiziksel ve gerçek hesap eksikleri yukarıda kalır.
