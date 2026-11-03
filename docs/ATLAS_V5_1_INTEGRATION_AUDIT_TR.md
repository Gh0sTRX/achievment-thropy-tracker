# Achievement Atlas v0.14 / Ultimate v5.1 — Entegrasyon Denetimi

**Tarih:** 3 Kasım 2026 (Europe/Istanbul). **Sürüm:** 0.14.0 korunur.
**Çalışma dalı:** `audit/v014-v51-integration`; taban `codex/public-profile-trophies`.
**Yöntem:** kaynak incelemesi + sentetik regresyon/performans testleri. Gözlem,
ölçüm ve doğrulanmamış riskler aşağıda ayrı belirtilir. Profesyonel sızma testi,
sağlayıcı sertifikasyonu veya canlı hesap doğrulaması yapıldığı iddia edilmez.
**Sınır:** main ve mevcut geliştirme dalları güncellenmez; yeni Release/tag yayınlanmaz.

## 1. Önceki proje durumu

Başlangıçta uzaktan güncel referanslar alındı ve dosya farkları karşılaştırıldı:

| Referans | Gözlenen HEAD | Durum |
| --- | --- | --- |
| main | `98f870b908fa73ec2711c2f3fd359eca92a7ab77` | Temel uygulama ve imzalama/gizlilik belgeleri; değiştirilmedi |
| codex/public-profile-trophies / PR #1 | `c43d0525db0bcd2908d3ef34dd4ee3e0f8fff3e8` | 0.14.0 + V5/V5.1 mevcut |
| feature/atlas-ultimate-v5-live-ui / PR #2 | aynı `c43d052…` | PR #1 ile aynı ağaç; taşınmamış dosya/fonksiyon farkı yok |

