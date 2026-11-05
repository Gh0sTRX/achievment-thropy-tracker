# Issue 10 — Kimlik, ilk kurulum ve arama

## Marka kararı

5 Kasım 2026 tarihinde Microsoft Trademark and Brand Guidelines, Steam Branding Guidelines ve Sony Interactive Entertainment Copyright and Trademark Notice incelendi. Microsoft birçok logo/ikon kullanımında izin gerektiğini belirtir. Sony bildirimi marka sahipliğini gösterir, bu uygulamaya logo dağıtım lisansı vermez. Steam sayfasının bulunması da bu projenin özel lisans onayı sayılmadı. Projeye verilmiş açık bir üretici logo lisansı saptanmadı. Bu nedenle bağımsız Atlas işareti korundu; Xbox yeşil, PlayStation mavi ve PC/Steam metin kimliği kullanıldı. Logo çizilerek taklit edilmedi, resmî onay/ortaklık iddia edilmedi.

Kaynaklar:
- https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks
- https://partner.steamgames.com/doc/marketing/branding
- https://sonyinteractive.com/en/copyright-and-trademark-notice/

## UX

Ana menü Atlas Hub, Kütüphane, Başarım Kasası, Hedefler, Profil. Müze diğer ekranlarda. İlk kurulum Xbox/PSN/Steam/CSV seçeneklerini gösterir. Servis ayarı kayıtlı olması doğrulanmış erişimden ayrılır. Steam ID/URL ve güvenli anahtar alanı mevcut hesap akışına bağlanır. Hesap ekranında platformun son başarılı eşitlemesi gösterilir; yedek/import mevcut yerel korumalı akışta kalır.

Ctrl+K ve `/` aynı native arama dialogunu açar. Oyunlar, başarımlar, platform, cihaz, edisyon, DLC ve “sabitlenen” sorguları desteklenir. Oklar/Enter/Escape ile kullanım; kapanışta odak iadesi vardır. Sonuçtan oyun kendi kalıcı rotasına, başarım aynı rotanın inline detayına açılır. 40 sonuç DOM sınırı, veri dizisi/spoiler tercihi değiştiğinde indeks yenileme vardır. Gizli ad/açıklamalar spoiler kapalıyken indekslenmez. Metinler escape edilir, yalnız gerçek sağlayıcı görselleri kullanılır.

Ayar anahtarları arama indeksine gönderilmez. Tüm indeks istemcide yereldir, üçüncü tarafa arama isteği yapılmaz.
