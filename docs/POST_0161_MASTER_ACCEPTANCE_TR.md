# v0.16.1 sonrası ana emir — kaynak kabul raporu

## 1. Kaynak ve entegrasyon

Başlangıç HEAD: `955f2361fbf9e06adea3cc0486154924557a20dc`.
Dal: `fix/37-confirmed-xbox-artwork-candidates`. Açık PR yok. #23–#26,
#38–#39, #41–#43 kaynakları git ancestry ile kontrol edildi: 405664e,
8ff03c6, 9512d14, f562759, 1b78d07, da489e4, dc577aa, 3e008c4, d365609,
e45b452, f3d2a0d, 54a76b1, 955f236 korunuyor. Yeniden cherry-pick veya
PR açma yok. Main, codex geliştirme tabanı ve yayımlı kanal değişmedi.

## 2. Windows kapısı

955f236 Unit tests `42237214666` başarılı. Bu native installer kanıtı değildir.
PR'lar kapatılınca Windows workflow yalnız main/codex push'larında çalışıyordu;
aktif kaynak dalı push filtresine eklendi. Native WebView2, frozen uygulama,
DPAPI, installer, upgrade/rollback ve mevcut self-update testleri korunur.
Publish/promote/attestation koşulları değiştirilmedi: bu dal otomatik yayın
yapamaz. Yeni kaynak için Windows CI sonucu tamamlanmadan hazır denmez.
Derlemede SDK kurulu olması gerçek hesap kabulü değildir; self-update testi
önceden yayımlanan paketleri sınayabilir, yeni paketin yayımlandığı anlamına gelmez.

## 3. Artwork kök nedenleri ve son düzeltme

Önceki düzeltmeler: CSV'nin kimlik/URL içermemesi açık gösteriliyor; oyun ve
edisyon onayı gerekiyor. Onaylı TitleHub kategorileri aktarılıyor; kayıp cache
aynı edisyonun saklı kaynak adresinden yeniden kurulabiliyor. Yerel kullanıcı
dosyaları öncelikli. Dört ekran boyutunda kapak/kompakt fallback kontrolü var.

Bu tur doğrulanan tutarsızlık: Health, farklı edisyona ait saklı URL'yi veya
yerel kullanıcı dosyasının alternatif adayını kullanılabilir kaynak sayabiliyordu;
indirici bunları reddediyordu. Ayrıca Health eski uygulamaları sayarken indirici
saymıyordu. `media_sync.game_sources` her iki akışta aynı kaynak kurallarını
kullanır; Health de retained uygulamaları oyun kapsamına katmaz. Kayıt silinmez.

Cover/hero/banner/logo/screenshot ve ikonlar ayrı; cached/missing_source/failed/
blocked ayrı. HTTP kodları ayrıntıda korunur; 403/429 engel, 404 başarısız.
Tek oyun artwork seçme/yeniden deneme akışı mevcut. Sağlayıcıda olmayan görsel
üretilmez. Gerçek Minecraft/Cold War/Asphalt art kapsaması ölçülmedi; mock PNG
kapsama kanıtı değildir. SteamGridDB API erişimi ve edisyon onayı hâlâ gerekir.

## 4. Xbox araştırması

`authenticated_client` her kullanımda diskteki OAuth'u okuyup SDK
`refresh_tokens` çağırıyor ve XUID'yi denetliyor; token yenilenmeden oturum
doğrulanmış sayılmaz. SDK oturumu context kapanışında kapanıyor, kalıcı HTTP
istemcisi tutulmuyor. Ağ hatası→aynı Controller ile tekrar sync testi arşiv/not/
pin korunmasını doğruluyor. Opsiyonel media/guide başlatma hataları başarılı
profil sonucunu bozmuyor. Profil guard'ı activity kaydı hata verse de bırakılıyor.

Gerçek offline→online hatasının sanitised hata kodu ve yetkili oturum izi yok;
kesin kök neden bulunmuş sayılmaz. Eşzamanlı OAuth yenileme/ortak SDK token
dosyası, dış süreç erişimi ve gerçek XSTS süresi ayrıca canlı test gerektirir.
Gizli oturum verileri istenmedi veya rapora alınmadı.

