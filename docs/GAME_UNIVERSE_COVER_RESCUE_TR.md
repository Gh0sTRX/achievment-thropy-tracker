# Game Universe · tüm kütüphane kapak kurtarma

## Kapsam

Bu çalışma **Minecraft / Cold War / Asphalt'a özel değildir**. Xbox, PlayStation,
Steam ve yerel CSV üzerinden tutulmuş **tüm oyun/sürüm kayıtlarını** Game Universe
için ele alır. Kütüphanenin çok büyük olması nedeniyle eksikler 20 kayıtlık
sayfalarda gösterilir. Uygulama/servis kayıtları (Netflix gibi) oyun kapsamına
girmez; kullanıcı arşivinden silinmez.

## Uygulamada

**Oyun Görselleri → Game Universe · Tüm oyun kapaklarını tamamla**:
1. **Tüm kapakları tara:** Her oyunun yerelde açılabilen gerçek `cover`
   dosyasını say; eksik oyunları sıralı ve sayfalı göster. Sırf kaynak URL'si
   bulunması bir görselin indirildiği anlamına gelmez.
2. **Tüm eksik kapakları bul ve tamamla:** Önce kaynak metadata keşfi, sonra
   güvenli HTTPS kapak indirmesi yapar. Mevcut kapakları,
   kullanıcı dosyalarını, hero/logo/banner ve başarım ikonlarını değiştirme.
   İşlem arka plandadır; sonra tekrar tara. 401/403/429 engelleri aşılmaz.
3. **Eşleştir / kapak seç:** Kaynaksız oyun için aynı yerel oyun kaydını
   görsel çalışma alanına yükle. SteamGridDB API anahtarı varsa oyunu ara,
   çıkan isimlerin *gerçek oyun/edisyon* olduğunu elle kontrol edip onayla,
   galeriden kapağı seç. Ya da kendi dosyanı seç. SteamGridDB araması otomatik
   yanlış isim/edisyon eşleşmesi yapmaz.
4. Game Universe içindeki Görseller sekmesinden **Tüm Game Universe
   kapaklarını yönet** düğmesi aynı envantere götürür.

## Gizlilik, güven ve garanti sınırı

- Veri kaynağı olmayan, adı benzer ama edisyonu farklı kayıt için resim uydurulmaz.
- Kullanıcının yerel kapak seçimi, önceki pin/notlar/kazanımlar korunur.
- Gerçek kapak kaynağı/API anahtarı olmayan kayıtlar toplu indirmeyle otomatik
  tamamlanamaz; gerekçeleri ve eşleştirme yolu görünürdür.
- Kullanıcının özel Windows veri klasörü ve gerçek hesapları bu geliştirme
  sırasında okunmadı. Kütüphanedeki **gerçek kapsama yüzdesi henüz ölçülmedi**.
- Görseller açık kaynak depoya paketlenmez veya yeniden dağıtılmaz.
- Bu branch Development Release değildir. Release/main değişikliği için ayrı
  kullanıcı onayı ve fiziksel cihazda kabul gerekir.

## Testler

`tests/test_game_universe_cover_queue.py`:
- 27 oyun ve üç sağlayıcıyla (Xbox/PSN/Steam) 20+6 sayfalama,
- cover-only indirmede diğer görsellerin ve ikonların korunması,
- Title ID uyuşmazlığı ve kullanıcı görselinin ezilmemesi.

`tests/test_cover_inventory_ui.cjs`:
- 20+6 eksik oyun sayfalama, genel toplam, seçili oyunun cover
  çalışma alanına yönlendirilmesi ve yalnız kapak indirme isteği.

Bu testler gerçek servis kapaklarını doğrulamaz; gerçek Game Universe arşivinde
tarama ve güvenli eşleştirme hâlâ Windows kabul adımıdır.


## PR #44 · kimlikle kaynak keşfi

`atlas/cover_recovery.py`, mevcut `covers_only` indirmesine isteğe bağlı
`discover_sources: true` adımını ekler. Sadece kapak düğmesi bunu açar;
başarım eşitlemesini veya ücretli rehber çağrılarını başlatmaz.

- Xbox: OpenXbox TitleHub `get_title_info(Title ID)`, işlem başına tek yetkili
  oturum. Yanıttaki Title ID **ve cihaz kümesi** aynı olmalı; cihaz/edisyonu
  bilinmeyen eski CSV kaydına sessizce başka kimlik atanmaz.
- PSN: Mevcut doğrulanmış profilin NP Communication ID + cihaz kümesi,
  işlem başına tek `trophy_titles` kataloğu. NPSSO veya doğrulanmış profil yoksa
  neden gösterilir. Başarım/kupa sorgusu ve yetkisiz veri çekme yapılmaz.
