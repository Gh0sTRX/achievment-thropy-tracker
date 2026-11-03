# 0.12 — etkin geliştirme güncelleme kanalı

Varsayılan kanal `development` GitHub prerelease yayınıdır. Windows kod imzalama
sertifikası olmadan uygulama içinden güncelleme yapılabilir. Kurulum SHA256 ile
kontrol edilir; ardından gerçek GitHub OIDC/Sigstore derleme imzası, şeffaflık
kaydı ve SLSA köken kanıtı doğrulanır. İmza kontrolü kaldırılmamıştır.

Güven kökü Sigstore 4.5.1'in paketlediği üretim kökünden alınmış ve SHA256 ile
uygulamaya sabitlenmiştir. Doğrulama bu kökü doğrudan okur; kullanıcı cache'inden
veya güncelleme sunucusunun verdiği yeni kökten güven devralmaz. Yalnız:
- Gh0sTRX/achievment-thropy-tracker (repo/owner sayısal kimlikleri de kontrol edilir),
- .github/workflows/windows-package.yml,
- main veya codex/public-profile-trophies dalı,
- push olayı ve GitHub-hosted runner,
- doğru dosya adı, SHA256, kaynak commit ve workflow run kimliği
kabul edilir. Pull request, fork, farklı repo/dal/workflow ve bozuk kanıt reddedilir.

Workflow, Windows testleri başarılı olduktan sonra resmi actions/attest ile
kurulum dosyasının köken kanıtını üretir. Linux yayın işi kanıtı aynı Python
doğrulayıcıyla gerçekten doğrulamadan geliştirme kanalına yükleme yapmaz.
Özel güncelleme anahtarı veya GitHub kişisel token'ı uygulamaya gömülmez.

## Kullanım

Bu özelliği içeren 0.12 sürümü bir kez kurulmalıdır. Eski 0.11 güncelleyicisi
Windows sertifikası istediğinden yeni kanalı kendiliğinden açamaz. Sonrasında
Güncellemeler → Güncellemeyi indir → Kur ve yeniden başlat kullanılır. Uygulama
açılışta kanalı kontrol eder. Aynı sürüm numarasındaki daha yeni GitHub build'leri
run kimliğiyle ayırt edilir; daha eski sürüm/build uygulanmaz.

Yalnız Windows Setup kurulumu desteklenir; kaynak ve portable sürümler elle
kurulur. Profil/rehber/medya işlemi bitmeden uygulama kapatılmaz. Dosya ve köken
kanıtı indirmeden önce/sonra, kurulum öncesinde ve yardımcı süreçte tekrar
kontrol edilir. Yardımcı mevcut uygulamanın doğrulama modunu çağırır. Veriler
saklanır; önceki uygulama dosyaları yedeklenir ve kurulum hatasında geri kopyalanır.
Windows uygulama kilidi, Inno AppMutex ve betik politikası korunur.

## Windows sertifikasından farkı

Bu, Windows'un güvendiği bir yayıncı sertifikası değildir; yalnızca bizim
uygulamamızın kendi güncelleme güven modelidir. İlk dosyanın Chrome/SmartScreen
uyarısını kaldırmaz. Defender veya Windows tespiti/politikası aşılmaz, devre dışı
bırakılmaz; dosya karantinaya alınırsa doğrulama/kurulum başarısız olur.

Gelecekteki `stable` kanal mevcut Authenticode/same-publisher doğrulamasını korur.
Güven kökü veya yetkili workflow/dal değişikliği ayrı incelenmelidir. Ticari
sertifika gelene kadar geliştirme sürümleri yalnız bu açıkça belirtilen kanalda
sunulur. İmzalı köken kanıtı güvenlik açığı veya kötü amaçlı kod olmadığını tek
başına garanti etmez; kod incelemesi ve testler ayrıca gereklidir.
