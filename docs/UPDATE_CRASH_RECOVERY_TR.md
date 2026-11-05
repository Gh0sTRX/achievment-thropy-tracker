# Yarıda kalan güncellemenin kurtarılması (kaynak dalı)

Bu geliştirme `feature/update-crash-recovery` dalında, PR #8'in doğrulanmış kodu üzerine kurulur. Yayımlanmış 0.15.0 yardımcılarını geriye dönük değiştirmez; yeni Release yayımlanmadı.

## İşlem sırası

1. Yeni installer'ın mevcut SHA256/köken veya yayıncı doğrulaması yapılır.
2. Kurulum dışındaki `updates/release-*/previous-version` yedeğinin dosyaları disk flush ile tamamlanır ve tam dosya/dizin SHA256 envanteriyle doğrulanır.
3. Aynı release klasörüne `recovery-state.json` atomik dosya değişimiyle, UTF-8 ve disk flush kullanılarak `pending` olarak yazılır. Plan, yollar ve envanter burada kalır; uygulama binary'sine bağımlı değildir.
4. Kullanıcının HKCU RunOnce anahtarına yalnız bu plana ait `!AchievementAtlasRecovery-<hash>` değeri yazılıp geri okunarak doğrulanır ve registry anahtarı flush edilir. Komut, kurulum dışına kopyalanmış PowerShell yardımcısını `-Recover` ile çalıştırır. Sürekli arka plan servisi veya zamanlanmış görev oluşturulmaz. Komut Windows sınırını aşarsa/registry kaydı başarısızsa installer başlamaz. ExecutionPolicy değiştirilmez.
5. Installer başarılıysa kalıcı durum `completed` olur ve RunOnce temizlenir; özel veri klasörüyle uygulama açılır. Hatalı kurulum geri alındığında `rolled_back` yazılır ve görev temizlenir.
6. Yardımcı yarıda sonlanırsa bir sonraki kullanıcı oturum açılışında Windows kurtarmayı bir kez dener. `pending` kaydının planla ilişkisi ve yedeğin tüm içeriği yeniden doğrulanır. Eski dosyalar geri yüklenir; yeni eklenmiş dosyalar silinir; son küme doğrulanır. Sonra `rolled_back` yazılır ve eski uygulama aynı veri klasörüyle açılır.

Çalışan uygulama varsa, yedek/kayıt bozuksa veya yollar uyuşmuyorsa kurtarma dosyaları değiştirmez. İşlem kaydı/yedek ve update.log tutulur. Tamamlanmış işlem için tekrar kurtarma hiçbir dosyayı değiştirmez ve uygulamayı tekrar açmaz. Sonuç belirsizse dosyaları silmek veya güncellemeyi zorlamak doğru değildir.

Bekleyen veya bozuk işlem kaydı varsa yeni download/install ağ isteği veya kapanış öncesinde engellenir. Kullanıcının RunOnce Atlas kayıtları da denetlenir; başka veri klasörüne geçiş, önceki kurtarmanın üstüne yeni kurulum başlatamaz. Tamamlanmış/geri alınmış kayıtlar engel değildir.

## Kaldırma ve yerel gizlilik

Yeni uninstaller yalnız `!AchievementAtlasRecovery-` isim alanındaki RunOnce değerlerini kaldırır: kullanıcı uygulamayı kaldırdıktan sonra otomatik kurtarma eski uygulamayı yeniden kurmamalıdır. İlgisiz RunOnce değerleri korunur. Library/profil/ayarlar kurulum ağacından ayrı kalır. Registry komutunda yerel yardımcı dosya yolu vardır; parola, servis anahtarı veya oyuncu tokenı yoktur. Yedekler mevcut saklama politikasındaki gibi yerelde kalır.

Manuel kurtarma gerekirse, ilgili `updates/release-*` klasöründeki `apply-update.ps1` betiği `powershell.exe -NoProfile -File "<tam yardımcı yolu>" -Recover` ile çalıştırılır; varsayılan plan aynı klasördeki plan.json'dır. Windows betik politikası engelliyorsa politika atlatılmaz. Kurtarma dosyalarını silmeden önce log ve yedeği koru. Uygulamayı kaldırmak otomatik denemeyi iptal eder; veri klasörünü temizlemeden önce bunu yapmak sarkan bir RunOnce yolunu önler.

## Test kanıtı ve sınırlar

`tests/test_update_crash_recovery.ps1` yardımcıyı gerçek bir alt PowerShell sürecinde başlatır; sahte installer dosyaları değiştirdikten sonra süreç zorla öldürülür. Kurtarma yeni süreçte çalışır. Sekiz senaryo: pending, kayıp kurulum, bozuk yedek, çalışan uygulama, bozuk JSON, yol uyuşmazlığı, kayıp yedek ve tamamlanmış işlem. Reddedilen kurtarmada dosyaların korunması, tekrar denemenin çalışması, ikinci kurtarmanın no-op olması ve özel veri klasörü aktarımı denetlenir. Windows koşusunda gerçek HKCU RunOnce komutu/yazma/temizleme ve ilgisiz değerin korunması da kontrol edilir. Linux'ta yalnız registry/süreç uygulama sınırları taklittir; dosya journal'ı ve süreç öldürme gerçektir.

Yerel Linux/PowerShell 7.4.6: 8 senaryo ve önceki 9 helper senaryosu geçti. Windows PowerShell 5.1/pwsh ve Inno uninstall sonuçları CI'dan doğrulanmalıdır. Native eski→yeni yükseltme testi, yeni uninstaller'ın kurtarma kaydını temizleyip ilgisiz registry değerini koruduğunu da denetler.

**Garanti sınırı:** Gerçek elektrik kesintisi, gerçek yeniden oturum açılışı, firmware/disk cache dayanıklılığı, Windows startup politikası ve RunOnce zamanlaması fiziksel cihazda doğrulanmadı. RunOnce bir kez deneme mekanizmasıdır; Windows/politika çalıştırmazsa veya deneme başarısızsa manuel kurtarma gerekebilir. Açılışta uygulamayla yarış veya kilitli dosya kurtarmayı erteleyebilir; uygulama zorla kapatılmaz. Registry/uninstall metadata, ACL/ADS ve harici kısayollar transaction olarak geri alınmaz. Şema/snapshot, eski dosya kümesini korur; tam sistem transaction'ı olduğu iddia edilmez.
