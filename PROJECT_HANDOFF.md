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


## 4 Kasım 2026 — Foundation arşivleme/kurtarma ek dilimi (PR #5)

Bu oturumda PR #5'in mevcut dalı üzerinde **yeni release üretmeden** şu işler eklendi:

- `atlas/archive.py`: izinli yerel state + aktif library için SHA-256 kontrollü taşınabilir JSON export; hesap tokenları/servis ayarları ve geçmiş profil/medya cache dosyaları export dışında.
- `Library.export_archive()` ve `restore_archive()`: kayıt ID/edition/platform bağlarını koruyan doğrulama; restore öncesi `recovery/pre-restore-*.json` kopyası; iki JSON arasında yarım kalan restore için açılışta marker tabanlı rollback.
- `/api/archive/export` ve `/api/archive/restore`: localhost Host/Origin + token denetimi; restore için açık `confirm:true`, aktif eşitleme/güncelleme engeli.
- Hesap & Veri ekranında yerel arşiv indir/yükle kontrolleri; açık kullanıcı onayı ve hata durum mesajları.
- `tests/test_archive.py` (round-trip, API auth+confirmation, hash, platform ayrımı, restore failure/rollback), `tests/test_foundation_ui.cjs` yapısal ek kontrolleri.
- Ayrıntı ve sınırlamalar: `docs/V015_ARCHIVE_RECOVERY_TR.md`.

**Önemli:** PR #4 önce incelenmeli; PR #5 hâlâ PR #4 üstünde bağımlı DRAFT. `codex/public-profile-trophies`, `main` ve Development Release'e doğrudan merge/publish yapılmadı. Bu dilim, uygulamanın **diğer** `save()` çağrıları için tam çoklu-dosya transaction garantisi sağlamaz. Arşiv kişisel oyun kayıtlarını içerir, herkese açık repoya konmamalı. Yeni oturumda PR #5'in son commitindeki CI/Windows installer sonucunu mutlaka kontrol et.

**Sonraki P0:** Gerçek Windows installer + 0.13/0.14.1 yükseltme/rollback testi; karma Xbox XUID/gamertag ve PSN ID ayrımı, CSV edition/DLC doğruluğu; ardından diğer dosyaların transaction/migration sistemine geçirilmesi. Gerçek platform hesapları ve fiziksel gamepad sonuçları olmadan doğrulanmış deme.


### Ek P0 veri izolasyonu düzeltmesi

`Library.import_csv()` artık Xbox TrueAchievements CSV içe aktarımında önceden kayıtlı PSN/PC oyunlarını, kupalarını ve sabitlenmiş hedeflerini silmez. Yeni CSV sonuçlarının oyun/başarım sayısı yalnız içe aktarılan Xbox kayıtlarını raporlar; başka platformla çakışan oyun ID'sinde içe aktarma iptal edilir. Karma arşiv `platform=mixed` ve `complete_export=False` işaretlenir. Regresyon: `tests/test_core.py::test_xbox_csv_import_preserves_psn_records_and_pins`. Bu, aynı adlı Xbox edition/DLC kayıtlarının güvenilir eşlenmesi sorununu henüz çözmez.


## 4 Kasım 2026 — Yeni P0 + native motion devamı

- `atlas/identity.py`: Xbox XUID ve PSN account ID'nin platform kapsamlı kontrolü; aynı görünen ad/farklı kalıcı ID çakışmasında yazmayı reddetme; gelen oyun/kupa platform ve oyun bağı doğrulaması.
- `atlas/public_profiles.py` kimlik kontrolü; `atlas/core.py::apply_public_profile` kayıt öncesi kimlik güvenliği. Canlı hesap testi yapılmadı. `tests/test_identity.py` ve mevcut profile testleri.
- `atlas/journal.py`: sıradan `Library.save()` çağrılarını iki JSON dosyalı kurtarılabilir yazma günlüğüne geçirir. Başlangıçta yarıda kesilmiş işlem geri alınır; `tests/test_journal.py` donma/başarısız disk yazımı senaryoları.
- `atlas/web/ui/motion.js/css`: tek yerel shell üzerinde temaya göre sayfa/filtre/oyun geçişleri; `prefers-reduced-motion` ve uygulama hareket azaltma tercihi dikkate alınır. Eski Atlas Ultimate overlay'i etkinleştirilmez.
- `docs/V015_IDENTITY_STORAGE_MOTION_TR.md` teknik sınırları ve testleri açıklar. Eski `profiles/`, artwork cache, Windows rollback hâlâ genel transaction kapsamı dışında.

**Yayın tuzağı:** `.github/workflows/windows-package.yml` içindeki `push: codex/public-profile-trophies` yayın akışını (`publish-development`) otomatik tetikler! Kullanıcı mevcut Development sürümünü korumak istediğinden PR #4 / #5 önce bağımsız `integration/atlas-v015` dalında sıralı birleştirilmeli; son installer build için entegrasyon → codex yönünde ayrı draft PR açılmalı. `codex/public-profile-trophies`, `development` Release ve `main` üzerinde yayınlama/otomatik push olmamalıdır. Son test/PR durumunu yeni sohbette yeniden denetle.
