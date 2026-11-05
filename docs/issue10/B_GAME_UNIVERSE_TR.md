# Issue 10 — Game Universe ve görsel kapsamı

Oyun kartları, hero ve Console A aynı `#/game/{kalıcı-kimlik}` rotasına gider. Panel kütüphane içinde kaydırılmaz; tek native shell içinde ayrı sayfadır. Genel bakış, kupalar, hedefler, görseller, DLC/gruplar, zaman çizelgesi ve notlar mevcut kayıtlardan üretilir. Kupalar 48 satır sayfalanır, gizli adlar korunur, detaylar mevcut inline sistemi kullanır. Geçmiş ve Escape önceki sayfa, cihaz/platform filtresi, kütüphane sayfası, kaydırma ve görünür kart odağını geri getirir. Kaydedilmemiş notlar arka plan render işleminde korunur.

Görsel indirme kapak/logo yanında hero/banner/screenshot adaylarını da kullanır. Xbox TitleHub türleri kalıcı title ID bağlamında sınıflanır. Dosyalar mevcut HTTPS/redirect/MIME/boyut/decode kontrollerinden geçer; yerel kullanıcı görseli korunur. Görsel sağlığı yalnız gerçekten önbellekteki dosyaları sayar; aday URL kapsama sayılmaz. SteamGridDB sürüm onayı mevcut akışta korunur. Otomatik başlık benzerliğiyle edisyon birleştirme yapılmaz.

## Doğrulama

- Sentetik Chromium: 1920×1080, 1440×900, 980×640, 390×844. Rota, back/forward, deep link, focus, 7 sekme, taslak not, XSS kaçışı, yatay taşma kontrolleri geçti.
- Yeni sentetik görsel testi: beş türde 0/5 → 5/5 doğrulanmış yerel kapsam; ikinci indirmede ağ çağrısı yok.
- Gerçek kullanıcı arşivi bu ortamda yok. Gerçek hesap görsel kapsaması ölçülmedi; yukarıdaki oran yalnız fixture sonucudur.
- Gerçek hesap / fiziksel gamepad / Windows görsel UX testi yapılmadı.

## Henüz tamamlanmayanlar

Kalıcı SteamGridDB eşleştirme kaydı, kullanıcıya 2–5 aday sıralama, sağlayıcıya göre yeniden deneme beklemeleri, Game Universe tab klavye ok gezinmesi ve gamepad B desteği sonraki parçalarda tamamlanmalıdır. Bu PR bütün Issue 10 teslimatı değildir. Yeni release oluşturmaz.
