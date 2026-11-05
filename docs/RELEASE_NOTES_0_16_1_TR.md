# Achievement Atlas 0.16.1 — geliştirme güncellemesi

## Değişiklikler

- Büyük kütüphanenin `/api/data` yanıtı istemci destekliyorsa gzip ile aktarılır. Eski istemcilere tam JSON desteği korunur.
- İçerik belirteci değişmediyse başarımlar/oyunlar tekrar gönderilmez; pin, tercihler, durum ve raporlar güncel kalır. Not, artwork, ilerleme ve profil değişiklikleri tam yanıtı geçersiz kılar. Arşiv biçimi değişmez, kontrolsüz migrasyon yapılmaz.
- Değişmeyen kütüphanede büyük diziler ve arayüz indeksleri korunur; raporlar içerik ve pinlere göre önbelleklenir. Gecikmiş eski yanıt daha yeni görünümü ezemez.
- Görsel Sağlığı düğmesinin POST/GET uyumsuzluğu giderildi; origin/token koruması sürer.

## Ölçüm ve doğrulama sınırları

Yerel sentetik kütüphane, aynı süreç/loopback HTTP, tek ölçüm; gerçek hesap veya internet eşitleme hızı değildir. İlk JSON serileştirme ve gzip CPU maliyeti devam eder; gzip tek başına daha düşük işlem süresi iddiası değildir.

| Başarım | Tam JSON byte | Gzip byte | Değişmeyen yanıt byte | Tam/gzip/kısmi süre ms |
|---|---:|---:|---:|---|
| 5.000 | 2.053.706 | 88.434 | 1.999 | 66,48 / 61,59 / 3,42 |
| 15.000 | 6.119.286 | 264.867 | 1.801 | 161,60 / 200,66 / 8,72 |
| 40.000 | 16.327.656 | 696.660 | 2.030 | 476,39 / 505,85 / 11,02 |

40 bin kayıtta ilk ağ aktarımı yaklaşık %95,7 küçüldü. Kısmi yanıt yine durum/rapor içerir, boyutu kullanıcıya göre değişir. 184 Python testi, HTTP sıkıştırma/partial/restore/failure regresyonları ve gerçek Chromium üzerinden pin/not/health/yanıt sıralaması testi yerelde geçti. Windows paketleme ve yayın kanıtları yayın sonrasında aşağıya kaydedilir.

## En önemli kalan 10 eksik

1. Yetkili gerçek Xbox hesabıyla uçtan uca kabul testi.
2. Yetkili gerçek PSN hesabıyla eski/yeni cihaz ve kısmi hata kabul testi.
3. Gerçek Steam anahtarı/hesabı ile kapsam ve rate-limit kabul testi.
4. Windows Authenticode sertifikası/yayıncı itibarı; GitHub/Sigstore köken doğrulaması Windows imzası değildir.
5. Fiziksel gamepad ve farklı Windows cihazlarında test.
6. NVDA/ekran okuyucu odak ve tam erişilebilirlik kabulü.
7. Gerçek cihazda güç kesintisi/logon/antivirüs koşullarında updater dayanıklılığı.
8. Eski oyun/edisyon artwork ve achievement ikon kapsamasının gerçek kaynaklarla tamamlanması.
9. Türkçe rehber kaynak doğruluğu ve ücretli çağrı bütçesinin gerçek servislerle kabulü (otomatik rehber varsayılan kapalı).
10. Daha büyük gerçek arşivlerde ilk JSON serileştirme/istatistik CPU maliyeti ve düşük donanım bellek profili.

Öncelik: gerçek hesap kabulü, eski platform/edisyon tutarlılığı, Windows imzalama ve düşük donanım ölçümü. Sahte başarımlar veya yapay oyun görselleri eklenmedi. Main dalı değiştirilmez.
