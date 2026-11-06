# Eksik görsel önbelleğinin kurtarılması

## Kodda doğrulanan hata

`media_sync.download` başarılı kapak/hero indirmesinden sonra URL alanını
`local` olarak kaydediyor. Asıl kaynak `artwork_meta.source_url` içinde kalıyor.
Önbellek dosyası silindiğinde veya JSON arşivi görsel dosyaları olmadan geri
yüklendiğinde, eski indirme akışı bu kaynağı kullanmıyor; yeniden indirme
`missing_source` sayılabiliyordu. Sağlık raporu ise aynı kaynağı sayabiliyordu.

## Düzeltme ve veri koruması

İndirme, mevcut adaylardan sonra saklanan kaynak adresini de deniyor. Bunun
için oyun kimliği, platform ve edisyonun kayıttaki değerlerle eşleşmesi
gerekiyor. Aynı adlı başka oyun/edisyon aranmaz veya otomatik birleştirilmez.
Kullanıcının yerel dosyası internette aranmıyor. Mevcut URL güvenlik denetimi,
görsel decode kontrolü, iptal, retry ve indirme sayaçları korunuyor.
Notlar, kazanım tarihleri ve pinler değiştirilmez; arşiv migrasyonu yoktur.

## Doğrulama sınırı

Sentetik test gerçek PNG baytlarını mock HTTP yanıtıyla indiriyor, dosyayı
siliyor ve yalnız aynı edisyonun saklanmış kaynağından tekrar indirildiğini
kontrol ediyor. Ayrı negatif test diğer oyun/platform/edisyon ve kullanıcı
dosyasının kullanılmadığını doğruluyor.

Bu bulgu kullanıcının cihazındaki bütün eksik kapakların açıklaması değildir.
CSV'de kaynak URL/sağlayıcı kimliği bulunmayan oyunlar hâlâ açık eşleştirme
gerektirir. Gerçek Xbox/PSN/Steam hesabı veya canlı artwork sağlayıcısıyla
kabul testi yapılmadı. Kapak bulundu diye ayrı hero/logo varmış gibi davranılmaz.
Offline/online göstergesi bu değişikliğin kapsamında değildir. Release yoktur.
