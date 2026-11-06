# Sınırlı Next Move — kaynak uygulaması

Ürün problemi: önceki önerici TA oranı, puan ve açıklama varlığını ağırlıklı
skora çeviriyordu. Bu sinyaller bir başarımın kolaylığı veya oyuncunun sonraki
hedefi olduğuna kanıt değildir. Ana ekranın ve hedef panosunun Next Move alanı
artık ayrı `next_moves` raporunu kullanır. Eski sıralama diğer uyumluluk
alanlarında korunur; kullanıcı arşivi veya pinleri değiştirilmez.

En fazla üç farklı oyun/edisyon, her biri tek hedef. Sıra: kullanıcının pini,
eldeki kayıtlarda en az %75 kazanılmış olması, son 30 günün geçerli kazanım
tarihleri. Eşitlik kimlikle deterministik çözülür; oyun adları birleştirilmez.
Kazanılmış veya kaynakta risk işaretli hedef önerilmez. Bu üç sinyal yoksa
uydurma bir hedefle alan doldurulmaz. Yalnız gün biliniyorsa saat üretilmez;
belirsiz, gelecek veya kilitli kayıt tarihleri kullanılmaz.

Her öneri gerekçeyi, arşivdeki kaynak etiketlerini ve süre/zorluk/sahiplik/online
erişilebilirlik bilgilerinin doğrulanmadığını gösterir. Kapsamı tam olmayan
arşivde kalan kayıt sayısının bütün oyun/DLC anlamına gelmediği belirtilir.
Kaynak etiketi kaydın mevcut iddiasıdır; bağımsız doğrulama puanı değildir.
TA oranı, Gamerscore ve açıklama varlığı sıralamayı değiştirmez.

Platform raporları ayrı, uygulama günün değişiminde öneri cache'ini yeniler.
Hiçbir API/LLM/ücretli rehber çağrısı başlatılmaz. Yeni form/tema/sayfa yoktur.
Offline/online durum göstergesi kullanıcı talebiyle ertelenmiş kalır.

Testler: pin önceliği, 3 sınırı, edisyon ayrımı, mutasyonsuz çalışma, puan/ratio
bağımsızlığı, tarih negatifleri, riskli/kazanılmış hedefler; Chromium kart/kaynak/
belirsizlik/platform ayrımı. Bunlar sentetik testlerdir. Gerçek kullanıcıyla
hedef bulma süresi ve tercih testi yapılmadı; 30 saniye veya kolay hedef vaadi yok.
