# Steam bozuk satır ve hesap kapsamı

İki mock regresyon düzeltmeden önce hata verdi. Bozuk player achievement satırı
(string veya liste apiname) AttributeError/TypeError'a dönüşerek tüm eşitlemeyi
durduruyordu. Satır biçimi artık dict + dolu string apiname olarak doğrulanır;
geçersiz kayıt SteamError olur, yalnız o AppID failed_title_ids'e alınır. Aynı
hesabın önceki oyun kaydı korunur; diğer oyunların sonuçları işlenebilir.
401/403/429 ve iptal global durdurma davranışı değiştirilmez.

known_games koruması önce cache hesabına bakmadan eski game_id'leri kullanıyordu.
Hesap değiştirilince yeni hesabın boş başarımlı oyun şeması yanlışlıkla eski
başarımların kaybolması gibi yorumlanıyordu. Koruma artık yalnız aynı SteamID64
için uygulanır; hesap kimliği olmayan eski arşivler de güvenli tarafta kalmak
için korumayı sürdürür. Tam regresyondaki legacy schema testi bu ayrımı yakaladı,
test kaldırılmadan koruma düzeltildi. Başka hesabın kazanımı yeni hesaba taşınmaz; başarımı olmayan
oyun için sahte kazanım oluşturulmaz.

Testte iki AppID, bozuk satırın iki şekli ve farklı hesap cache'i var. Eski oyunun
kazanımı, unlock timestamp'i, notu ve pini korunur. Bunlar resmî API'ye karşı
mock yanıtlardır; gerçek Steam hesabı veya görünürlük kabulü değildir. Geçmiş
profil arşivleri, Steam AppID ve diğer platformlar korunur; migrasyon yoktur.
