# Atlas Ultimate 0.13 — uygulama ve doğrulama

Kullanıcının Atlas_Ultimate_Interactive.html, DESIGN_SYSTEM_GALLERY.html,
CODEX_MASTER_IMPLEMENTATION_BRIEF_TR.md, COMPONENTS_AND_TOKENS_TR.md ve
SCREEN_WIREFRAMES_TR.md dosyaları tasarım referansı olarak kullanıldı.
Prototipteki oyunlar, skorlar ve bağlantı iddiaları üretim verisine taşınmadı.
Paketin söz ettiği REAL_GAME_ASSET_MANIFEST.json bu yüklemede yoktu; oyun/edisyon
kimlikleri tahmin edilmedi ve uzaktan oyun listesi üretilmedi.

## Uygulanan fazlar

- A: ACS renk tokenları, bağımsız platform filtresi/tema, erişilebilir shell,
  küresel arama, mobil menü ve yerel state.json içinde görünüm tercihleri.
- B: kayıtlı oyuna bağlı sinematik hero ve gezinme okları, oyun şeridi,
  Izgara/Vitrin/Koleksiyon düzenleri, oyun dosyası, tarihler, DLC grupları ve
  kalıcı yerel notlar. Aynı adlı farklı cihaz oyunları birleştirilmez.
- C: 48 satırlık başarım sayfalaması, grup/durum/oyun filtreleri, sağdan açılan
  klavye erişimli detay paneli, gizli başarım koruması, gerçek API ilerlemesi,
  kaynağa bağlı kupa rütbesi ve Hedef Panosu. Pin değişikliği sunucu başarılı
  olmadan kesinleşmez. TA oranı süre veya yüzde değildir.
- D: yalnız gerçek kazanımların müzesi ve yerel oyuncu profili. Platin için
  kazanılmış PSN platinum kaydı gerekir. Tam kapsam bildirilmeyen bir listede
  bütün kayıtlar kazanılmış olsa bile kesin oyun %100 iddiası yapılmaz.
- E: mevcut güvenli artwork cache ve kullanıcı dosyaları korunur; SGDB logos,
  hero/kapak seçimi, odak, karartma, ambient bulanıklık, kaynak atfı ve özel
  görsel sıfırlama. Kaynak erişimi 403/429 ile durursa atlatılmaz.

Opsiyonel Faz F (gamepad / console mode) bu sürümün kapsamına alınmadı.

## Mimari ve veri

`atlas/web/model.js` saf kapsam/metrik/tarih/ilerleme projeksiyonlarını taşır;
15.000 kayıt her çizimde oyunlara indekslenir. Kasa yalnız görünür 48 kaydı
çizer. Kütüphane 80 kartlık sayfalara bölünür. `ultimate.js` mevcut API
bağlarını değiştirmeden yeni ekranları bağlar; `ultimate.css` ACS katmanıdır.
Statik dosyalar sunucunun açık izin listesine eklendi; keyfi dosya servisi yok.

Geriye uyumlu state.ui tercihleri: theme_mode, platform_filter, library_layout,
focus_game_id, reduced_motion, dense_mode, high_contrast, font_scale ve
hero_contrast. Eski oyun ID'leri ve pinler korunur. `art_theme` eski x/y/preset
alanlarını korur, overlay ve blur ekler. Yeni endpoint'ler `/api/preferences`
ve `/api/game/notes` aynı token/Host/Origin kontrolleri arkasındadır.

Veri sağlayıcıları bu işten önce mevcut olan Xbox ve PSN adaptörleridir.
Bunlar gerekli servis erişimine bağlıdır; Gh0sTRX55 canlı profili bu arayüz
görevinde doğrulanmadı. PC/Steam adaptörü planlanıyor; Windows/iOS/Android
Xbox ağı oyunları Xbox kapsamındadır. PSN adaptörü olmadığı yönündeki eski
tasarım belgesi ifadesi mevcut uygulamaya uygulanmadı.

## Görseller

Kaynaklar: mevcut Xbox/PSN sağlayıcı URL'leri, kullanıcının seçtiği yerel dosyalar
ve isteğe bağlı SteamGridDB. Diğer 11 kaynak keşif kataloğunda kalır; entegrasyon
varmış gibi sunulmaz. Oyun resimleri veya font dosyaları repo/EXE içine eklenmedi.
Yapay zekâ oyun görseli üretilmedi. Kaynak metadata'sı dağıtım izni sayılmaz.

## Doğrulama

- Python: 79 birim/HTTP entegrasyon testi geçti.
- Node: dört JS dosyasının sözdizimi; model testi 15.000 kayıtta platform/edisyon
  ayrımı, yalnız Xbox Gamerscore, boş veri, kapsamlı tamamlama, gizli kayıt,
  sıfır ölçülen ilerleme ve geçerli tarihleri doğruladı.
- Chromium: 1920×1080, 1440×900, 980×640, 390×844 boyutlarında tüm yeni/var olan
  sayfalarda yatay taşma yok. Boş durumlarda JavaScript hatası yok.
- Geçici TEST FIXTURE verisiyle: pin API, drawer/Escape, not saklama, tarih/DLC,
  filtreler, yeniden yüklemede tema/düzen kalıcılığı, reduced motion,
  yüksek kontrast ve %130 yazı büyütme kontrol edildi.
- 15.000 kayıtta tarayıcı testi: 48 DOM satırı, 313 sayfa; örnek yerel çizim
  54–126 ms. Bu bir performans garantisi veya farklı cihaz benchmark'ı değildir.
- Yerel ekran görüntüleri work/ultimate altında; test verileri/tercihler yalnız
  /tmp içinde tutuldu, dağıtıma eklenmedi.
- Windows pywebview, frozen SDK/güven kökü ve Setup kurulum/kaldırma kontrolleri
  Windows paket workflow'unda ayrıca çalışır. Yayın işi gerçek Sigstore köken
  kanıtını doğrulamadan geliştirme güncellemesini yayınlamaz.

Kod imzalama ve mevcut güncelleyici korumaları değiştirilmedi. İlk indirme için
Windows yayıncı sertifikası hâlâ ayrıdır; SignPath onayı varsayılmaz.

İlk uygulama commit'leri: f0ae1ee (Faz A), cc15538 (Faz B–E), 691121b
(%130 yazıda mobil genişlik). Ana daldaki SignPath/gizlilik belgeleri de
korunarak birleştirildi.
