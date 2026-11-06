# v0.16.3 adayı — Artwork Rescue ve Console Mode kabulü

7 Kasım 2026. Geliştirme: `codex/public-profile-trophies`. Başlangıç `fd707ff`,
yayımlı 0.16.2 binary kaynağı `ee13cd7`. Bu çalışma yayın yetkisi içermez.
Main, development release manifesti ve yayımlı 0.16.2 değiştirilmez.

## Gerçek kullanıcı başlangıç kabulü

Kullanıcının v0.16.2 test sonucu: Xbox reconnect/sync GEÇTİ; PSN/Steam GEÇTİ;
oyun kapakları SORUNLU; Console Mode KISMEN GEÇTİ. Bu, tüm API uçları,
rate-limit/gizlilik senaryoları veya fiziksel kontrolcünün tamamı doğrulandı
demek değildir. Önceki raporlardaki “gerçek hesap henüz denenmedi” ifadesi bu
yeni kullanıcı gözlemiyle sınırlandırılır; otomatik test hâlâ sentetiktir.

## Artwork — kök neden ve değişiklikler

- Aynı yerel oyun ID'si ve aynı edisyonda Title ID değişirse saklı source_url
  yeniden kullanılabiliyordu; test eski adrese fetch yapıldığını gösterdi.
  Recovery artık Title ID'yi de doğrular; yeni provenance bu alanı taşır.
- Farklı Title ID'ye bağlı geçerli cache baytları da doğru görsel sayılmaz.
  Health ve renderer bilinen kimlik çakışmasını reddeder; dosya silinmez.
  Kullanıcının açık yerel dosya tercihi korunur. Kimliksiz eski dosya metadata'sı
  doğrulanmış oyun eşleşmesi diye raporlanmaz; eski dosyalar topluca silinmez.
- Reset sırasında eski Title ID'nin original_url'sinin dönmesi red testle
  doğrulandı; aynı edisyon adı yeterli sayılmaz, eski URL geri getirilmez.
- Health daha önce ağırlıkla son indirme durumunu gösteriyordu. Şimdi altı tür
  ayrı: cover, hero, banner, logo, screenshot, achievement icon. Cached dosya,
  kayıp cache, bozuk dosya, local_file_missing, kimlik çakışması, missing_source,
  401/403/404/429 ve mevcut fakat indirilmemiş kaynak için neden/eylem vardır.
- Yalnız ikon eksiği olan oyun da listelenir. İkon cached/missing/source/error/
  blocked sayıları ve HTTP kodları ayrıdır. Eski 403, geçerli cache'i engelli
  gibi göstermez. URL sayısı indirme sayısı olarak sunulmaz.
- Seçili oyun kontrolü, aynı oyun için yeniden indirme ve görsel seçimine dönüş
  vardır. Liste 20 satır gösterir; daha fazlası varsa seçili oyun kontrolüyle
  hedeflenebilir. Bu akış isimden otomatik edisyon/Title ID üretmez.

## Console Mode — mevcut shell içinde

Simüle gamepad red testi oyundan geri gelince konsolun/oyun seçiminin dönmediğini
gösterdi. Console kökenli Game Universe rotasından geri dönüşte mevcut native
router önce sayfa/scroll'u onarır; ardından konsol aynı oyunla açılır, seçili
kart odaklanır. Rail yeniden çizilirken odak aynı seçili karta taşınır. Kartlar,
metinler ve kontrol kılavuzu mevcut Cinematic/Blades/NXE/XMB sistemindedir.
Yeni tema veya ikinci shell yoktur.

Test D-pad, analog/nötr, A aç, B geri, X başarım pini, Y arama, LB/RB sekme,
seçili oyun ve odak dönüşü ile Escape'i içerir. Analog testinde nötr örneği
beklenmeden A basılması test düzeneğinde düzeltildi; üretim tuş kontrolü
gevşetilmedi. X'in başarım ekranında hedef sabitlediği kılavuzda açık yazılır;
konsolda rastgele bir başarım otomatik sabitlenmez. Fiziksel kontrolcü/TV
mesafesi/NVDA kabulü tamamlandı diye işaretlenmez.

