# Achievement Atlas v0.15 — Kimlik, veri bütünlüğü ve native animasyonlar

**Durum:** Geliştirme/entegrasyon paketi; bu belge gerçek hesap testi veya yayımlanmış sürüm sertifikası değildir.

## Kimlik doğrulama ve profil ayrımı

- Xbox Gamertag ve PlayStation Online ID yalnızca **görünen ad** ve arama girdisidir. Kalıcı bağ sırasıyla XUID ve PSN account ID üzerinden, platform kapsamında tutulur.
- Her servis snapshot'ındaki oyun kimliği, platformu, tekilliği ve başarımın oyun bağı, diske yazmadan önce doğrulanır.
- Kullanıcı adı aynı görünürken farklı bir kalıcı hesap ID'si gelirse arşiv **sessizce değiştirilmez**. Farklı ID'li başka bir oyuncuya geçmek için farklı/güncel görünen adı kullanıp kimliği doğrulamak gerekir.
- Aynı Xbox XUID yeni Gamertag ile gelirse önceki kazanımlar korunur. Xbox suffix `#1234` ayrı kimlik işaretidir; adın kozmetik biçimi kalıcı ID yerine geçmez.
- Otomatik Xbox/PSN senkronizasyonunun gerçek uçtan uca doğrulanması için gerçek hesap erişimi gerekir; mevcut testler sözde servis yanıtlarıyla yapılır.

## Veri günlükleme / kurtarma

- `atlas/journal.py`: normal `Library.save()` işlemleri artık `library.json` ve `state.json` için bütünlük günlüğü kullanır.
- Her iki eski dosyanın **orijinal baytları** geçici kurtarma kopyalarına yazılır, işlem işaretçisi kaydedilir, ardından yeni iki JSON dosyası değiştirilir. İkinci dosya yazımı başarısızsa önceki ikisi de geri getirilir. Uygulama açılışında yarım kalan işlem varsa aynı kurtarma yapılır.
- Koruma `library/state` ikilisi içindir. Ayrı `profiles/`, görseller, kimlik tokenları ve Windows installer için global atomic transaction henüz yoktur.
- Diskte yeterli geçici boş alan gereklidir. Yüksek hacimli 40 bin+ başarımda gerçek performans ölçümü ve ani güç kesintisi testi ayrıca yapılmalıdır.

## Native animasyonlar

- `atlas/web/ui/motion.js` ve `motion.css` tek uygulama kabuğuna yüklenir; bağımsız Atlas Ultimate overlay'i yeniden etkinleştirilmez.
- Farklı sayfalara geçişte 270 ms civarında kısa fade/slide, içerik kademelenmesi ve platform/filtre/oyun seçimi etkileşimlerinde kısa yerleşme animasyonu.
- Cinematic: dikey fade; Xbox Blades: yatay giriş; NXE: hafif scale; XMB: dikey yumuşak geçiş.
- `prefers-reduced-motion` ve Atlas'ın `reduced_motion` ayarı animasyonları devre dışı bırakır. Sayfa içeriği ve klavye odağı geçiş için bekletilmez; hiçbir navigasyon ikinci bir state'e taşınmaz.
- Arayüz animasyonları gerçek artwork ve veriyi değiştirmez; WebView2, klavye odağı, ekran okuyucu ve fiziksel gamepad üzerinde manuel görsel kontrol sürmelidir.

## Testler ve yayın sınırı

`tests/test_identity.py`, `tests/test_journal.py`, mevcut `tests/test_public_profiles.py`, `tests/test_foundation_ui.cjs` ve CI JS syntax check.

Windows installer derlemesi ile Windows **gerçek yükseltme/rollback** testi farklıdır. Geliştirme kanalına otomatik gönderim yapılmamalı; `windows-package.yml` kodunda `codex/public-profile-trophies` dalına doğrudan push yapıldığında Development Release yayınını tetikleyen davranış vardır. Bu nedenle önce **entegrasyon dalında** PR #4 ve #5 sırayla birleştirilerek derleme iş akışı yalnız doğrulama amaçlı çalıştırılır, yayın ayrı işlemle yapılır.
