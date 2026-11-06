# Kullanıcı görselini kaldırma ve manuel sağlayıcı kaynağı

İki regresyon önce başarısız oldu. Birincisi: API kapağı cache'e alınır,
cover_url `local` olur; kullanıcı kendi dosyasını seçip kaldırınca önceki
adres boşalır. İkincisi: manuel SteamGridDB seçiminde source_url site ana
sayfası olarak ve oyun/edisyon kimlikleri olmadan saklanır; cache dosyası
kaybolduğunda gerçek seçili dosya kaynağı kurtarılamaz.

save_art artık önceki kaynak aynı oyun/platform/edisyona aitse gerçek adresi
original_url olarak korur. Kullanıcı dosyası korunur; reset var olan bu adrese
döner. Diğer edisyonun saklı adresi otomatik geri getirilmez. Tüm yeni manuel
kayıtlara oyun/platform/edisyon/Title ID provenance'ı eklenir. Manuel sağlayıcı
seçiminin source_url'si indirilen gerçek dosya, page_url'si sağlayıcı sayfasıdır.

Üç test: cache→kullanıcı dosyası→reset; manuel SGDB→cache kaybı→aynı dosyadan
yeniden indirme; farklı edisyonun kaynağının reddi. Gerçek PNG baytları ve mock
HTTP kullanılır; canlı oyun artwork kapsamı veya yeniden dağıtım izni kanıtı
değildir. Eski bozuk kaydın eksik dosya adresi tahmin edilmez; onaylı aday veya
kullanıcı seçimi gerekir. Arşiv migrasyonu, yeni API çağrısı veya yayın yoktur.