- Steam: `provider=steam`, `platform=pc`, `edition=steam`, geçerli ve çelişmeyen
  AppID üzerinden resmî CDN kapak adayı. URL varlığı başarı sayılmaz; gerçekten
  indirilen dosya decode edilmeli.
- SteamGridDB: Mevcut bellekteki kişisel anahtarla aday araması. İsim yalnız aday
  üretir. Önceden onaylanmış oyun/platform/edisyon/cihaz eşleştirmesi aynıysa
  kaynak otomatik kullanılabilir; diğerleri **Onay bekleyen eşleşmeler** kuyruğuna
  gider. “Eşleştir / kapak seç” adayları mevcut onay kutusuna taşır ve kutuyu
  işaretlemez. Kimlikler platformlar arasında dönüştürülmez.
- Yerel dosya ve decode edilmiş geçerli cache önceliklidir. Kayıtlı güvenli
  kaynaklar, resmî keşif ve son olarak onaylı topluluk kaynakları izlenir.
- Keşif kimliği, gerekçesi ve adayları yerelde tutulur. Olumsuz sonuçlar 6 saat,
  hatalar 5 dakika tekrar sorgulanmaz; kimlik, profil veya servis erişim durumu
  değişirse yeniden değerlendirilir. Anahtar diske yazılmaz. Aynı isim/kimlik
  aynı işlemde tekrar sorgulanmaz; 401/403/429 veren sağlayıcı zorlanmaz.
- İptal mevcut isteğin bitmesini bekler; sonraki sorguyu engeller ve tamamlanmış
  kaynakları/görselleri korur. Her 25 kayıt veya 5 saniyede ara kayıt yapılır.
- Profil, edisyon, cihaz, nesne veya kullanıcı görseli istek sırasında değişirse
  sonuç uygulanmaz. Aynı profil eşitlemesi, doğrulanmış keşif ve görsel
  eşleştirmelerini korur; diğer hesapların verilerine taşınmaz.

## Görünmeyen kart kapağının kök nedeni

`visuals.js/cssUrl`, zaten kodlanmış `localArt` adresini `encodeURI` ile ikinci
kez kodluyordu. `fixture%3A0` → `fixture%253A0` biçimindeki adres kartta yanlış
cache kimliği sorgulatırken, detay/Console `img` adresi doğru kalabiliyordu.
Geçerli yüzde kaçışları korunuyor. Yeni Chromium testi CSS'in kullandığı gerçek
adresi HTTP ile açıp 200 yanıtını ve üç ekrandaki ortak kaydı doğrular.

## Geniş sentetik doğrulama ve kanıtlar

`tests/test_cover_recovery.py`: Xbox 360/One/Series, PS3/Vita/4/5, Steam ve
kimliği olmayan CSV içeren 20/100/500/1000 oyun. Bu karma testte Xbox/PSN
oturumları **bilerek kapalıdır**; yalnız Steam mock görüntüleri indirilebilir.
Ayrı Xbox ve PSN testleri SDK biçimindeki mock metadata ile kesin kimlik/edisyon
kabulünü ve yanlış eşleşme reddini doğrular.

Ölçülen örnek (yerel Linux, `tracemalloc` açık, paralel Chromium yükü mevcut;
ağ yanıtları sentetik, süreler gerçek servis performansı değildir):

| Oyun | Yeni/geçerli kapak | Kaynaksız | Toplam süre | İzlenen tepe Python belleği |
|---:|---:|---:|---:|---:|
| 20 | 2 | 18 | 0,072 s | 0,37 MiB |
| 100 | 11 | 89 | 0,337 s | 1,76 MiB |
| 500 | 55 | 445 | 2,604 s | 8,49 MiB |
| 1000 | 111 | 889 | 7,701 s | 18,52 MiB |

Bu süre keşif, mock indirme/decode, diske yazma, tekrar tarama ve envanteri
kapsar. Python bellek izlemesi native Pillow/işletim sistemi belleğini kapsamaz.
Kaynak eksikliği bu testte kasıtlı oturum yokluğudur; gerçek oyuncu kapsaması değildir.

`tests/test_cover_recovery_ui.cjs`: Gerçek localhost API üzerinden 20 oyun;
önce **0**, sonra **7** decode edilmiş kapak, **13** onay bekleyen aday, **0**
yanlış otomatik isim eşleşmesi. Haricî HTTPS tarayıcıda kapalıdır; dosyalar
uygulamanın kendi Atlas markasıdır, gerçek oyun kapağı olarak sunulmaz.
Kütüphane kartı, Game Universe ve Console aynı yerel kapak URL'sini açar;
yeniden yüklemede ve dış servisler kapalıyken cache korunur.

