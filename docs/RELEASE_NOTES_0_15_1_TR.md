# Achievement Atlas 0.15.1 — güncelleme dayanıklılığı

0.15.0 üzerine güncelleme güvenliği iyileştirmesi. Tek native arayüz ve gerçek platform/edisyon kayıtları korunur.

- Hatalı kurulumda yeni eklenen dosyaları temizleyen, tüm eski dosya kümesini SHA256 ile doğrulayan geri alma.
- Yeni yardımcıda özel veri klasörünün başarılı ve başarısız güncelleme sonrası korunması. Zaten dağıtılmış eski yardımcı bu bilgiyi içermiyorsa ilk geçişte aynı klasörü yeniden seçmek gerekebilir; arşiv silinmez.
- Diske tamamlanan yedek, yardımcı/plan ve kalıcı recovery-state; kurulum yarıda kalırsa kullanıcı kapsamında RunOnce ile sonraki logon'da bir kez kurtarma denemesi.
- Bozuk/kayıp yedekte, uyuşmayan kayıtta veya çalışan uygulamada dosyalara dokunmama. Tamamlanmış kurtarma tekrar çalıştırılırsa no-op.
- Bekleyen kurtarma varken ikinci güncellemeyi engelleme; uninstall sırasında yalnız Atlas kurtarma görevlerini silme.
- Paket ve arayüzde gerçek sürüm etiketi; eski Preview kurulum açıklamaları güncellendi.

Kaynak doğrulaması: 146 Python testi, 9 helper ve 8 süreç kesintisi senaryosu, Linux/Windows PowerShell testleri; gerçek eski installer yükseltme/kaldırma matrisi ve yayımlanmış uygulamanın native güncelleme düğmeleri. 0.15.1 sürüm paketinin Windows CI sonucu yayın öncesinde ayrıca kontrol edilir; sürüm notunun varlığı başarılı build kanıtı değildir.

Fiziksel elektrik kesintisi ve gerçek yeniden logon doğrulanmış sayılmaz; Windows politikası/zamanlaması otomatik denemeyi engelleyebilir. Registry/ACL/ADS tam transaction geri alma kapsamında değildir. Kurtarma tasarımı ve manuel yol: UPDATE_CRASH_RECOVERY_TR.md.

Windows Authenticode sertifikası henüz yoktur. Geliştirme kanalı SHA256 ve GitHub/Sigstore push provenance doğrular; bu bir Windows yayıncı imzası değildir. Bu sürüm sahte kupa, AI oyun artwork'ü veya yeni ücretli rehber varsayılanı eklemez. Main dalı değiştirilmez.
