# Issue #10 / A — CI sağlamlaştırması

İncelenen kırmızı koşular: 42055604757 / job 127343039044 (registry sentinel kayıp), 42055604856 / job 127343040498 (eski installer HTTP 504). Önceki 0.15.1 yayın koşuları başarılıdır; bu iki daha yeni PR kontrolü başarılı diye sunulmaz.

Kurtarma fixture'ının otomatik başlangıç görevi olarak gerçek RunOnce'a yazılması dış Windows logon tüketicisiyle yarışabilir. Test, üretim kodunu değiştirmeden yalnız çalıştırılan test kopyasının sabit registry yolunu gerçek registry sağlayıcısındaki benzersiz HKCU test anahtarına yönlendirir. PowerShell 5.1 Get-FileHash fonksiyonuyla çakışmaması için Windows filesystem cmdletleri gölgelenmez. Flush, değer/komut, ilgisiz sentinel, cleanup ve fresh-process rollback doğrulamaları korunur. Üretim kökü aynı kalır; fixture artık gerçek başlangıç görevi değildir. Bu kök-neden değerlendirmesi kayıp değer ve başarılı diğer koşulara dayanan bir çıkarımdır; fiziksel logon testi iddiası değildir.

`windows_download.ps1`: en fazla üç transport denemesi; 5xx/408/429/transport timeout yeniden denenebilir. Diğer 4xx ve SHA uyuşmazlığı derhal başarısız olur. Parçalı dosya silinir, doğrulanmamış EXE çalıştırılmaz. Hem native test hem eski installer matrisi aynı helper'ı kullanır. Dört ağ/hash senaryosu gerçek dosya hash'iyle, ağ sınırı taklidiyle test edilir.

Yeni Release ve main merge yok. Issue #10'un devamı Game Universe/artwork, PSN/Steam, UX/marka ve controller/performance ayrı PR'leridir.

Doğrulandı: Unit tests 42066272591 ve Windows installer 42066272796 başarılı. Native self-update kontrolü de başarılı; yayın işleri atlandı. Yeni sürüm yayımlanmadı. Sonraki özellik dallarının CI sonuçları ayrıca izlenmelidir.