CI `native-browser-audit` artifact'ı:
- `native-cover-before.png`, `native-cover-after.png`: kütüphane.
- `native-cover-universe-before.png`, `native-cover-universe-after.png`: Game Universe.
- Tüm ekran görüntülerinde **sentetik arşiv / test görseli** etiketi bulunur.
- `cover-recovery-synthetic.json`: 20/100/500/1000 ölçümleri.
- `cover-ui-results.json`: gerçek localhost + mock sağlayıcı test sonuçları.

Python tam regresyonu, Node kontrolleri ve 16 Chromium betiği çalıştırılır.
Windows native/installer/rollback kanıtı **yalnız güncel PR HEAD CI yeşil olduğunda**
geçerlidir; önceki HEAD başarısı bu değişikliğin başarısı sayılmaz.

## Gerçek kabul ve yayın sınırı

Gerçek kullanıcı arşivi ve canlı Xbox/PSN/Steam/SteamGridDB servis oturumları bu
çalışmada kullanılmadı. %100 gerçek kapak kapsaması, fiziksel gamepad kabulü veya
sertifikalı Windows imzası iddia edilmez. Authenticode sertifikası hâlâ ayrı iştir.
PR #44 son HEAD Unit/Chromium/Windows kontrolleri ve kullanıcının gerçek Windows
kabulü ile yayın onayı beklenir. `main` birleştirme ve Development yayını yapılmaz.


## Devam: ikinci tıklama gerektirmeyen kurtarma

Önceki akışta kaynak keşfi indirmeden önce yapılıyordu. Yeni bulunan resmî URL
404/bozuk görüntü döndürürse ek kaynak araması ancak sonraki kullanıcı denemesinde
başlayabiliyordu. `cover_recovery.recover` artık tek düğmeyle sınırlı bir akış yürütür:

1. Kayıtlı kaynakları ve yerel cache'i değerlendirir.
2. Eksikler için kimlikle metadata keşfi yapar; doğrulanmış yeni kaynakları indirir.
3. Yeni kaynak da başarısızsa **en fazla bir ek keşif** yapar. Onaylı ek kaynak
   varsa indirir; isimden bulunan belirsiz adayı onay kuyruğuna koyar.

Sonsuz tekrar yok: en fazla 3 indirme / 2 keşif aşaması. Her aşama, önceki aşamanın
cache'ini kullanır; tamamlanmış kapak yeniden indirilmez. Resmî metadata, SGDB
adayları ve onaylı seçimler aynı işlem içinde paylaşılır. Xbox fallback testinde
TitleHub isteği ve yetkili oturum **birer kez** çalışır. Süresi dolan oturum veya
servis hatasını atlatmak için başka uç noktaya geçilmez.

- HTTP 403 host engeli bütün aşamalarda korunur. 401/429 indirme engelinde
  sonraki keşif/indirme aşaması başlamaz. Tükenmiş görüntü URL'leri aynı işte
  tekrar denenmez; normal transient retry sınırı değişmedi.
- İptal ve profil/kütüphane değişiminde sonraki aşama başlamaz. Tamamlanmış
  görseller korunur; yeni profilin arşivi eski işin raporuna katılmaz.
- Nihai `downloaded/cached/failed/...` sayıları **oyun kapağı başına** hesaplanır.
  Ara denemeler `passes` ve `asset_attempts` altında tutulur; indirme sayısı gibi
  sunulmaz. Ara hata giderildiyse nihai hata sayısında kalmaz.
- Yerel disk yazma hatası, URL'nin bozuk olduğu varsayımıyla ortak kaynak
  engeline dönüştürülmez. Genel medya indirmesi için yeni bir kurtarma döngüsü
  açılmaz; bu akış yalnız `covers_only + discover_sources` içindir.

Geniş 20/100/500/1000 testi artık bu gerçek orkestrasyon üzerinden çalışır;
yukarıdaki tablo bu akışın yerel, mock ağ yanıtlı ölçümüdür. Chromium fixture'ında
20 oyundan 7'si indirilir, 13'ü onay bekler. Bir bozuk kayıtlı URL ve bir yeni
resmî 404 aynı tıklamada kurtarılır. **7 tekil kapak / 9 varlık denemesi** açıkça
ayrılır; resmî 404'ten sonra yalnız önceden onaylı SGDB eşleşmesi otomatik kullanılır.
Gerçek oyuncu arşivi veya canlı servis kabulü değildir.
