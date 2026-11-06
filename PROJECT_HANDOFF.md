# PROJECT_HANDOFF — Achievement Atlas

Geç gelen artwork yanıtları: manuel seçim fetch'i dosyayı yazmadan önce profil/
edisyon/cihaz/eşleştirme ve kategori metadata'sını immutable snapshot ile tekrar
doğrular. Yeni user_file ve farklı profil korunur. Aday sorgusunda in-place
edisyon değişimi reddedilir; upload cache+metadata yazımı tek lock altındadır.
docs/ISSUE_37_STALE_ART_RESPONSES_TR.md, üç yeni yarış regresyonu. Son HEAD CI
ayrıca izlenir; 8b4331a Unit/Windows işleri başarılıydı. PR/merge/release yok.

Görsel devamı: custom reset öncesi provider URL kaybı ve manuel SGDB seçiminin
site ana sayfasını dosya kaynağı gibi saklaması düzeltildi. Yeni kayıtlar gerçek
image source_url + ayrı page_url ve oyun/edisyon kimlikleri taşır. Farklı edisyon
kaynağı reset ile geri getirilmez. docs/ISSUE_37_CUSTOM_ART_RECOVERY_TR.md.
Yeni HEAD CI ayrıca izlenmeli; be22f1e Unit/Windows işleri başarılıydı. PR yok,
merge/release yok. Canlı artwork kapsamı hâlâ ölçülmedi.

PSN devamı: reuse platform/title/edisyon/cihaz eşitliği ve trophy_groups deep copy
koruması; PSN 401/403/429/TooManyRequests kod/sınıfının güvenli hata mesajında
korunması. docs/ISSUE_37_PSN_REUSE_TR.md. Bu canlı PSN hızı/kabulü değildir.
Sonraki exact-head CI yeniden izlenmeli; önceki dd237a9 iki CI işi başarılı.
Yeni PR/merge/release yok, kaynak dalı korunur.

Görsel devamı: tek 403 tüm sağlayıcıların indirmesini durduruyordu; host kapsamlı
403 engeli eklendi. Aynı host'a yeni istek yok, önceden seçilmiş bağımsız host
adayları devam edebilir. 401/429 ve kullanıcı iptali global stop korunur.
docs/ISSUE_37_MEDIA_FORBIDDEN_SCOPE_TR.md. Gerçek kapak kapsamı ölçülmedi.
94c0ada Windows 42241833904 ve Unit/Chromium 42241833771 başarılı; bu yeni
kaynak için exact-head CI ayrıca izlenmeli. PR/merge/release yok.

Xbox refresh devamı: kilitsiz eski token okuması üç-thread mock ile yeniden
üretildi; süreç içi read/refresh/write guard eklendi, API sorguları kilit dışında.
Dört yeni test ve sınırlar docs/ISSUE_37_XBOX_REFRESH_RACE_TR.md. Bu canlı
offline→online hatasının kesin kök nedeni kabulü değildir. Son kaynak için
Windows/Unit CI yeniden tamamlanmalı; ea00c20'ın iki CI işi yeşildir ama yeni
kodun kanıtı olarak kullanılamaz. Yeni PR/merge/release yok.

Yeni ana emir: docs/POST_0161_MASTER_ACCEPTANCE_TR.md. Başlangıç 955f236,
228 Python ve dört Node suite başarılı. Artwork Health/indirme kaynak uygunluğu
ortaklaştırıldı; edisyon/user-file ve retained app sayımı düzeltildi. Aktif kaynak
dalı Windows push test filtresine eklendi; publish/promote guard'ları değişmedi.
Yeni HEAD için CI/Windows sonucu tamamlanmadan hazır veya yayımlandı denmez.
Gerçek Xbox/PSN/Steam hesap, gerçek artwork kapsamı ve fiziksel gamepad/NVDA
doğrulanmadı. Açık PR yok, yeni PR/merge/release yok.

Sonraki kaynak çalışması: sınırlı Next Move ayrı `next_moves` raporu ve ana
ekran/hedef/oyun öneri alanlarına bağlandı. En fazla üç farklı oyun; pin,
kayıtlarda tamamlanmaya yakınlık ve geçerli son kazanım tarihi. Kaynak ve
bilinmeyenler açık; TA ratio/GS ağırlığı yok. Eski rank uyumluluk için korunur.
226 Python testi; docs/ISSUE_37_NEXT_MOVE_TR.md. 54a76b1 Unit tests başarılı
(42235578403), Windows o test/docs-only push'ta tetiklenmedi; önceki Windows
koşusu yeni Next Move kaynağının kanıtı değildir. Yeni kaynak CI ayrıca izlenir.
Açık PR/release/main-dev merge yok. Gerçek kullanıcı kabulü hâlâ yapılmadı.