## 5. PSN / Steam

PSN ilk tarama: title iterator, sonra oyun başına groups ve earned trophies
sayfalaması seri çalışır. İlk tam tarama bu nedenle daha çok istek gerektirir;
gerçek süre ölçülmedi. İptal/progress title discovery'ye de eklendi. Rate-limit
hatası bypass edilmez, güvenilmez paralellik yok; devam eden SDK isteği bitene
kadar iptal gecikebilir. On dakikalık conservative signature cache ve force
seçeneği var. Gerçek NPSSO/hesap kabulü yapılmadı.

Steam: resmî Web API, SteamID64/vanity, public/private/key/429 kontrolleri,
AppID ayrımı, kullanıcı kazanımları ile altı saatlik schema cache ayrımı mevcut.
Kısmi sonuç ve farklı hesap korumaları mock testli. Gerçek anahtar/hesap testi
yapılmadı. PSN ve Steam puanları Xbox Gamerscore'a dönüştürülmez.

## 6. Console / Game Universe

Tek shell, gerçek kapak, okunaklı metin ve akıştaki kontroller korunur.
54a76b1 test izolasyonu: kapaklı/kapaksız oyun açıkça seçilir; önceki testin
kalıcı platform/oyun tercihi sonucu değiştirmez. Tam satır tıklama, bağımsız
pin, spoiler, ortak ikon/tarih/kaynak ve native history/scroll/focus testleri
korunur. Fiziksel gamepad, televizyon mesafesi ve NVDA kabulü yapılmadı.

## 7. Veri güvenliği

PC içeren karma archive, ham JSON indirme/restore, hash ve recovery backup
testleri var. Eski arşiv migrasyonu yok. İçe aktarım/yeniden sync not/pin/
kimlik/tarih/yerel görsel korumaları testli. Bu tur kullanıcı arşivi açılmadı.
JSON backup medya dosyalarını taşımaz; tam portable media backup ayrı eksik.
Eski hatalı şekilde yeniden serileştirilmiş yedeğin hash'i tahminle onarılmaz.

## 8. Next Move

En fazla üç oyun, pin/eldeki tamamlanma/son 30 gün kazanımı; belirsiz ve gelecek
tarih yok. Kaynak ve kapsam/erişilebilirlik belirsizliği açık. Ratio/GS/süre
skoru, LLM veya ücretli çağrı yok. Mutasyonsuz offline test ve platform/kart
Chromium kontrolü var. 30 saniyede hedef bulma gerçek kullanıcıyla ölçülmedi.

## 9. Test matrisi ve yayın kararı

Yerel Python: **228/228**, dört Node suite ve gerekli JS syntax kontrolleri
başarılı. Yeni iki Health testi farklı edisyon/user-file kaynak reddi ve retained
app sayım tutarlılığını doğrular. Tam Chromium CI ve Windows sonuçları yeni
push SHA üzerinden izlenmeli; eski yeşil kaynak yeni HEAD kanıtı değildir.
Windows sonucu başarısız/beklemedeyse geliştirme paketi hazır denmez.

Yayın yetkisi yok. Testler yeşil olsa bile imzasız Development adayını stable
veya güvenilir Windows yayıncı imzası gibi sunma. Main/dev merge/release yok.

## 10. Yayından önce gerçek kabul

Arşiv kopyasında: Cold War/Asphalt/Minecraft edisyonu ve gerçek kapak yüklemesi;
Xbox offline→online→offline ve hata sonrası uygulama kapanmadan yeniden deneme;
PSN oyun sayısı/süre/iptal; Steam public/private ve kazanımlar; yedek/restore;
klavye/gerçek gamepad/NVDA; not/pin/media hash korunması. Kimlik ve secret
paylaşmadan güvenli özet alınmalı. Offline/online göstergesi backlog'da kalır.

Ürün değeri hipotezi: sağlayıcı kapalıyken arşivine erişmek, edisyonları
karıştırmadan eksikleri bulmak, kaynaklı hedef seçmek. Bu rapor tek başına
oyuncunun Atlas'ı tercih ettiğini veya ürünün tamamlandığını kanıtlamaz.