## Hedef oyunlar ve kabul tablosu

| Alan | Durum ve kanıt sınırı |
|---|---|
| Artwork Health | Kodlandı; gerçek yerel API + sentetik PNG/cache/HTTP yanıtlarıyla testli. Canlı kişisel kapsama ölçümü yok. |
| Minecraft: Xbox 360 Edition | Bloke: kullanıcının bu oyuna ait Title ID/kaynak/cache verisine erişim yok. Xbox 360/Bedrock/PC/iOS/Android birleştirilmedi. Testteki “12” gibi kimlikler sentetiktir. |
| Call of Duty: Black Ops Cold War | Bloke: gerçek edisyon ve mevcut kaynak bilinmiyor; kapağı düzeldi denmez. |
| Asphalt 9 / Asphalt Legends | Bloke: platform/edisyon ve isim değişimi doğrulanmadı; ad benzerliğinden eşleştirme yapılmaz. |
| Console Mode | Kodlandı; klavye ve standard Gamepad API simülasyonu. Fiziksel gamepad/TV kabulü bekler. |
| Xbox | Kullanıcı v0.16.2 akışı geçti dedi. Mock provider/yenileme/kimlik regresyonları korunur; tüm API senaryoları kabulü değil. |
| PSN / Steam | Kullanıcı v0.16.2 akışları geçti dedi. Provider/schema/partial/kimlik testleri korunur. |
| Arşiv | Ham JSON hash/restore, pin/not/tarih/local media koruma testleri. JSON medya dosyalarını taşımaz. Migrasyon yok. |
| Windows | Yeni exact HEAD Unit ve Windows native/installer/upgrade/rollback işlerinin sonucu SHA üzerinden ayrıca doğrulanmalı. Eski yeşil kaynak yeni HEAD kanıtı değildir. |
| Release | Yayımlanmadı. Otomatik kapılar başarılı olsa da gerçek hedef oyunlar ve fiziksel Console Mode kabulü eksik; yayın ayrıca kullanıcı onayı gerektirir. |

## Test raporu

Son yerel tur: **254/254 Python**, dört Node suite, gerekli JS syntax kontrolleri
ve CI sırasındaki **14 Chromium script'i** başarılı. Dört çözünürlük, 16 tema/
ekran, 5k/15k/40k ve simüle gamepad dahil; page_errors boş. Sürüm metadata'sı
0.16.3 test adayıdır, yayımlı kanal 0.16.2 kalır. Windows sonucu exact push
SHA'sında ayrıca beklenir; yerel Chromium, Windows WebView2 yerine geçmez.
Upgrade matrisi kullanıcıdaki mevcut yayımlı 0.16.2'yi de sabitlenmiş SHA256
ile içerir; aday kurulum/rollback testi güncelleme kanalında 0.16.3 yayımlamaz.
CSV'nin boş Title ID'si ile None eşdeğerdir; kullanıcının açık manuel SGDB
seçiminin aynı yerel oyun/edisyon kaynağı bu yüzden kaybolmaz. Dolu farklı
Title ID'ler yine reddedilir. Bu sınır durumu için red→green regresyon eklendi.

Yeni Title ID recovery ve reset testleri düzeltme öncesi başarısız oldu.
Health/UI testi gerçek localhost API'sini, tek oyun kapsamını, altı kategoriyi,
cache'i, kaçışlı oyun adlarını ve targeted retry'ı doğrular; indirme stub'ı açıkça
mock'tur. İlk UI testinde ID helper'ı CSS seçici gibi kullanıldığı için timeout
oldu; doğru DOM seçicisiyle test düzeltildi, kontrol kaldırılmadı.

Tam Python/Node, CI sırasındaki Chromium seti, dört çözünürlük/16 tema,
5k/15k/40k, arşiv ve tam Windows native/kurulum/upgrade-rollback çalıştırılır.
Son CI ve fiziksel kabul durumları Issue #40'ta kaynak SHA ile kaydedilir.
Hiçbir test veya başarısızlık gizlenmez; gerçek arşiv/credential istenmedi.
