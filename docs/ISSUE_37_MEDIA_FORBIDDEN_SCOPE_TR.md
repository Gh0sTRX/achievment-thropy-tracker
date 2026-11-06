# Görsel erişim engelinin kapsamı

Önceki indirmede tek görselin HTTP 403 yanıtı global stop event'ini kuruyordu.
Başka izinli sağlayıcıdaki mevcut adaylar da denenmeden cancelled oluyordu.
Regresyon önce başarısız oldu: Xbox görseli 403, bağımsız SGDB hero başarılı
mock yanıtına rağmen indirilen sayısı sıfırdı.

403 artık o işte sunucu adına göre engellenir. O sunucuya yeni istek yapılmaz;
önceden seçilmiş/onaylı bağımsız host adayı işlenebilir. Bir sonraki manuel
indirme yeni iştir. Başlatılmış en fazla dört ikon isteği kendi yanıtını
tamamlayabilir; global rate-limit veya kullanıcı iptali yeni işleri durdurur.
401/429 global durdurma korunur; engellenen adresin içeriği scrape edilmez,
kimlik/URL tahmin edilmez, bot engeli aşılmaz. 404/403/kaynaksız sayaçları ayrı.
Alternatif başarıyla indirildiyse eski hata kodu başarılı kayda taşınmaz.

Testler: 403 host reddiyle farklı sağlayıcının ilerlemesi, aynı host'a ikinci
isteğin engellenmesi, 429 global stop ve başarılı alternatifin temiz provenance'ı.
Mock PNG kullanılır; gerçek oyun kapak kapsamı veya canlı sağlayıcı izni kanıtı
değildir. Kullanıcı dosyaları, arşiv, edisyon kimlikleri ve mevcut onaylar korunur.
