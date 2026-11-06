# Onaylı CSV / Xbox oyun eşleştirmesinde artwork

## Gözlem

Kullanıcı Xbox keşfinden bir oyun ve edisyonu açıkça onayladığında
`Controller.xbox_map` yalnız `cover_url` değerini alıyordu. TitleHub yanıtının
`images` listesindeki kapak, logo, arka plan, banner ve screenshot adresleri
aktarılmıyordu. Buna karşılık herkese açık profil eşitlemesi bu listeyi işliyordu.
Bu nedenle aynı sağlayıcı verisi iki giriş yolunda farklı görsel kapsaması
oluşturabiliyordu. Bu kod gözlemidir; kullanıcının canlı yanıtı kaydedilmedi.

## Düzeltme

İki akış `artwork.xbox_title_candidates` ayrıştırıcısını kullanır. Yalnız
bildirilen türler ve mevcut HTTPS host izin listesinden geçen adresler kabul
edilir. Yinelenen aynı tür/adres çiftleri elenir; bilinmeyen türler atlanır.
Boyut veya oyun adına bakarak olmayan bir hero/logo türetilmez.

CSV eşleştirmesi hâlâ kullanıcı onayı, oyun adı ve keşfedilmiş Title ID/edisyon
kontrolünü gerektirir. Adaylara onaylı yerel oyun kimliği ve sağlayıcı Title ID
eklenir. Görseller mevcut durdurulabilir indirme akışından alınabilir; bu PR
kendiliğinden ağ isteği veya ücretli rehber çağrısı başlatmaz.

Yerel kullanıcı görselleri, notlar, pinler ve kazanılma tarihleri korunur.
Başarım kimlikleri değiştirilmez. Yeni platform veya arşiv migrasyonu yoktur.

## Test sınırı

Sentetik test güvenli/bilinmeyen/tekrarlı kategorileri ve bozuk listeyi denetler.
Controller testi onaysız eşleştirmeyi reddeder; onaydan sonra gerçek PNG
baytlarını mock HTTP ile mevcut cache akışına taşır, kullanıcı logosunun
üstüne yazılmadığını ve arşiv alanlarının korunduğunu doğrular.

Bu testler canlı Xbox erişimi veya gerçek oyunun tüm kategorilerinin TitleHub
tarafından sağlandığı anlamına gelmez. Kaynakta görsel yoksa eksik kalır.
Offline/online bildirimi sırada kalır. Release veya main merge yapılmaz.