Son CI takibi: f3d2a0d Unit tests kırmızısı Console Mode testindeki kalıcı
oyun seçimi varsayımındandı (42234874945 / 42234866618). Kapaklı ve kapaksız
fixture artık açıkça seçiliyor. Aynı CI sırasındaki 11 Chromium script'i
yerelde birlikte geçti; 5k/15k/40k ve gamepad simülasyonu dahil, fiziksel kabul
değil. Sonraki kaynak SHA için uzak CI yeniden beklenir; eski kırmızı sonuç
saklanır. Açık PR yok, kaynak dalından devam; merge veya release yok.

## Son kullanıcı emri — eksikleri sürdür ve açık PR'ları kapat

Tek teslimat dalında PSN ilk listeleme sırasında iptal/progress ve Console Mode
okunaklı kapak/metin/kontrol düzeni eklendi. Python 222 test. Gerçek PSN hız
kazanımı veya fiziksel kontrolcü kabulü iddia edilmez. #43 kullanıcı talebiyle
merge edilmeden kapatılacak; bu tamamlandı/release anlamına gelmez. Kaynak
`fix/37-confirmed-xbox-artwork-candidates` dalında korunur. Aşağıdaki tek açık
PR anlatımları tarihsel durumdur. Main/dev/release değişmez. Yeniden geliştirme
için bu daldan devam et; yeni PR açmak mevcut kullanıcı tercihi değildir.

## 6 Kasım — PR konsolidasyonu (önce bu bölümü oku)

Kullanıcı açık PR birikimini kapatıp işi bütünleştirmeyi istedi. Tek teslimat
PR #43, hedef `codex/public-profile-trophies`: #23–#26, #38–#39 ve #41–#42
kaynakları ve belgeleri bu dalda korunur. Eski incelemeler yerine geçen #43
belirtilerek kapatılır; dallar silinmez. #1/#2 main incelemeleri de kapatılır;
main veya geliştirme dalına merge ve release yapılmaz. Aşağıdaki eski PR
durumları tarihsel kayıttır, güncel açık PR listesi değildir.

Kullanıcı Windows gözlemi: offline, tarihler, trophy ikonları, not/pin kalıcılığı
çalışıyor; kapaklar eksik. Xbox yeniden başlatınca toparladı, kök neden kabulü
yok. PSN ilk eşitleme yavaş; Console Mode şikâyeti düzen/konsol hissi.
Offline/online göstergesi kullanıcı talebiyle yalnız sırada; hemen uygulanmaz.
Yerel test son kodda 219 Python; tam satır, cache recovery ve onaylı TitleHub
görsel kategorileri dahil. Yeni birleşik HEAD CI sonucu ayrıca doğrulanmalıdır.
Gerçek PSN/Steam kabulü, fiziksel gamepad ve NVDA henüz doğrulanmadı.

Devam düzeltmesi: profil kaydından sonraki opsiyonel media/guide başlatma hataları
hesap eşitleme hatası olarak gösterilmez. Ağ hatası sonrası aynı uygulamada
yeniden deneme ve not/pin/arşiv koruma mock testi eklendi; canlı Xbox hatasının
kök nedeni doğrulandı denmez. Yeni toplam 221 Python testi; exact-head CI yeniden
kontrol edilir. Yeni PR açılmaz, mevcut #43 güncellenir.

**Güncellendi:** 6 Kasım 2026. Bu sürüm kontrollü belge yeni ChatGPT/Codex oturumlarında kaldığımız yerden devam etmek içindir. GitHub'daki commitleri, PR durumlarını ve CI sonuçlarını her yeni oturumda yeniden sorgula; bu belge geçmiş anlık kayıttır.

## Aktif üst emir — #37: offline arşiv + sınırlı hedef planlayıcısı

Kullanıcı #37 / #35 / #36 ve #27–#34 planını uygulamak için “devam et” dedi. Öncelik Xbox-first, sonra yetkili Steam/PSN; yeni tema/platform/sosyal/launcher/LLM özellikleri ve büyük mimari rewrite yok. **Main veya geliştirme dalına otomatik merge ve yeni Development Release YOK.** Yayımlı kanal 0.16.1 değişmedi.