[PR #1](https://github.com/Gh0sTRX/achievment-thropy-tracker/pull/1) ve
[PR #2](https://github.com/Gh0sTRX/achievment-thropy-tracker/pull/2) açıktı ve Draft
durumundaydı. Açıklamalarındaki eski 79/95 test sayıları güncel kodun kanıtı değildir.
Başlangıç commit'inin [Windows çalışması](https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/41703590930)
ve [birim çalışması](https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/41703590922)
GitHub üzerinden **success** olarak gözlendi; bu, bu audit değişikliklerinin testi değildir.

Kaynak kapsamı: `atlas/*.py` (depo/veri, ayar, Xbox/PSN, cihazlar, öneriler, rehber,
medya, iptal, HTTP, güncelleme/köken, masaüstü/mutex), yüklenen bütün `atlas/web`
HTML/JS/CSS katmanları, `run.py`, testler, requirements, PyInstaller/Inno Setup,
imza/tarama/manifest/update betikleri ve iki GitHub workflow'u incelendi. Çalışma
ortamındaki kullanıcı kitaplıkları, OAuth tokenları veya özel CSV dosyaları açılmadı.

## 2. v5.1’den taşınan değişiklikler

**Gözlem:** iki entegrasyon dalı aynı HEAD olduğundan yeniden merge/cherry-pick
edilecek eksik V5.1 commit'i yoktu. Eski V5 dosyaları güncel kodun üzerine kopyalanmadı.
Bu audit, mevcut özelliklerin test edilmesi ve tespit edilen boşlukların düzeltilmesidir:

- Tarihlerde iki Python giriş noktası aynı doğrulanmış ayrıştırıcıya bağlandı;
  Excel, açık ISO/ay isimleri, belirsiz tarih reddi tutarlı hale geldi.
- Crossfade, yalnız yeni resim gerçekten yüklenince uygulanır; eski yükleme sonucu
  yeni seçimi ezemez. Başarısız URL'de önceki geçerli görüntü/CSS boş durumu korunur.
- Artwork geçişinde en fazla iki görsel düğümü önbelleklenir; aynı/pending URL tekrar
  istenmez, başarısız URL için 60 saniyelik tekrar beklemesi ve 16 kayıt sınırı vardır.
- 15–40 bin kayıt ve array değişimiyle indeks geçersizleştirme ölçüldü; backend aynı
  genel öneri/insight listesini yanıt içinde tekrar hesaplamaz.

Yeni bağımlılık, framework, veri sağlayıcı, oyun resmi veya sahte ilerleme eklenmedi.

## 3. Zaten mevcut olduğu için tekrar uygulanmayan özellikler

- Classic / Ultimate geçişi; Cinematic, Blades, NXE, XMB; ayrı platform filtresi.
- Provider/title/edition kimlikleri, Xbox 360 katalog+kazanım birleşimi, PSN ortak
  kupa listeleri ve Windows/iOS/Android etiketleri.
- Oyun/başarım indeksleri, 48/50 satırlık kasa ve 60/80 kartlık kütüphane sayfalaması,
  geciktirilmiş V5 arama, `/api/status` revision polling.
- Satır altı kupa ayrıntıları, hedefler, notlar, gizli başarımı bilinçli açma,
  Quest Board, Game Universe ve yerel kayıt kapsamlı Hall of Fame.
- Kamuya açık hedef profili, profil arşivleri; medya/rehber/profil durdurma.
- Console Mode dialog/klavye/gamepad, sınırlı polling, kopmada klavye fallback.
- Gerçek artwork cache/yerel dosya/SteamGridDB; kaynak atfı ve kullanıcı seçimi.
- Windows simgesi, mutex, Setup, uygulama içi development updater, Sigstore köken
  doğrulaması ve ayrı stable Authenticode yolu.

## 4. Düzeltilen hatalar

| ID / Öncelik | Doğrulanan sorun ve etki | Düzeltme / kanıt |
| --- | --- | --- |
| F01 Critical | `Controller.public_sync` yalnız `guides.configured()` kontrol ediyordu: anahtarların varlığı izin verilmeden ücretli çağrı başlatabiliyordu. UI tercihi ayrıca gizliydi. | `ATLAS_AUTO_GUIDES == '1'` şartı; görünür ve maliyet açıklamalı seçim. Anahtarlar tek başına, açık 0, açık 1 ve eksik servis ayrı testlendi. |
| F02 High | Rehber durdurma yalnız kupalar arasında kontrol ediliyordu; Brave beklerken durdurulsa da OpenAI başlayabiliyordu. | Her servis aşaması öncesi cooperative check ve ayrı `guides.Cancelled`; devam eden sonuç korunur, sonraki çağrı yapılmaz. Manual üretim auto-off ile bağımsız kalır. |
| F03 High | `Library._read` bozuk mevcut JSON'u boş varsayılan gibi açabiliyordu; sonraki kaydetme özgün veriyi ezebilirdi. | Yalnız olmayan dosyada default; bozuk JSON/kök tipinde açıklamalı fail-closed hata. Özgün byte'ların korunması testli. Tam schema/recovery arayüzü hâlâ eksik. |
| F04 High | 0.13 arşiv tarih/platform normalizasyonundan önce tam dosya yedeği yoktu. | `migration-v014-library.json` ve state yedeği ilk değişiklikten önce exact bytes olarak alınır; var olan yedek ezilmez. Kimlik, pin, bilinmeyen alan ve idempotence testi var. |
| F05 High | `/api/data` içeriği kopyalandıktan sonra revision yeniden okunuyordu. Arada bir worker kaydederse eski veri yeni revision'la sunulup UI güncellemeyi kaçırabilirdi. | Snapshot ve revision aynı kilit altında yakalanır. Rapor hesaplanırken save tetikleyen deterministik yarış testi var. |
| F06 High | Eski Xbox map/sync yolu yalnız title_id arıyor, PSN oyununu açıkça dışlamıyordu. Bazı SDK hata metinleri ham gösteriliyordu. | Xbox platform sınırı; uygulamaya ait açıklama dışındaki istisnalarda sınıf adı. PSN map/schedule reddi ve örnek secret içeren RuntimeError testi var. |
| F07 Medium | Crossfade yükleme başarısızlığını beklemiyordu; geç gelen sonuç/seçim ve tekrar istekleri denetlenmiyordu. | `art_transition.js`, yüklenmiş düğümlerle sınırlı cache, stale-request token, hata fallback'i; Node ve gerçek yerel HTTP resim testi. |
| F08 Medium | İki Python tarih ayrıştırıcısı farklı formatlar destekliyordu; JS bazı geçersiz ay önekleri ve 24:00 gibi clock rollover kabul edebiliyordu. | Ortak normalizer; tam ay adı/abbr doğrulaması, JS saat sınırları; Excel yarım gün, ay/saat reddi testleri. |

Düzeltmeler bu inceleme dalındadır; kurulu/yayınlanmış 0.14 EXE kendiliğinden değişmez.

## 5. Xbox entegrasyon durumu

**Kod gözlemi:** OpenXbox OAuth code/state callback, token refresh, XUID doğrulama,
hedef Gamertag çözümü; sözleşme v1/v2 oyun geçmişi ve pagination, TitleHub metadata.
360 için tam katalog ve hedefin kazanılmış listesi ID üzerinden birleştirilir;
modern kazanılma durumu/progress ayrı normalize edilir. Eşitlemede en fazla üç oyun
çalışır. Aynı hedef ve güvenilir özet/katalog sayısı eşitse 10 dakikalık cache;
`Tam yenile` bunu atlar. 401/403/429 atlatılmaz.

**Test:** hedef XUID'nin servis hesabıyla karışmaması, pagination döngüsü,
360/modern kayıtlar, sıfır kimlik, kısmi hata koruması, cihaz/edisyon ve iptal
mock'ları geçti. Windows workflow SDK kurulum/import ve uygulama paketini test eder.
**Canlı ağ testi:** Xbox/Microsoft login ve Gh0sTRX55 sorgusu bu audit'te yapılmadı.
Oturum yokken gerçek servis erişimi veya hedefin bütün oyunları alındı denemez.

**Eksik:** Xbox DLC grup bilgisinin her modern yanıt için tam normalize edildiği
kanıtlanmış değil (`normalize_achievements` group alanını taşımıyor); eski CSV
map fallback'i ad+puan eşleştirmesine dayanıyor. Tam erişim/katalog kapsamı sınırlıdır.

## 6. PlayStation entegrasyon durumu

**Kod:** gerçek PSNAWP adaptörü vardır. NPSSO operatör oturumu, hedef Online ID ve
account ID, title/communication ID, `trophy_group_id='all'`, kazanılma durumu,
gerçek trophy tier, gizlilik ve rate limit şartlarıyla sorgulanır. Ortak PS3/PS4
listesi tek kimlik olarak korunur; farklı communication ID'ler birleştirilmez.
Güvenilir özet varsa hedefe özel kısa süreli cache kullanılır.

**Test:** fake SDK nesneleriyle hedef kullanıcı/grup/progress ve credential-error
redaksiyonu geçti. Kazanılmış PSN kaydı Gamerscore'a çevrilmez.
**Canlı ağ testi:** NPSSO/hesap erişimi kullanılmadı; Gh0sTRX55'in PSN listesi veya
PS3/Vita/PS5 gerçek cihazları doğrulanmadı. Senkron PSNAWP isteği durdurmayı ancak
istek/generator kontrol noktasında görür; anında ağ abort garantisi yoktur.

## 7. PC/Steam entegrasyon durumu

**Gözlem:** canlı Steam/PC başarım provider'ı yok; görünüm ve filtre vardır.
Xbox ağına ait Windows/iOS/Android oyunları Xbox provider altında kalır. SteamGridDB
bir artwork kaynağıdır; Steam hesap/başarım entegrasyonu değildir. Tema seçmek bağlantı
açmaz. Gerçek PC başarımları veya oynama süresi indirilmiş gibi sunulmamalıdır.

## 8. Artwork ve Türkçe rehber sistemleri

Artwork: yerel dosya / onaylı SGDB adayları / izinli Xbox-PSN URL'leri; HTTPS domain,
redirect, MIME, byte/piksel ve gerçek decode kontrolleri, yerel override önceliği.
API anahtarı bellekte. 11 kaynak kataloğundaki her site için bir adaptör olduğu
iddia edilmez. Gerçek kapak/hero/logo kapsaması oyuna ve sağlayıcıya bağlıdır.
Bu audit üçüncü taraf oyun resmi üretmedi, indirmedi veya paketlemedi; test resminde
projenin kendi Atlas markası kullanıldı.

Rehber: Brave sorgusuna oyun/kupa/cihaz/sürüm; OpenAI'a bunlar + koşul/title ID ve
arama alıntıları/URL'leri gider. Tam rehber aynalama yok; kaynaklı kısa Türkçe model
özeti vardır. Kullanıcı notları/Gamertag/token gönderilmez; giriş metninin kendisinde
kişisel bilgi varsa dolaylı gönderim olabilir. Model kaynak indisleri iddianın
bağımsız doğrulaması değildir. Varsayılan otomatik üretim kapalı; açık onay veya
elle eylem gerekir. Maliyet limiti/ön hesap yoktur.

Bu davranışlar [PRIVACY.md](../PRIVACY.md) içinde veri alanları, DPAPI'nin kapsamı,
açılış bağlantıları, profil geçmişi, yedekler, iptal ve silme yollarıyla güncellendi.

## 9. Performans ölçümleri

**Yerel tek koşum; sentetik veri; gerçek profil/network benchmark'ı değildir.**
Python 3.12 + yerel Chromium, timezone Europe/Istanbul. Fixture adları AUDIT olarak
etiketlendi ve XSS test dizgileri içerdi; veriler yalnız geçici dizinlerde tutuldu.
Tablo script+zorunlu layout süresidir; network, cold-start, resim decode ve paint/FPS
benchmark'ı değildir. Sonuçların 40 bin kayıtta daha düşük olması warm-cache/JIT ve
koşum sırasından etkilenir; ölçeklenmenin daha hızlı olduğu anlamına gelmez.

| Kayıt / oyun | Backend status (3 örnek, ms) | V5 Hub script+layout | V5 Library script+layout | İlk sayfa DOM kartı | `/api/data` gövdesi |
| --- | --- | --- | --- | --- | --- |
| 15.000 / 300 | 163,60 / 197,28 / 196,75 | 40,50 ms | 23,50 ms | 60 | 6.119.080 byte |
| 40.000 / 800 | 521,33 / 539,96 / 578,78 | 31,70 ms | 19,70 ms | 60 | 16.327.450 byte |

- V5 O(G+A) indeksini ham library/games/achievements referanslarına göre yeniler;
  iki array değiştirilerek scope/istatistik cache invalidation doğrulandı.
- Sayfa 2'de de yalnız 60 kart; 40 bin başarımlı kasa modeli 48/50 satır sayfalanır.
- Her poll'da tam veri gelmez; `/api/status` küçük durum yanıtıdır. Revision
  değişiminde **hala tam** library JSON'u taşınır; backend sorting ve JSON/disk
  maliyeti v0.15 teknik borcudur. Guide/media kayıtları sık revision yaratabilir.
- İlk inspector testi devtools response-body cache sınırına takıldı; ürün hatası
  diye raporlanmadı. Ölçüm Content-Length ile tekrarlandı ve tarayıcı koşumu geçti.

Tekrar: `python tests/audit_fixture_server.py` ve ayrı terminalde
`node tests/browser_audit.cjs`. Playwright/Chromium isteğe bağlı geliştirici araçlarıdır,
ürün bağımlılığı eklenmedi. Ham ölçümler/ekranlar `work/audit/` altında, Git'e alınmaz.

## 10. Güvenlik ve gizlilik kontrolü

- HTTP yalnız 127.0.0.1, kesin static path allowlist, Host/Origin ve POST token
  şartları korunur. Yeni art modülü yalnız seçili oyunun güvenli `visualUrl` sonucu
  veya sınırlandırılmış yerel artwork endpoint'ini kabul eder.
- HTML/URL/CSS escaping mevcut pipeline üzerinden; browser fixture'ında `<script>`
  ve `onerror` metinleri çalışmadı. Keyfi yeni dosya servisi eklenmedi.
- OpenXbox token dosyası plaintext SDK deposudur; **yalnız settings.json** Windows
  DPAPI wrapper'ındadır. JSON/profile/cache/yedekler şifreli değildir.
- GitHub startup check ve kayıtlı Xbox reconnect gibi otomatik ağ akışları gizlilik
  belgesinde açıklandı. Ortam değişkenleri yerel ayardan önceliklidir.
- CODE_SIGNING_POLICY güncel Windows paket workflow'uyla karşılaştırıldı: optional
  PFX imzası + stable doğrulama vardır, SignPath onaylı entegrasyon yoktur. Development
  GitHub OIDC/Sigstore köken kontrolü Windows yayıncı imzası veya malware-free kanıtı değildir.
- Bu audit dalı güvenilen development push ref'i değildir. PR build'lerinde iki
  publish işi de skip olmalıdır; yeni tag/Release/ana dala push yapılmaz.

## 11. Test sonuçları

**Yerel son durum:** `python -m unittest discover -s tests -v`: **111 geçti, 0 başarısız**
(96 başlangıç testi + 15 yeni regresyon). Node `test_ui_model.cjs` ve
`test_art_transition.cjs` assert grupları geçti; ayrı bir test-adedi toplamı uydurulmadı.
Tüm yüklenen JS modüllerinin `node --check` kontrolü yapılır.

Chromium: **1920×1080, 1440×900, 980×640, 390×844** boyutlarında yedi V5 sayfası,
scope ayrımı, Classic/V5 geçişi, inline/spoiler, sayfa 2, yanlış HTML dizgileri,
cache invalidation, başarısız resim fallback ve reduced-motion koşumu geçti;
`pageerror` listesi boş. Console dialog odağı, D-pad/analog/A/B, disconnect ve
klavye fallback sanal Gamepad API girdileriyle geçti. Bu fiziksel controller veya
NVDA/JAWS ile ekran okuyucu sertifikasyonu değildir.

**Mock testleri:** Xbox/PSN hedef, katalog, earned, profile switch/restore; SGDB
403/429/aday ve yerel decode; ücretli servislerde opt-in/manual/cancel/network-error;
update manifest/hash/publisher/provenance negatif senaryoları.
**Gerçek ağ:** bu audit'te yalnız GitHub repo/PR/Actions okundu; Xbox, PSN, Brave,
OpenAI ve SGDB için ücretli/oturumlu canlı test yapılmadı.
**Fiziksel cihaz:** gerçek Xbox/PlayStation/gamepad yok.

**Audit PR Windows doğrulaması:** sonuç henüz bekleniyor. Paket/test başarısı burada
önceden ilan edilmez. Native window/icon, frozen SDK/DPAPI, Setup install/uninstall
sonuçları PR checks tamamlandığında bu bölüme işlenecek. Yeni Release yayınlanmaz.

## 12. Kalan kritik eksikler

Aşağıdaki tabloda "risk" kaynak gözleminden çıkarımdır; canlıda hata görülmüş gibi
sunulmaz. Zorluk: S = dar değişiklik, M = birkaç modül, L = çapraz katman/veri taşıma.
**Critical seviyesinde açık olduğu doğrulanmış hata bu audit sonunda bırakılmadı;
High riskler canlı doğrulama ve veri dayanıklılığı için yayın öncesi ele alınmalıdır.**

| ID / Öncelik | Dosya/fonksiyon ve tanım | Kullanıcı etkisi / doğrulama | Öneri / zorluk | Mevcut test kapsamı |
| --- | --- | --- | --- | --- |
| R01 High | `core.build_library` CSV oyunu GameName hash'iyle gruplar; CSV'de edisyon kimliği yoksa aynı ad ayrı sürümleri ayıramaz. | Kaynak-kısıtı/risk: API ID ayrımı doğru olsa da CSV'den kesin edisyon çıkarılamaz; yanlış birleştirme ihtimali. | TA game/page/provider kimliğine dayanan onaylı import şeması, idempotent eşleme/migrasyon; L. | CSV scope/ID testli; iki aynı adlı farklı gerçek TA edisyon export'u yok. |
| R02 High | `server.xbox_login/xbox_reconnect` beklenen adı global library.gamertag ile karşılaştırır; mixed library bu alanı son PSN hedefiyle doldurabilir. | Kod gözlemi: farklı Xbox/PSN adlarında geçerli servis reconnect yanlış reddedilebilir. | Servis XUID'si, platforma ait hedef ve CSV sahibi sözleşmesini ayır; M. | Tek Xbox reconnect ve hedef XUID mock var; karma farklı-ad auth akışı eksik. |
| R03 High | `public_profiles._xbox/_psn`, `xbox.*`: canlı vendor davranışı ve tüm kataloğun kapsamı doğrulanmadı. | Mock başarısı endpoint/session/privacy/rate-limit değişimini garanti etmez; legacy image/CDN ve DLC kapsamı eksilebilir. | Opt-in test hesaplarıyla kayıtlı, credential-redacted contract suite; M/L. | Gerçek SDK import + hedef/pagination/360/PSN grup mock'ları; canlı/cihaz yok. |
| R04 High | `core.save/apply_public_profile` library/state/profile dosyalarını ayrı atomik yazar, tek transaction değildir. | Elektrik/disk-full sırasında dosyalar arası tutarsızlık riski; fail-closed recovery uygulaması açmayabilir. | Journal/generation snapshot ve geri alma/onarım ekranı; L. | Bozuk JSON ve migration yedeği testli; çok dosyalı crash fault-injection yok. |
| R05 High | `scripts/apply_update.ps1`, `updater.install`: gerçek eski→yeni native upgrade/rollback matrisi yok. | Setup smoke, tam self-update ve başarısız upgrade'in eski dosya kümesini birebir döndürmesini kanıtlamaz. Copy rollback yeni orphan dosyaları silemez. | İzole Windows VM'de 0.13→audit upgrade, kesinti/disk/lock senaryoları ve exact rollback manifest; L. | Hash/publisher/proof reddi + temiz install/uninstall; uçtan uca upgrade yok. |
| R06 Medium | `core.apply_live_game`, `xbox.normalize_achievements`: eski CSV fallback ad+puan; modern group/DLC metadata kapsamı sınırlı. | Katalog adı değişince eşleşme kaçabilir; DLC görünümü eksik olabilir. Her kaydı canlı kusursuz diye sunmak yanlış olur. | Kaynak-ID eşleme tablosu ve gerçek DLC fixture'ları; M. | Tek oyun ad+puan, ambiguous skip/360 public ID testli; çok DLC gerçek sözleşmesi yok. |
| R07 Medium | `server.status`, `core.save`, `generate_guides`: full JSON snapshot, sorting ve disk serialization. | 40k'da 16,3 MB yanıt ve ~0,55 sn backend; sık rehber kaydı UI'ı yeniden yükletebilir. | Revision cache/delta API ve batched guide persistence; M/L. | 15k–40k ölçümü, medya batch ve status-revision yarışı var; cihaz bütçesi/SLA yok. |
| R08 Medium | `app.js/ultimate.js/ui/ultimate.js`, CSS katmanları; eski drawer renderer/markup ve global handler override'ları. | Yeni değişiklikte çift olay/odak/selector çakışması riski; V5 cosmetic localStorage değişen origin'de kalıcı olmayabilir. | Tek detail/event façade; erişilemeyen eski drawer'ı kontrollü kaldır, kalıcı UI şeması; M. | İki UI inline, resize, keyboard/gamepad/XSS smoke var; fiziksel okuyucu yok. |
| R09 Medium | `artwork.*`, `media_sync.*`: bütün oyunlar için resmi hero/logo yok; 11 kaynağın çoğu keşif linki. | Eksik artwork normal olabilir; SGDB confirmation otomatik edisyon doğrulaması değildir. | Kaynak bazlı kapsama, attribution ve kullanıcı onaylı kesin katalog eşlemesi; M. | Decode/limit/403/429/local override/crossfade testli; gerçek CDN erişimi yok. |
| R10 Medium | `guides.create/generate_guides`: kaynak alıntısı modelin adımlarını bağımsız doğrulamaz; çağrı maliyet bütçesi yok. | Auto açıkken büyük kütüphane maliyeti ve yanlış rehber adımı riski. | Tahmini çağrı sayısı/bütçe, batch onayı, adım→kanıt ve cache sürümleme; M. | Explicit opt-in/manual/cancel ve source-indices testi var; canlı içerik doğruluğu/fiyat yok. |
| R11 Medium | `settings._values`, OpenXbox token deposu, yerel history/cache/updates. | Ayarlar process-global; SDK token plaintext; cache ve profil/update yedekleri sınırsız büyüyebilir. | Instance-scoped settings, OS credential vault araştırması, retention/clear UI; M. | DPAPI/settings redaksiyon ve offline update testli; çok instance/retention/vault yok. |
| R12 Medium | Requirements sürüm aralıkları, `windows.spec`, `preview/` ve eski metinler. | Aynı kaynakta dependency çözümü değişebilir; Preview ZIP gerçek güncel V5 ile aynı değil. | Reproducible lock/SBOM ve gerçek frontend'den preview üretimi veya eski preview kaldırma; M. | CI SDK/frozen testli; hash-lock/SBOM/bitwise reproducibility yok. |
| R13 High (ürün eksikliği) | PC/Steam achievement adapter mevcut değil. | PC teması gerçek Steam profilini indirmez. | Ayrı izin/kimlik/catalog tasarımı ve contract testleri; L. | Planlandı etiketi ve metrik izolasyonu var; canlı adapter testi olamaz. |

İlk on madde kullanıcıya kısa teslim özetinde öncelik sırasıyla aktarılır; R11–R13
açık ürün/gizlilik/supply-chain borçları olarak ayrıca korunur.

## 13. Önerilen v0.15 geliştirme planı

1. **P0:** Bu audit'in ücret/onay ve arşiv koruması düzeltmelerini review edip
   dağıtım kararı ver. Bu görev otomatik merge/yayın yapmaz.
2. **P0:** R01/R02 için provider/servis/CSV sahibi kimlik sözleşmesi ve bozulmayan
   migrasyon fixture'ları; çok dosyalı crash-recovery tasarımı (R04).
3. **P1:** İzinli Xbox/PSN canlı contract matrisi; DLC/360/PS3/Vita/PS5 kapsamı,
   tam native update/rollback VM testi ve dependency lock/SBOM (R03/R05/R06/R12).
4. **P1:** Delta/status report cache, batch guide kaydı; 40k ölçümünü düşük donanımda
   cold/warm tekrarla. Rehber çağrı bütçesi ve kanıt izleme (R07/R10).
5. **P2:** Tek renderer/event katmanı, ekran okuyucu/fiziksel controller, retention UI
   ve provider artwork kapsamı (R08/R09/R11). Steam adaptörünü bunlardan ayrı, açık
   yetkilendirilmiş bir iş olarak ele al; temayı entegrasyon diye sunma (R13).

Geri alma: PR merge edilmeden mevcut kullanıcı sürümü/depo dalları değişmez. Daha
sonra kod geri alınırsa `git revert` ile audit commit'leri review edilerek geri
çevrilir; migration yedekleri elle ve uygulama kapalıyken gözden geçirilerek geri
konur. Kullanıcının mevcut JSON'unu otomatik olarak eski yedekle değiştirme.
