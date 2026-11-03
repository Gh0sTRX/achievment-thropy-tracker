# Achievement Atlas v0.14.1 — Atlas Ultimate V5.1 bakım güncellemesi

**Yayın kanalı:** GitHub `development` (ön sürüm). Bu sürüm `main` için değil, güvenilen `codex/public-profile-trophies` dalının Windows derlemesi içindir.

## Düzeltilenler

- **İzinsiz API maliyeti önlendi:** Brave/OpenAI anahtarları tanımlı olsa bile otomatik Türkçe rehber sorguları yalnız `ATLAS_AUTO_GUIDES=1` açık izinle başlar. Elle başlatma ayrı tutuldu; arayüze izin ve maliyet açıklaması eklendi.
- **Güvenli veri taşıma:** Eski JSON veri ve tercih migrasyonlarından önce özgün dosya yedeği; bozuk JSON'da sessiz sıfırlama yerine hata. Mevcut başarımlar, sabitlenen hedefler ve profil kayıtları korunur.
- **Tutarlı veri sürümü:** API veri görüntüsü ile revision aynı kilitle okunur; eşitleme ve kısmi indirme hatalarında önceki veriler korunur.
- **Görsel iyileştirmesi:** Sinematik wallpaper crossfade yalnız resim başarıyla yüklendiğinde gerçekleşir; eski/güncel olmayan istekler yeni seçimi ezemez, başarısız görsellerde fallback bulunur ve azaltılmış hareket desteklenir. **Yapay zekâ oyun görseli oluşturulmaz.**
- **Tarih ve zaman çizelgesi:** Geçerli ISO/İngilizce ay adları/Excel seri tarihlerinde tutarlı yorumlama; iki farklı biçimde yorumlanabilecek tarihleri tahmin etmeme.
- **Xbox/PSN kapsam ve güvenlik:** Xbox-only eski senkronizasyon yollarında PSN oyunlarını reddetme, beklenmeyen SDK hata mesajlarında potansiyel gizli değerleri ifşa etmeme.
- **Gizlilik belgeleri:** PSN servis oturumu, üçüncü taraf rehber istekleri, Windows DPAPI ve yerel arşiv açıklamaları güncellendi.

## Neler hâlâ eksik?

- Gerçek Xbox ve PSN hesaplarıyla ağ üzerinde uçtan uca doğrulama yapılmadı. Kullanıcı adıyla profil sorguları **işletmeciye ait servis erişimi** gerektirir; uç noktaların kullanılabilirliği değişebilir.
- Steam/PC başarım entegrasyonu yapılmadı. SteamGridDB yalnız artwork sağlayıcısıdır.
- Fiziksel gamepad, ekran okuyucu ve **eski kurulumdan yeni kurulumun kesintili/başarısız geri alma** senaryoları bağımsız sertifikasyon görmedi.
- Özel ticari oyun görselleri paketlenmedi; gerçek görsel seçimi kullanıcı/sağlayıcı izinlerine bağlıdır.
- Windows Authenticode/SignPath kod imzası **onaylı değil**. GitHub/Sigstore derleme köken kanıtı, Windows yayıncı sertifikası veya zararsızlık garantisi değildir.

## Yayın doğrulaması

Yeni `0.14.1` kaynağı üzerinde Windows build/install, Python+Node regression suite, GitHub/Sigstore attestation, doğrulama manifesti ve Release varlığı **yayın işinden sonra ayrı kontrol edilmelidir**. Bu dosyanın varlığı tek başına Release işleminin başarılı olduğu anlamına gelmez.

[Kaynak ve teknik borç raporu](ATLAS_V5_1_INTEGRATION_AUDIT_TR.md) · [Privacy](../PRIVACY.md) · [Code signing](../CODE_SIGNING_POLICY.md) · [Windows indirme](WINDOWS_DOWNLOAD_TR.md)