#25'in native history/focus kırılması kaynak `9512d149ae6e17b92cf01a4d1c6d8a380342ca5a` ile giderildi: Windows `42134533000`, unit PR `42134532809` başarılı; 203 Python + Chromium regressions. Gerçek düğme anchor'ı taşınmadığı için fazladan Vault rotası oluşuyordu; render sonrası aynı kayıt odağı da korunuyor. Eski başarısız koşu `42107565658` saklanır; test atlanmadı.

Yeni küçük PR'lar: #38 (`fix/37-offline-archive-contract`, kaynak `1b78d0702f13df63d14e80de87f207e78faa4827`) Steam/PC profili yüzünden export/recovery backup reddini ve platform ad/uyarı kaybını düzeltir; 211 test. #39 (`fix/37-archive-file-transport`, kaynak `da489e465b428f554341ff055c544338210a6d8e`) tarayıcının JSON yeniden yazımında 1.0→1/büyük sayı değişimi ile hash bozmasını, ham export/import ile düzeltir; 215 test ve gerçek UI indirme/restore tarayıcı senaryosu. Hash/Host/Origin/token/onay/boyut korumaları kaldırılmadı. Son CI kanıtı docs/ISSUE_37_STATUS_TR.md'de tutulur.

Kullanıcı 6 Kasım'da kendi Windows cihazında **arşiv kopyasıyla gerçek Xbox kabulü yapabileceğini** bildirdi. Henüz gerçek sonuç alınmadı. Parola/token/API anahtarı isteme veya public rapora koyma. Deneme protokolü docs/ISSUE_37_WINDOWS_ACCEPTANCE_TR.md. JSON yedek medya dosyalarını içermez; aynı klasörde cache korunması taşınabilir tam medya yedeği değildir.

Mevcut bağlam: #23 → #24 → #25 kodları incelemeye açık; #38 → #39, #25 üstüne küçük ekler. #26 yalnız belgeler, yeni kanıtları toplar. Hiçbirini otomatik birleştirme. Alan bazlı provenance kısmi; tam offline fiziksel Windows, gerçek hesaplar, NVDA/gamepad, portable media backup ve bağımsız güvenlik/p95-RAM ölçümü bitmedi. Next Move MVP, bu kabul kapıları olmadan büyütülmez.

## Aktif görev — Issue #22 kaynak düzeltmeleri, YAYIN YOK

Kullanıcı Issue #22'nin tamamını uygulamayı, küçük test edilebilir PR'lar ve rapor vermeyi istedi. **Bu görevde main/geliştirme dalına otomatik merge ve yeni Development Release YOK.** Önceki 0.16.1 yayın yetkisi bu yeni işe taşınmaz.

PR zinciri: #23 `fix/22-achievement-universe` → codex; #24 `fix/22-media-provenance` → #23 dalı; #25 `fix/22-provider-setup-history` → #24 dalı. Son #22 kaynak `9512d149ae6e17b92cf01a4d1c6d8a380342ca5a`. Hepsi incelemeye açık tutulur. Bu belge doğrulama dalında; yeni sürüm yayımlanmadı, sürüm 0.16.1 kaldı. Geliştirme tabanı `145accefdf1053d826249d52e54aeba6aa69fbfd`, main `98f870b908fa73ec2711c2f3fd359eca92a7ab77` korunur.

Uygulandı: Vault/Universe ortak satır ve gerçek tarihler/kaynak/ikon/açıklama; URL'siz yerel ikon; decode sıralı kompakt hero/kapak; gerçek görsel sayaçları ve güvenli cache; açık kimlik onaylı Xbox metadata zenginleştirme; görünür ve düzeltilmiş keşif HTTP akışı; PSN/Steam uygulama içi ayar+ayrı bağlantı testi; platform ad/durum/geçmiş ayrımı; global sarı bant yok; rehber hatası ayrı; legacy app filtresi ve oyun vitrin/öneri/media hariç tutma; CSV/pin/not/metadata/yerel görsel koruma. Gizli bilgi girilen alanlar temizlenir, mevcut DPAPI sürer. Resmî Sony OAuth veya anahtarsız Steam vaadi yok.

Yerelde 203 Python, dört Node suite, yeni metadata/setup Chromium testleri ve önceki Universe/search/16 theme/5k–40k/gzip/partial/gamepad/reduced-motion kontrolleri geçti. Windows son kaynak CI sonucu başarılı; audit dosyasında koşular kayıtlı. Gerçek PSN/Steam/Xbox kabulü, fiziksel gamepad/NVDA ve kullanıcı arşiviyle önce/sonra art kapsamı ölçülmedi. Test kayıtları sentetiktir, gerçek başarımlar diye raporlanmaz.

