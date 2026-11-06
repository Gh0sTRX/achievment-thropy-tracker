# PSN tekrar eşitleme ve hata sınıfları

## Doğrulanan hatalar

`sync_control.reuse` aynı ID, hesap, ilerleme imzası ve API neslini kontrol
ediyordu; platform, Title ID, edisyon ve cihaz değişimini ayrıca kontrol
etmiyordu. Negatif test farklı platformda eski satırların döndüğünü göstererek
başarısız oldu. Şimdi bu alanlar değiştiğinde cache reddedilir ve gerçek sağlayıcı
sorgusu gerekir. Aynı ad nedeniyle oyunlar birleştirilmez.

PSN cache hit, satırları koruyor ama oyun üzerindeki trophy_groups bilgisini
yeni oyuna taşımıyordu. Aynı kimlikteki gruplar ve satırlar deepcopy ile korunur;
yeni nesne değişirse eski arşiv/cache nesnesi değişmez.

PSN title fetch içindeki 401/403/429 hataları plain ValueError'a çevrilirken kod
kayboluyordu. Bazı TooManyRequests sınıfları da title partial hata gibi işleniyordu.
Güvenli uygulama mesajı korunurken kod/sınıf metadata'sı taşınır; hesap ekranında
expired/rate_limited ayrımı yapılabilir. Ham URL, header veya secret gösterilmez.

## Test ve sınırlar

Kimlik/edisyon/cihaz negatifleri, grup kopyalama ve mutasyonsuz reuse; PSN
401/403/429 ile SDK TooManyRequests sınıfı mock testleri eklendi. Tam Python
regresyonu çalıştırılır. Bu testler gerçek NPSSO/PSN hesabı kabulü veya ilk
eşitleme hız ölçümü değildir. Yeni paralellik, hız sınırı atlama veya yeni servis
eklenmedi. Eski arşivler dönüştürülmez; şüpheli cache'te ağ sorgusu tercih edilir.
