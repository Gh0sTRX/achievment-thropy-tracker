# PROJECT_HANDOFF — Achievement Atlas

**Tarih:** 3 Kasım 2026. Bu sürüm kontrollü belge yeni ChatGPT/Codex oturumlarında kaldığımız yerden devam etmek içindir. GitHub'daki commitleri, PR durumlarını ve CI sonuçlarını her yeni oturumda yeniden sorgula; bu belge geçmiş anlık kayıttır.

## Ürün ve tercihlerin değişmeyen temeli

Depo: https://github.com/Gh0sTRX/achievment-thropy-tracker (depodaki yazım aynen korunur).
Windows için local-first achievement/trophy companion. TrueAchievements CSV ve deneysel Xbox OpenXbox/PSN PSNAWP bağlantıları, Quest Board, Hall of Fame, Game Universe, gerçek oyun kapak/logo/hero seçimi, isteğe bağlı Türkçe kaynaklı rehber içerir.

- **Tek uygulama kabuğu:** Cinematic, Xbox 360 Blades esintili, Xbox 360 NXE esintili, PS3 XMB esintili temalar asıl uygulamaya giydirilir. İkinci Atlas Ultimate overlay'i yeniden oluşturma.
- **Console Mode** isteğe bağlı tam ekran; gerçek library ile çalışır; bir başka API sağlayıcısı değildir.
- **Sahte achievement, sahte platform hesabı, uydurma oyun istatistiği veya uydurma kazanma süresi yok.**
- **Yapay zekâ ile oyun görseli üretme.** Gerçek, kullanıcı tarafından seçilmiş veya mevcut izinli/onaylı kaynaklardan gelen görseller; kullanıcı seçimi öncelikli, yanlış edition resmi otomatik kullanılmaz.
- Brave/OpenAI ücretli rehber çağrıları otomatik varsayılan kapalıdır. Açık kullanıcı izni gerektirir. OAuth token, NPSSO, API anahtarları, kişisel CSV ve yerel kullanıcı verilerini commit/rapora ekleme.
- Kullanıcının veri klasörünü ve main dalını koru. Gerçek Xbox/PSN hesabı veya fiziksel gamepad test edilmeden doğrulandı deme.

## Git dal/PR zinciri

1. **main**: eski temel sürüm; şu anki geliştirmeleri otomatik üzerine alma.
2. **codex/public-profile-trophies**: v0.14.1 Development Release tabanı; taslak PR #1, main dalına karşı.
3. **feature/atlas-ultimate-v5-live-ui**: önceki taslak PR #2; güncel v5.1 zaten geliştirme dalında, eski dosyaları üzerine kopyalama.
4. **feature/unified-native-themes**: PR #4; dört temayı tek native shell'e indirir, ayrı Console Mode ve Timeline.
5. **feature/v015-foundation-onboarding-recovery**: PR #4 dalından türemiş v0.15 Foundation başlangıcı; beş ana menü, ilk açılış rehberi, kaynak durum şeridi, ayrıntılı update blockers ve iptal.

**Birleştirme sırası:** Önce PR #4 inceleme ve testlerden sonra codex/public-profile-trophies'a; ardından Foundation PR'ı yeniden tabanlanarak aynı dala. main veya Release için otomatik merge/publish yapma.

## Yayın ve güven

Son yayımlanan sürüm: **Achievement Atlas v0.14.1 Development**
https://github.com/Gh0sTRX/achievment-thropy-tracker/releases/tag/development

GitHub/Sigstore build provenance, Windows Authenticode/SignPath yayıncı imzası değildir. SignPath Foundation başvurusunun onaylandığını iddia etme. Testli Setup; fakat gerçek kullanıcı ortamında eski sürüm yükseltme / veri kurtarma / tam rollback doğrulaması eksik.

## Önemli kaynak dosyalar

- atlas/core.py: CSV, library/state dosyaları, provider merge, yedek/migrasyon.
- atlas/public_profiles.py, atlas/xbox.py: Xbox ve PSN adapter'ları; mock test mevcut, gerçek ağ doğrulaması eksik.
- atlas/server.py: localhost HTTP, token/Origin, veri, iş/stop denetimleri, update blocker adları.
- atlas/updater.py, atlas/provenance.py, scripts/apply_update.ps1: güncelleme ve köken/rollback.
- atlas/web/index.html, atlas/web/app.js, atlas/web/ultimate.js: native arayüz ve başarım mantığı.
- atlas/web/ui/shell.js ve shell.css: dört native tema, Console Mode, genel Timeline.
- atlas/web/ui/foundation.js ve foundation.css: sade navigasyon, boş data onboarding, kaynak durumu, güncelleme blocker UX.
- atlas/web/ui/ultimate.js ve ultimate.css: eski ayrı overlay dosyaları; aktif index.html'de yüklenmez.
- atlas/preferences.py: doğrulanan kalıcı görünüm tercihleri.
- tests/: Python / Node CI. Eski tests/browser_audit.cjs ayrı overlay beklediğinden yeni native GUI smoke'a uyarlanmalı.

## Halen açık yüksek önem sıralaması

1. Xbox/PSN gerçek servis oturumu, yetki, pagination, DLC, public profile limitleri ve cihazlarda uçtan uca doğrulama.
2. Karma Xbox/PSN profil adlarında hesap/XUID eşleştirme ayrımı.
3. CSV aynı isimli farklı edition ve DLC kapsamının kaynağa bağlı güvenilirliği.
4. JSON library/state/profile transaction, dışa aktarma, geri yükleme ve onarım.
5. Gerçek 0.13/0.14.1→yeni sürüm Windows yükseltme ve başarısız rollback matrisi.
6. 40 bin kayıtta büyük tek JSON ~16 MB; delta API, revision ve cache iyileştirme.
7. Oyun artwork'ü kapsama / edition / kaynak lisansları; kullanıcı override.
8. Steam/PC provider henüz yok; yalnız platform filtresi var.
9. Fiziksel gamepad, erişilebilirlik, mobil/XMB responsive gerçek kullanım testleri.
10. Rehberlerin kota/maliyet/kanıt doğruluğu.

Ek ayrıntı: docs/ATLAS_V5_1_INTEGRATION_AUDIT_TR.md ve docs/V015_FOUNDATION_PLAN_TR.md.

## Yeni sohbet için hazır devam isteği

"Achievement Atlas'a devam et. Önce https://github.com/Gh0sTRX/achievment-thropy-tracker deposundaki PROJECT_HANDOFF.md dosyasını ve docs/V015_FOUNDATION_PLAN_TR.md planını oku. PR #1, PR #2, PR #4 ve Foundation PR'ını kontrol et; branch commitleri/CI/Windows build durumlarını canlı doğrula. Foundation geliştirmelerini birleştirme zincirini bozmadan sürdür; ilk önce gerçek UI/ilk açılış ve güncelleme veri dayanıklılığı, ardından gerçek Xbox/PSN entegrasyon doğrulaması ve archive export/restore. Kullanıcı verisini, gerçek oyun artwork ilkesini ve main dalını koru. Açık onay olmadan yeni Release yayımlama."

## Dürüstlük notu

Bu belge bir kontrol listesi, canlı sürüm sertifikası değildir. En son Foundation dalının Windows sonucu, PR numarası ve GitHub Actions durumu belgenin oluşturulmasından sonra değişebilir. Yeni sohbette tekrar kontrol edilmelidir.