Rapor: docs/ISSUE_22_REAL_USER_UX_AUDIT_TR.md. PR'ları ve Actions'ı yeniden sorgulamadan başarılı/release var deme. Sonraki işlem kullanıcı incelemesi ve gerçek izinli hesap kabulüdür; yeni sürüm/main merge için açık yeni talep gerekir.

## 0.16.1 YAYIMLANDI — en güncel sonuç

Kullanıcı “devam et ve yayınla” talebi tamamlandı. PR #21 (18 dosya) geliştirme dalına merge edildi; main `98f870b908fa73ec2711c2f3fd359eca92a7ab77` korunur. Kaynak `1a3fab89be01f3283e62ea67f98ebfc6a35156bf`; Windows trusted push/yayın `42096532071`, 184-test matrix/browser/PowerShell `42096532065` başarılı. Gzip/kısmi yenileme, rapor/scope cache, geç yanıt koruması ve artwork health POST düzeltmesi. 40k sentetik ilk JSON 16.327.656→696.660 byte; değişmeyen yanıt 2.030 byte. Gerçek hesap hızı değildir.

Installer `AchievementAtlas-0.16.1-Windows-x64-Setup.exe`, 33.313.129 byte; SHA256 `509637b9ebe5c8da04d1b4a60ae9a3c602a68e5858c4ff53f96184e46224b577`. Canlı manifest HTTP ve GitHub asset digest eşleşti; authenticode_signed false. Yayın SONRASI stok **0.16.0→0.16.1** native UIA indirme/doğrulama/kurulum/yeniden açılış/veri koruma başarılı: PR21 Windows `42095260152`, job `127491971929`, artifact `13449205024`. Log gerçek sürüm geçişini doğrular; artifact içeriği yerelde açılmadı. İlk sabit90ms gamepad test flake'i örnekleme beklemesiyle düzeltildi. Uzayan yinelenen PR Linux görevi de sonunda başarılı; koşu `42095260009` tamamlandı.

Ayrıntı docs/RELEASE_NOTES_0_16_1_TR.md. Gerçek hesap/fiziksel cihaz/Windows imzası eksikleri sürer. Sonraki çalışma: hesap kabulü, artwork kapsamı, düşük donanım ve açık CI job süre sınırları. Yeni yayın için açık kullanıcı talebi gerekir; rutin belge commit'inde publish marker kullanma.

## 0.16.0 YAYIMLANDI — en güncel sonuç

5 Kasım 2026: Kullanıcının açık yayın talebi tamamlandı. PR #11–#20 geliştirme dalında birleştirildi (ana ürün zinciri #11–#18; #19 kuyruk/alt süreç temizliği, #20 tek okumalı UIA ad eşlemesi). Main `98f870b908fa73ec2711c2f3fd359eca92a7ab77` korunur.

- Yayın kaynak commit'i: `165145886d67f236021b1b551b345341eb0d7563`.
- Başarılı trusted push/attestation/publication koşusu: `42089196768`.
- Başarılı 175-test Windows/Linux/JS/PowerShell/browser koşusu: `42089196427`.
- GitHub development release: Achievement Atlas 0.16.0 — Development.
- Installer: `AchievementAtlas-0.16.0-Windows-x64-Setup.exe`, 33.316.608 byte.
- SHA256: `498c7ead5cdc6e0692b9232c5b1a8a2056111b482bd91ad391bb44d79294563b`.
- Gerçek yayın manifesti HTTP üzerinden doğrulandı: version 0.16.0, source_commit yukarıdaki commit, run_id 42089196768, authenticode_signed false.
- Yayın SONRASI stok **0.15.1→0.16.0** native UIA düğmeleri, indirme/köken/hash/helper/installer/yeniden açılış ve kayıt koruma testi başarılı. PR20 Windows koşusu `42089180677` tekrar çalıştırıldı; native job `127466984546`; log açıkça `Native self-update passed: 0.15.1 -> 0.16.0` der. Rapor artifact `13443839045`. Artifact ZIP yerel indirmesi ağ politikası nedeniyle alınamadı; başarı kanıtı GitHub job/log ve artifact kaydıdır, içerik yerelde açıldı diye raporlama.

