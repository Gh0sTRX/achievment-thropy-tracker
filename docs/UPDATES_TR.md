# GitHub güncelleme kanalı

Uygulama açılışında GitHub Releases `/releases/latest` kararlı yayını kontrol
edilir. Güncellemeler ekranından kontrol elle tekrarlanabilir. Kullanıcı yeni
sürümü indirir; doğrulamadan sonra **Kur ve yeniden başlat** düğmesini kullanır.
Actions çıktıları geçicidir ve bu kanal için kullanılmaz. Kararlı vX.Y.Z yayını,
uyumlu Setup.exe ve update-manifest.json sağlamalıdır. Taslak/prerelease ve eski
veya aynı sürümler kurulmaz.

Manifest repo/sürüm/dosya adı/boyut/SHA256/yayıncı sertifika özetini içerir.
İndirme yalnız sabit GitHub deposundan HTTPS ile yapılır; yönlendirme alanları
GitHub varlık sunucularıyla sınırlandırılır. Dosya akış halinde indirilir;
boyut ve hash tutmazsa silinir. Manifestteki `signed=true` tek başına güven
sağlamaz: mevcut uygulama ve indirilen kurulum Windows Authenticode ile
`Valid` olmalı ve aynı sertifika SHA256 değerini taşımalıdır.

Sertifika yenileme/yayıncı değişimi için otomatik güven verilmez; ilk yeni
imzalı sürümün elle doğrulanarak kurulması gerekir. Bu sürümün ilk kez kurulması
önceki uygulamaya güncelleyici eklemek için de gereklidir. İmzasız 0.x
geliştirme paketleri kendi kendilerini güvenilir yayıncıya dönüştüremez.
Mevcut sertifika erişimi olmadığından imzalı kanal şu an devreye alınmış değildir.
Bu özellik Chrome/SmartScreen korumasını aşmanın bir yolu değildir.

## Kurulum davranışı

Yalnız Windows Setup ile kurulmuş frozen sürüm desteklenir. Kaynak kod ve
portable sürümde kontrol yapılabilir; otomatik kurulum yapılmaz. Devam eden
profil, rehber, medya veya oturum işlemi varsa güncelleme bekletilir. Kütüphane
ve ayarlar diske kaydedilir, doğrulanmış yardımcı başlatılır, pencere kapatılır.
Yardımcı eski işlemin çıkmasını bekler; zorla sonlandırmaz. Kurulumdan önce
hash/imza yeniden kontrol edilir. Windows tek-örnek kilidi ve Inno AppMutex kontrolü başka açık uygulama örneği
varken dosyaların değiştirilmesini önler. Mevcut uygulama dosyaları yedeklenir; kurulum
hatasında önceki dosyalar geri kopyalanıp eski uygulama yeniden açılır. Yerel
kütüphane kurulum klasörü dışında tutulur ve korunur. Günlük/yedekler uygulamanın
veri klasöründeki updates altında kalır. Windows betik politikası yardımcıyı
engellerse politika değiştirilmez ve uygulama kapanmadan işlem iptal edilir.

## Yayınlama

Windows workflow, son imzalamadan sonra scripts/build_update_manifest.py ile
manifest üretir. Sertifika yoksa manifest `signed=false` olur. Yalnız vX.Y.Z
tag push'unda ve imzalı/matching manifest varsa publish işi kalıcı GitHub Release
oluşturur. Sertifika yoksa bu yayınlama işi durur. Normal PR derlemeleri yine
incelenebilir imzasız geliştirme artifact'ları üretir; otomatik kanala girmez.

Testler ağ/Windows doğrulayıcısı için sahte yanıtlarla yeni sürüm seçimi,
bozuk manifest/hash, yanlış yayıncı, imzasız dosya ve çalışırken kurulum
engellerini kapsar. Gerçek imzalı yükseltme ve başarısız kurulumdan geri dönüş,
gerçek sertifika ve iki imzalı sürüm olmadan uçtan uca doğrulanmış sayılmaz.
