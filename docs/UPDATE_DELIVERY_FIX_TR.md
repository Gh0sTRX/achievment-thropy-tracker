# 0.15 güncelleme teslimi düzeltmesi

Gözlem: geliştirme manifesti 0.14.1 iken kaynak sürümü 0.15.0. Preview etiketli Windows Setup gerçek kurulum dosyasıdır; HTML preview paketi ayrıdır. Kaynak kodunun veya Actions artifact'ının bulunması uygulamaya güncelleme yayımlandığı anlamına gelmez.

Doğrulanan hata: windows-package.yml içindeki manuel workflow_dispatch yayını, atlas/provenance.py içindeki yalnızca push kabul eden doğrulamadan geçemez. Eski kurulu sürümler de aynı güvenlik sözleşmesini kullanır. Yeni uygulamanın doğrulamasını gevşetmek eski uygulamaları düzeltmez.

Çözüm: Yetkili geliştirme dalına push derlemesinde EXE köken kanıtı ve manifest oluşturulur, artifact olarak saklanır; otomatik yayın yapılmaz. Mevcut Windows installer iş akışı manuel çalıştırılırken promote_run_id alanına başarılı push run ID girilir. İş akışı kaynak depo/dal/workflow/başarı durumunu kontrol eder; özgün artifact'ı indirir; EXE hash, boyut, commit, run ve Sigstore kanıtını yeniden doğrular. Yeniden derlemeden dosyaları yayımlar; manifest en son yüklenir. PR ve manuel derleme artifact'ları bu yoldan yayımlanamaz. Windows Authenticode imzası eklenmiş sayılmaz.

Bu ortamdan yeni Release oluşturulmadı. Windows üzerinde gerçek 0.14.1→0.15 yerinde yükseltme/geri dönüş henüz doğrulanmadı. Yeni push artifact'ı oluşmadan eski preview run'ı bu yeni yayın akışına uygun değildir.
