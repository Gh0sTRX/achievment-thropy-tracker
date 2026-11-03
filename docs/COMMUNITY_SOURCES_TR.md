# Kaynak incelemesi ve 0.7 düzeltmesi — 3 Kasım 2026

Ekran görüntüsündeki DEEP BLUE, PIXEL VALLEY, ORBITAL RANGER ve NIGHT DRIVE,
önceki sürümün `make_sample` işlevinden geliyordu. Bunlar Xbox hesabından
çekilmemişti. Microsoft oturumu açılmış görünmesine rağmen gerçek oyunları
içe aktaran bir işlem otomatik başlamıyordu. 0.7 sürümünde üretim kodundan
örnek veri kaldırıldı; bu işlev yalnız testlerde tutuluyor. Eski örnek kayıtlar
yedeklenip aktif kütüphaneden kaldırılır; gerçek kayıtlar ve oturum korunur.

## TrueAchievements ve benzerleri

- https://www.trueachievements.com/gamer/Gh0sTRX55 — araştırma aracından erişilemedi.
- https://www.trueachievements.com/help/ — araştırma aracı 402 yanıtı aldı.
- https://www.truetrophies.com/ — araştırma aracı 403 yanıtı aldı.

Bu inceleme sitelerin içeriklerini başarıyla okuyup API sözleşmelerini
doğrulamaya yetmez. Bu nedenle anonim ve eksiksiz bir TrueAchievements API'si
varmış gibi entegrasyon eklenmedi. Erişim engellerini aşma denenmedi.

TrueAchievements CSV aktarımı mevcut sütun sözleşmesiyle desteklenir. Gerçek
CSV dosyası kullanıcının kendi dışa aktarımıdır. Xbox/PSN API'sinden gelen
kazanılma durumu, topluluk rehberleri ve yapay zekâ notları ayrı tutulur.
Başarımlarda veri kaynağı gösterilir; ad/puan/kazanılma durumu model tarafından
üretilmez. TrueAchievements/TrueTrophies için oyun ve başarım adıyla rehber
arama bağlantısı verilir. Arama bağlantısı o sitenin içeriğinin indirildiği
veya bulunan rehberin doğrulandığı anlamına gelmez.

## Canlı Xbox akışı

Microsoft oturum açılışı → profil/XUID doğrulama → otomatik oyun geçmişi ve
başarım eşitlemesi → başarılı tam yanıtın yerel kütüphaneye kaydı → ana merkez.
Aynı oturum kullanıcı adıyla herkese açık hedef sorgulamada da kullanılabilir;
kullanıcıya tokens.json yolunu tekrar yazdırmaz. Kayıtlı oturum uygulama yeniden
açılınca yenilenmeye çalışılır. Hata veya boş yanıtta örnek veri gösterilmez;
ana merkez hata nedenini ve mevcut kayıt durumunu gösterir.

Gh0sTRX55'in cihazındaki oturuma bu geliştirme ortamından erişilemiyor. Bu
hesabın gerçek ilerlemesi uzaktan doğrulanmadı. Otomatik akış, sayfalama ve
veri bütünlüğü regresyon testleriyle kontrol edilir.

## Ek kaynak kontrolü

https://www.xboxachievements.com/ ana sayfası okunabildi. Sayfada Xbox Series,
Xbox One ve Xbox 360 için ayrı başarım listeleri ve rehber bölümleri bulunuyor.
Bu, genel başarım kataloğu/rehber kaynağı olabileceğini gösterir; bir oyuncunun
kişisel kazanılma durumunun anonim olarak sunulduğunu kanıtlamaz.
Black Ops II rehber adresine yapılan istek 403 döndürdü; içeriği doğrulanmadı.
PSNProfiles ve Exophase üzerinde Gh0sTRX55 profil adresleri de araştırma
aracından okunamadı. Bu sitelerden hesap verisi indirildiği iddia edilmez.
