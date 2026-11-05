# Güncelleme geri alma: doğrulanmış dosya snapshot'ı

## Gözlem

0.15.0'da `scripts/apply_update.ps1` yalnız installer sıfırdan farklı çıkış kodu döndürürse yedeği eski dosyaların üzerine kopyalıyordu. Yeni sürümün eklediği dosyalar silinmiyor; installer başlatma/bekleme istisnasında geri alma çalışmıyordu. Karışık dosya kümesi yeniden başlatılabiliyordu.

## Değişiklik

- Kurulum başlamadan kurulum ağacının dosya yolları, dizinleri, dosya SHA256 değerleri alınır; gizli dosyalar ve boş dizinler korunur.
- Kurulum dışında yeni bir yedek klasörü gerekir. Var olan kurtarma yedeği ezilmez. Reparse point içeren kurulumlar reddedilir.
- Kopyalanan yedeğin tüm içeriği doğrulanmadan installer başlamaz.
- Installer hata kodu veya başlatma/bekleme istisnasında önce yedek yeniden doğrulanır. Sonra yeni dosyalar/dizinler ve dosya-dizin tip değişimleri temizlenir, eski dosyalar geri yüklenir, tüm küme tekrar doğrulanır.
- Geri alma doğrulanamazsa otomatik yeniden başlatma yapılmaz; yedek yolu ve `ROLLBACK FAILED` update.log'a yazılır.
- Başarılı kurulum bu yoldan geri alınmaz. Profil/JSON dosyaları bu testlerde okunmaz veya değiştirilmez; otomatik güncelleme zaten verinin kurulum klasörü dışında olmasını gerektirir.

## Doğrulama ve sınırlar

`tests/test_update_snapshot.ps1` gerçek üretim fonksiyonlarını ve helper girişini çalıştırır. Yalnız süreç/OS sınırları sentetiktir. Dokuz senaryo: yeni dosya ve tip değişimi sonrası birebir geri alma; bozuk yedekte kurulum ağacına dokunmama; iç içe/eski yedek reddi; reparse point reddi; installer hata kodu; başlatma istisnası; silinmiş kurulum klasörünü yeniden oluşturma; bozuk geri alma sonrası yeniden başlatmama; başarılı güncellemeyi koruma. Yollar boşluk ve köşeli parantez içerir, gizli dosya da denetlenir.

Yerel PowerShell 7.4.6/Linux: 9 senaryo geçti. GitHub Windows PowerShell 5.1 ve pwsh sonuçları PR kontrollerinde ayrıca takip edilir. Windows installer workflow'una da eklendi. Bu testler gerçek Inno Setup'ın yarıda kesilmesi, gerçek 0.14.1→0.15 kullanıcı yükseltmesi veya fiziksel Windows cihaz testi değildir.

**Kalan:** güç kesintisinden sonra otomatik devam eden kalıcı update journal yok. Snapshot envanteri yardımcı süreç belleğindedir. ACL, ADS, registry, kısayol ve Inno uninstall kayıtlarının transaction geri alınması garanti edilmez; kapsam kurulum ağacının dosya/dizin içeriğidir. Disk dolması/kilitli dosya geri almayı engellerse yedek tutulur, uygulama başlatılmaz. Bilgisayarda/VM'de gerçek eski→yeni yükseltme ve kesinti matrisi sonraki adımdır.


## Gerçek kurulum yükseltme matrisi

`tests/test_windows_upgrade.ps1` Windows installer CI içinde gerçek yayımlanmış 0.13.0 ve 0.14.1 Setup dosyalarını sabit SHA256 ile indirir. Geçici ayrı kurulum/veri klasöründe eski native uygulamayı açıp localhost API üzerinden iki sentetik başarım, sabitleme ve oyun notu oluşturur. Yeni Setup aynı kurulum klasörüne gerçekten kurulur. Production snapshot fonksiyonlarıyla eski dosya kümesine bilinçli geri dönülür; eski EXE sürümü/self-test ve native uygulama kayıtları denetlenir. Yeniden yükseltme, yeni EXE sürümü/self-test, native başlatma, kalıcı yeni sabitleme ve restart yapılır. Son uninstall sonrasında dış veri klasöründeki library ve byte sentinel korunmalıdır.

Sonuç `upgrade-test-report.json` içinde artifact'a eklenir; CI sonucu görülmeden başarılı sayılmaz. Bu, Windows runner üzerinde gerçek Inno installer ve native EXE yükseltme testidir; gerçek kullanıcı verisi veya Xbox/PSN hesabı içermez. Installer sürecini kasıtlı öldürme, güç kesintisi, tam GUI güncelleme düğmesi zinciri ve registry transaction geri alma testi değildir. Hata durumları önceki dokuz helper senaryosunda OS süreç sınırında enjekte edilir.
