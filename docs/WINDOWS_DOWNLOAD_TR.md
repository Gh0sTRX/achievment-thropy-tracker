# Chrome / SmartScreen uyarısı ve Windows imzası

Chrome'un "Bu dosya tehlikeli" uyarısı tek başına bir teşhis değildir. İmzasız
yeni uygulamalar, düşük indirme itibarı, dosya içeriği veya gerçek bir zararlı
yazılım tespiti bu sonuca yol açabilir. İmzasız olmayı kesin neden olarak
sunamayız. Dosyanın taramadan geçmesi de tüm riskleri dışlamaz.

Bu projede UPX veya tek dosyalı kendini açan paket kullanılmıyor. Kaynak kod,
kurulum tarifi, bağımlılık listesi, SHA256 ve Windows test raporları incelenebilir.
Bunlar güvenilir yayıncı imzasının yerini tutmaz. Koruma kapatma, uyarıyı atlatma
veya dosyayı zararsızmış gibi yeniden adlandırma önerilmez.

## Yayıncı imzası için gereken erişim

Windows'un güvendiği bir sertifika otoritesinden kod imzalama sertifikası veya
Azure Artifact Signing / SignPath gibi bir imzalama hizmeti gerekir. Kendinden
imzalı sertifika üretmek sorunu çözmez. Sertifika, parola ve özel anahtarlar
sohbete veya Git deposuna konmaz.

PFX tabanlı imzalama için `scripts/sign_windows.ps1` eklendi. Depo işletmecisi
GitHub Actions secrets alanında `ATLAS_SIGNING_PFX` (PFX'in base64 değeri) ve
`ATLAS_SIGNING_PASSWORD` tanımlar. Script yalnız code-signing EKU'su olan,
Windows'un güven zincirine bağlanan sertifikayı kabul eder. EXE ve kurulum
ayrı ayrı SHA256 ile imzalanır, zaman damgası eklenir ve SignTool ile doğrulanır.
Geçici sertifika dosyası ve runner sertifikası işlem sonunda silinir.

Bu erişim tanımlı değilse paket açıkça imzasız geliştirme paketi olarak raporlanır;
uydurma yayıncı imzası eklenmez. Hizmet/HSM tabanlı sertifikalar için ilgili
sağlayıcının özel imzalama entegrasyonu ayrıca yapılandırılmalıdır.

Geçerli imza bile Chrome/SmartScreen uyarısının hemen kaybolacağını garanti
etmez. Sertifika/dosya itibarı ve tespit değerlendirmeleri ilgili güvenlik
sağlayıcısına aittir. Bir tespit hatalıysa dosyanın yayımlayıcısı Google veya
Microsoft'un resmi yanlış tespit inceleme sürecine başvurabilir.

Derleme ortamında Windows Defender çalıştırılabiliyorsa kurulum dosyası ayrıca
taranır. Sonuç `defender-report.json` içine yazılır. Tarayıcı kullanılamıyorsa
bu durum temiz sonuç gibi gösterilmez. Bu yerel tarama Google Safe Browsing
veya SmartScreen itibar kontrolünün yerine geçmez.
