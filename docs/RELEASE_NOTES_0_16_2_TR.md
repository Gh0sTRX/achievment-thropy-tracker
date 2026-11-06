# Achievement Atlas 0.16.2 — Development

## Yayın kanıtı — 6 Kasım 2026

Yayımlandı. Kaynak `ee13cd76ea9e6669d0dd60ed24fde773681c1e4d`,
geliştirme dalı `codex/public-profile-trophies`; main değişmedi.
247 Python testi ve tam Unit/Chromium/PowerShell matrisi: `42257112129` başarılı.
Windows native/installer/0.16.1 dahil upgrade-rollback, attestation ve yayın:
`42257112192` başarılı. Exact-source yayın test kapısı ayrıca geçti.

Installer `AchievementAtlas-0.16.2-Windows-x64-Setup.exe`, 33.346.488 byte;
SHA256 `df146f08541deada69fd97e83a006fe29d73de06c2db64598f343008c94c1ab2`.
Canlı manifest ve GitHub asset digest eşleşti; yayımlı EXE'nin gerçek baytları
da indirilip hash/boyut doğrulandı. Authenticode signed: false.

Yayın SONRASI stok **0.16.1 → 0.16.2** native uygulama içi indirme/doğrulama/
kurulum/yeniden açılış ve sentetik arşiv koruma geçti: aynı koşu attempt 2,
native job `128031624641`. Log `Native self-update passed: 0.16.1 -> 0.16.2`
der. Artifact metadata: paket `13523970328`, native rapor `13522699707`;
ZIP içerikleri yerelde açılmış gibi raporlanmaz. Bu fiziksel oyuncu cihazı veya
gerçek hesap kabulü değildir. Bu belge eklemesi yayın kaynağını değiştirmez.

`development` Git kaynak etiketi eski b214eee commit'inde korunmuştur. Etiketi
taşıma işlemi otomatik onay denetiminde yayımlanmış ref yeniden yazımı olarak
reddedildi; alternatif olarak etiket değiştirilmedi. Release sayfasındaki
otomatik Source code ZIP'i yerine gerçek kaynak için yukarıdaki ee13cd7 SHA'sını
kullan. EXE ve güncelleme manifestinin ee13cd7 kökeni ayrıca doğrulanmıştır.

## Kullanıcıya yansıyan düzeltmeler

- Game Universe ve Başarım Kasası ortak ikon/açıklama/tarih/kaynak bileşeni
  kullanır; tüm başarım çerçevesi tıklanabilir, pin ayrı çalışır, spoiler korunur.
- Kapaksız oyunlarda kompakt görünüm, mevcut kapaktan uyarlanan arka plan.
  Console Mode'da okunaklı kapak/metin/kontroller; yeni tema yoktur.
- Uygulama içi PSN/Steam kurulumu ve ayrı bağlantı testi. Platform hesap adları,
  durumları ve işlem geçmişi ayrıdır. Teknik ayrıntılar Hesap & Veri'dedir.
- Gerçek görsel indirme/önbellek/kaynaksız/hata sayıları ayrıdır. Onaylı Xbox
  TitleHub görsel türleri korunur; eksik cache aynı edisyon kaynağından kurtarılır.
  Bir host'un 403'ü bağımsız sağlayıcıları durdurmaz; 401/429 koruması sürer.
- Kullanıcı görseli sıfırlanınca önceki doğru kaynak korunur. Manuel sağlayıcı
  görselinin gerçek dosya adresi saklanır. Geç yanıt, yeni kullanıcı dosyasını
  veya değişmiş profil/edisyonu ezemez.
- Xbox token yenilemesi aynı süreçteki eşzamanlı işlemlerde sıraya alınır.
  Opsiyonel görsel/rehber hatası başarılı profil kaydını başarısız göstermez.
- PSN ilk oyun listesini alırken iptal ve ilerleme; yeniden kullanımda cihaz/
  edisyon kontrolü ve kupa grubu koruması; erişim/hız sınırı hatası ayrımı.
- Steam bozuk başarım satırı oyun düzeyinde ele alınır; aynı hesabın eski tarih,
  not, pin ve kazanımları korunur. Farklı hesap cache'i karıştırılmaz.
- Karma Steam/PSN/Xbox JSON yedeği ve tarayıcının hash bozan yeniden serileştirme
  hatası düzeltildi; native geri dönüş/odak davranışı korunur.
- Sınırlı Next Move: en fazla üç farklı oyun; pin, kayıtlardaki tamamlanma ve
  gerçek son kazanımlar. Kaynak ve bilinmeyenler açık; nadirlikten süre/kolaylık
  çıkarılmaz. Ücretli rehber varsayılan kapalıdır.

## Doğrulama ve kalan sınırlar

Kaynakta Python, Chromium, PowerShell ve Windows native/installer/upgrade/rollback
kontrolleri vardır. Yayın yalnız aynı commit'in tam test matrisi başarıyla
tamamlanırsa yapılır. Güncel sonuç kaynak SHA ve GitHub Actions ile ilişkilidir.
Önceki kaynakta bir native document-loaded timeout'u, test/süre değiştirilmeden
aynı commit'in tekrarında geçmiştir; WebView2 açılış kararlılığı takip edilir.

Gerçek Xbox reconnect hatasının tek nedeni doğrulanmadı. Gerçek PSN/Steam
hesap kabulü, PSN ilk sync hız ölçümü, fiziksel gamepad/NVDA ve kullanıcının
oyunlarındaki artwork kapsamı tamamlanmış değildir. Sentetik testler gerçek
başarım/görsel sonucu sayılmaz. JSON yedek medya dosyalarını içermez.

Paket Authenticode sertifikası olmadığında **imzasızdır**; GitHub/Sigstore köken
ve SHA256 doğrulaması Windows yayıncı imzası değildir. Windows/Chrome uyarısı
tamamen giderildi iddiası yoktur. Main değişmez; bu Development güncellemesidir.

## Güncelleme

Uygulama → Diğer ekranlar → Güncellemeler → Kontrol et → İndir → Kur ve yeniden
başlat. Önce yerel arşiv yedeği al; kişisel not/pin/medya dosyalarını sakla.
Kaynak eşleştirmesi olmayan CSV oyunlarına otomatik yanlış kapak atanmaz.