Eski bekleyen yayın koşusu 42086939651 iptal edildi. Başarısız UIA adayının (42088444741) yayını yapılmadı. Yeni kuyruk ayrımı ve süreç ağacı temizliği test/hash/attestation kontrollerini kaldırmaz. Gerçek hesap, fiziksel gamepad/ekran okuyucu/güç kesintisi/logon, kapsamlı artwork ve Windows imzası eksikleri sürer. Ayrıntı docs/RELEASE_NOTES_0_16_0_TR.md.

Uygulama içi güncelleme: Diğer ekranlar → Güncellemeler. Rutin belge/kod commit'inde `[publish-development]` kullanma; sonraki yeni sürüm yayını ayrı talep olmalıdır. Bu bölümden önceki “yayımlanmamış/yayın yok” kayıtları tarihî hazırlık durumlarıdır.

## En son yetki — 0.16.0 release hazırlığı

Kullanıcı son mesajında “devam et eksiklerimiz neler onu da söyle relase ye” diyerek yayın istedi. Önceki “yeni release yayımlama” sınırı bu yeni yayın talebiyle güncellendi; main korunur. 0.16.0, PR #11–#17 zinciri üzerine hazırlanır. Release dalı `release/0.16.0`; ayrı release PR'ı, test, geliştirme dalına merge ve yalnız yetkili `[publish-development]` commit marker'ı ile trusted push yayını kullanılır. Parola/anahtar, imza veya provenance kontrolleri atlanmaz. Yayın sonucunu Actions/manifeste bakmadan tamamlandı sayma.

Yeni release notu: docs/RELEASE_NOTES_0_16_0_TR.md. Kalan on eksik orada; gerçek hesap, fiziksel cihaz ve imza eksikleri sürer. Yeni self-update testi, yayın sonrası 0.15.1→0.16.0 stok kurulumunu doğrulamak için 0.15.1 baseline hash'ini içerir.

## Son devam — Steam sınırlı paralellik (yayımlanmamış)

Yeni dal `feature/steam-bounded-sync`, PR #16 üzerine. En fazla üç oyunluk bounded batch, kopyalanan cache/force/stop bağlamı, auth/429 sonrasında yeni grupları engelleme ve kararlı sonuç sırası eklendi. 175 test yerelde geçti; sentetik 30 oyun benchmark medyanı 312,44→106,44 ms. Gerçek Steam hesabı test edilmedi. docs/STEAM_BOUNDED_SYNC_TR.md ayrıntıları içerir. PR/CI sonuçlarını GitHub'dan yeniden sorgula; main merge/yeni release yok.

## Devam görevi — Steam metadata cache (yayımlanmamış)

Kullanıcı “devam et” dedi. PR #15'in son a7065a4 kaynağı Unit/Windows 42072993663/42072993224 başarılıydı. Yeni dal `feature/steam-schema-cache`, #15 üzerine; yeni release/main merge yok. Steam public schema metadata'sı 6 saat yerel ayrı dosyada; earned/oyuncu listesi her seferinde canlı sorgu sınırından geçer. Force/TTL/bozuk dosya/yeni kimlik invalidation testleri eklendi. 100 oyunlu mock bütçe 201→101 çağrı; canlı hesap hızı ölçülmedi. Ayrıntı docs/STEAM_SCHEMA_CACHE_TR.md. Yeni PR/CI sonuçlarını GitHub'dan yeniden kontrol et.

## En güncel görev — Issue #10 (yayımlanmamış)

Kullanıcının son master order talimatı: **main'i değiştirme, yeni Development Release yayımlama**. Önceki 0.15.1 yayın yetkisi bu yeni göreve otomatik taşınmaz.

A #11, B #12, C #13, D #14 ayrı ve üst üste kurulu PR'lar. Son çalışma dalı `feature/issue10-controller-performance`; E PR #15. Hiçbiri main/codex'e otomatik merge edilmedi. A Unit/Windows 42066272591/42066272796, B 42066432637/42066432834 başarılı. C/D eski PC planned-state desktop smoke beklentisi düzeltildi. D Unit/Windows 42071862650/42071862634 başarılı; C/E son Actions durumunu yeniden sorgula.

Uygulandı: native `#/game/{id}` Universe, 7 sekme/back/focus/inline, beş gerçek artwork türü/health/kalıcı edition-onayı, PSN title-atomik partial koruma/gruplar, resmi Steam Web API PC registry, DPAPI key, sade nav/4 seçenekli onboarding/Ctrl+K, ortak UI olayları, Gamepad A/B/X/Y/LB/RB, revision/scope/progress cache ve native Playwright testleri. **Gerçek hesap/NPSSO/Steam key yok; canlı test iddiası yok.** Fiziksel gamepad/güç kesintisi/logon testi yok. Üretici logo izni yok; Atlas markası + metin etiketleri.

