# Geç gelen manuel artwork yanıtları

Üç red→green regresyon: SGDB indirmesi sırasında yeni user_file seçilirse eski
yanıt kullanıcı dosyasını eziyordu; aynı ID'li profil kaydı değişirse eski yanıt
yeni kayda yazılıyordu; seçim sorgusu sürerken edisyon yerinde değiştirilirse
referans karşılaştırması değişikliği fark etmiyordu.

Manuel seçim artık başlangıç kimliğinin ve kategori metadata'sının derin
kopyasını alır. Ağ erişimi store lock dışında kalır. Yanıtın MIME'si ve mevcut
profil nesnesi/edisyon/cihaz/eşleştirme/görsel metadata'sı dosya yazımından önce
kontrol edilir. Değişmişse dosya veya metadata güncellenmeden yeniden onay
istenir. Görsel decode ve atomik cache yazımı mevcut sınırlarla korunur.
Seçim adayları için de canlı nesneyle kendi kendini karşılaştırma yerine
değişmez kimlik kopyası kullanılır. Yerel upload'un cache+metadata yazımları
aynı store lock altında tamamlanır; medya işinin aynı dosyaya yazımıyla yarışmaz.

Mock HTTP yanıtı içinde kullanıcı dosyası değiştirilerek gerçek PNG/WebP
baytlarının korunduğu doğrulanır. Profil nesnesi yenilenmesi ve in-place edisyon
değişimi negatifleri de vardır. Canlı oyun artwork kapsamı/hesap kabulü değildir.
Arşiv migrasyonu, kimlik birleştirme, yeni sağlayıcı, ücretli çağrı ve yayın yok.