Yerel son tur: 160 Python, dört Node suite, dört resolution Universe/search, 16 skin/resolution/high-contrast, 5k/15k/40k ve Gamepad API simülasyonu geçti. E Windows build sonucu ilk committe beklenir. Kaynak/sınırlar: [Issue #10 audit](docs/ISSUE_10_DELIVERY_AUDIT_TR.md). Test kanıtları `work/audit/` (gitignore) ve GitHub native-browser artifact'ı. Büyük JSON payload ve Steam sıralı ağ/kalıcı schema cache kalan performans borçlarıdır.

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
2. **codex/public-profile-trophies**: v0.15.1 Development Release tabanı; taslak PR #1, main dalına karşı.
3. **feature/atlas-ultimate-v5-live-ui**: önceki taslak PR #2; güncel v5.1 zaten geliştirme dalında, eski dosyaları üzerine kopyalama.
4. **feature/unified-native-themes**: PR #4; dört temayı tek native shell'e indirir, ayrı Console Mode ve Timeline.
5. **feature/v015-foundation-onboarding-recovery**: PR #4 dalından türemiş v0.15 Foundation başlangıcı; beş ana menü, ilk açılış rehberi, kaynak durum şeridi, ayrıntılı update blockers ve iptal.

**Birleştirme sırası:** Önce PR #4 inceleme ve testlerden sonra codex/public-profile-trophies'a; ardından Foundation PR'ı yeniden tabanlanarak aynı dala. main veya Release için otomatik merge/publish yapma.

## Yayın ve güven

Son yayımlanan sürüm: **Achievement Atlas v0.15.1 Development**
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


## 4 Kasım 2026 — Entegrasyon ve v0.15 Preview (SON DURUM)

Bu önceki PR sıralama talimatının **güncel sonucu**dur:
1. PR #4 (`feature/unified-native-themes`) `integration/atlas-v015` dalına **merge edildi**: `6d3f49a08b13b54261e128cb6d75fbbe8e4bdd3b`.
2. PR #5 (`feature/v015-foundation-onboarding-recovery`) aynı entegrasyon dalına **merge edildi**: `c493b3787afd7be7778c82787c3735f1fcfbc78d`.
3. `integration/atlas-v015` üzerinde gerçek `0.15.0` **Preview** sürüm ismi, Inno Setup installer ismi, HTML sürüm etiketi ve Windows Actions artifact isimleri güncellendi.
4. `windows-package.yml` Development kanalının **otomatik** yayınını kaldırdı; yalnız `workflow_dispatch` + `publish_development=true` + `codex/public-profile-trophies` koşullarıyla açık manuel yayın mümkün. Bu kod birleşmeden mevcut codex dalındaki eski workflow hâlâ auto-publish yapabilir; codex'e doğrudan push/merge yalnız yayın etkisi değerlendirilerek yapılmalı.
5. Final gözden geçirme PR #6: `integration/atlas-v015` → `codex/public-profile-trophies` **DRAFT**. Son installer ve unit/JS koşularının başarılı olduğundan emin ol. **PR #6'yı otomatik merge etme**; `main` ve `development` Release'i koru.

Yeni oturumda şunları denetle: PR #6 head commit ve son Windows artifact; Python+JS sonuçları; gerçek Windows 0.14.1→0.15.0 preview upgrade/rollback testi; gerçek Xbox/PSN kimlik ve fiziksel gamepad testleri. Paket verileri kişisel arşivden görür, uydurma kupa veya AI yapımı oyun artı yoktur.

**Not:** Başarılı CI gerçek kullanıcı Windows kurulumunda veri göçü/rollback, gerçek hesap bağlantısı ve fiziksel kontrolcü kanıtı değildir. Windows preview installer'ını otomatik güncelleme kanalıyla aynı sayma.


## 4 Kasım 2026 — PR #6 ANA GELIŞTIRME DALINDA BİRLEŞTİRİLDİ (güncel kayıt)

Kullanıcı isteğiyle entegrasyon dalındaki son v0.15.0 Preview, final CI/Windows preview build başarılı olduktan sonra **PR #6 üzerinden `codex/public-profile-trophies` dalına birleştirildi**. Merge commit: `b1c77545a47e8a354e0c263e97a7bcb9197e1549`. PR #4 ve #5 önce `integration/atlas-v015` içine zaten alınmıştı; yeni commit onların değişikliklerini de içerir.

- Versiyon: `0.15.0` **Preview**; yayımlanan `development` Release ile aynı şey değildir.
- `main` değiştirilmedi. Geliştirme kanalına otomatik yayın artık `windows-package.yml` içinde `workflow_dispatch` + `publish_development=true` + doğru kod dalı koşullarına bağlıdır. Birleştirme otomatik Release üretmez.
- Birleştirmeden önce `integration/atlas-v015` başlığındaki Windows installer build başarılıydı: https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/41725872621
- Birleştirme sonrası **codex branch** GitHub Actions installer/job/attestation/artifact ve `publish-development` skip durumlarını ayrıca canlı denetle. Tam Windows 0.14.1→0.15.0 canlı yükseltme/başarısız rollback, gerçek Xbox/PSN erişimi ve fiziksel gamepad testi hâlâ eksik.
- Kaynaklar: `docs/V015_FOUNDATION_PLAN_TR.md`, `docs/V015_ARCHIVE_RECOVERY_TR.md`, `docs/V015_IDENTITY_STORAGE_MOTION_TR.md`. Sadece gerçek oyun artwork'ü kullanılmalı, kişisel CSV/token repoya girmez.

**Bu paragraf önceki 'PR #6'yı merge etme' bekleme notunun daha güncel sonucudur.** Sonraki oturumlar commit/Actions/Release durumlarını yeniden sorgulamalıdır.


## 5 Kasım 2026 — Canlı doğrulanmış yayın ve devam işi

Bu bölüm önceki Preview/yayın bekleme notlarının güncel sonucudur. Kullanıcının açık isteğiyle PR #7 geliştirme dalına birleştirildi; commit `3346909d71b2459a845e003a5e09f77285b03979`. 0.15.0 Development Setup yayımlandı; `development-manifest.json` sürümü 0.15.0, run ID `41729972033`. EXE SHA256: `e016ac7532a77c690a1a6a5e0f4afb0cc24a4c0b4064a54ccf4a31a0205ced09`. GitHub Actions Windows ve unit koşuları başarılı. Yayınlanan dosya indirilerek Sigstore köken kanıtıyla doğrulandı. Windows Authenticode imzası yok; main değişmedi.

Yayın akışı: Normal push yalnız aday derler ve push provenance oluşturur. Manuel `promote_run_id` başarılı özgün push artifact'ını doğrulayarak yayımlar. Ayrıca geliştirme dalında commit mesajında `[publish-development]` varsa başarılı build ardından açık yayın yapılır. **Bu işareti rutin geliştirme commitlerine koyma.** Ayrıntı: `docs/UPDATE_DELIVERY_FIX_TR.md`.

Devam dalı: `fix/update-rollback-snapshot`. Kurulum hatasında yeni sürümün orphan dosyalarını temizleyen, yedeği ve geri alınmış dosya kümesini SHA256 ile doğrulayan düzeltme. `docs/UPDATE_ROLLBACK_SNAPSHOT_TR.md` test kapsamını ve güç kesintisi sınırlarını açıklar. Bu değişiklik henüz yayımlanmış 0.15 Setup'a dahil değildir. Canlı hesap/gerçek kullanıcı bilgisayarı/fiziksel gamepad testi yapılmış sayılmaz.


### Devam — Windows yükseltme matrisi

PR #8 / `fix/update-rollback-snapshot` üzerinde gerçek 0.13.0/0.14.1 yayımlanmış installer → yeni Setup yükseltmesi, snapshot ile bilinçli dosya geri alma, eski/new native uygulamada kayıt/kimlik/not/pin ve uninstall sonrası dış veri koruma testi eklendi. `tests/test_windows_upgrade.ps1`, Windows installer workflow'unda çalışır; `upgrade-test-report.json` artifact'ı sonucu belgeler. Son CI sonucunu canlı kontrol et; testin eklenmiş olması geçtiği anlamına gelmez. Güncelleme düğmesi üzerinden tam self-update ve güç kesintisi hâlâ ayrı test kapsamıdır.

### Devam — native güncelleme düğmeleri ve data-dir

PR #8'de native WebView2 düğmelerinden yayımlanmış 0.14.1→güncel geliştirme sürümü self-update testi eklendi. Tam ağ/köken kanıtı/helper/installer/yeniden açılış zinciri, ayrı GitHub Windows runner üzerinde başta bulunmadığı doğrulanan varsayılan veri klasöründe çalışır. LOCALAPPDATA değiştirilmez; WebView2 runtime keşfi korunur. Son CI sonucu görülmeden geçti deme. Ayrıca yeniden başlatmada özel `--data-dir` kaybı düzeltildi (install plan + helper'ın başarılı/geri alma başlatmaları). Eski dağıtılmış helper'ın davranışı geriye dönük değişmez. Kalıcı update power-loss journal hâlâ sonraki iştir.

## Devam — kalıcı update kurtarma dalı

PR #8'in son doğrulanan commit'i `7adcc8a3eada6581f4840d1209fd0a7accd6b3f9`: 144 Python testi, 9 helper senaryosu, gerçek 0.13.0/0.14.1→aday kurulum matrisi ve yayımlanmış 0.14.1→0.15.0 gerçek native düğme/köken/helper/yeniden açılış zinciri geçti. Windows koşusu: https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/42017115300 . PR #8 henüz merge/release edilmedi.

Yeni `feature/update-crash-recovery` dalı PR #8 üzerine bağımlıdır. Kalıcı recovery-state.json + kullanıcı kapsamlı tek seferlik Windows RunOnce denemesi, yeni süreçte kurtarma ve uninstall sırasında kurtarma görevinin iptali eklenir. Ayrıntı/sınırlar: `docs/UPDATE_CRASH_RECOVERY_TR.md`. Son CI görülmeden Windows/güç kesintisi doğrulandı deme. Fiziksel güç kesintisi ve gerçek logon testi bu CI süreci öldürme testlerinden farklıdır. main ve mevcut Development Release korunur.


## 5 Kasım 2026 — 0.15.1 YAYIMLANDI (en güncel kayıt)

Kullanıcı açıkça güncelleme olarak yayın istedi. PR #9 önce PR #8 dalına, ardından sürümlenmiş/test edilmiş PR #8 `codex/public-profile-trophies` dalına birleştirildi. Yayın kodu commit'i: `8b904e2f297ffae4d131799abeeb604c457c5100`. Main değişmedi (`98f870b908fa73ec2711c2f3fd359eca92a7ab77`). Önceki 'henüz merge/release edilmedi' kayıtları tarihseldir.

- Development manifest: **0.15.1**, run `42052975199`, GitHub push provenance, Authenticode imzası **yok**.
- Gerçek yayımlanmış Setup: `AchievementAtlas-0.15.1-Windows-x64-Setup.exe`, 33,285,398 byte; SHA256 `dba8a8c385ee261ac59970b7ac9e6d3fb10da426af39a6d6641e2b0cecbec3e4`.
- Setup, manifest ve köken kanıtı gerçek indirme bağlantısından indirilip tekrar kriptografik doğrulandı.
- Başarılı yayın Windows koşusu: https://github.com/Gh0sTRX/achievment-thropy-tracker/actions/runs/42052975199 ; unit koşusu `42052975153` başarılı. 146 Python testi; 9 rollback ve 8 yeni süreç kesintisi senaryosu Windows/Linux ve PowerShell 5.1/pwsh üzerinde geçti. Gerçek 0.13.0/0.14.1/0.15.0 → 0.15.1 yükseltme, kayıt/not/pin, geri alma ve uninstall kontrolleri geçti.
- Yayın SONRASI gerçek stok **0.15.0 → 0.15.1** native UIA menü/kontrol et/indir/kur/yeniden açılış akışı başarılı. PR8 Windows koşusu `42051960172` yeniden çalıştırıldı; native job `127339880613`; rapor artifact `13429325710`. Düğmeler gerçek native pencerede çalıştı, network/Sigstore/helper/installer ve kayıt koruması doğrulandı.
- Fiziksel güç kesintisi ve gerçek yeniden logon hâlâ doğrulanmış değildir. Yeni kalıcı kurtarma, 0.15.1 kurulduktan sonra yapılan sonraki güncellemelerde kullanılır; ilk geçişi eski yardımcı yürütür. Gerçek Xbox/PSN hesap ve fiziksel gamepad testleri de ayrı eksiklerdir.
- Yayın kaynakları: docs/RELEASE_NOTES_0_15_1_TR.md, docs/UPDATE_CRASH_RECOVERY_TR.md, KURULUM.txt. Yeni görevde manifest/branch/Actions durumlarını tekrar canlı oku. Rutin committe `[publish-development]` kullanma; yayın kullanıcı tarafından açıkça istenmelidir.
