# Birikmiş PR teslimatı

## Console Mode CI regresyon takibi

f3d2a0d kaynaklı Unit tests 42234874945 / 42234866618 başarısız oldu:
`test_console_layout.cjs` seçilen oyunun kapağı olmadığını varsayıyordu.
CI sırasındaki önceki testler platform/seçili oyun tercihlerini kalıcı olarak
değiştiriyor; fixture içinde audit-game-1'in gerçek yerel test kapağı var.
Tek başına testin geçmesi tam test sırasının geçtiği anlamına gelmedi.

Test artık platform/cihaz/katalog filtresini ve oyun kimliğini açıkça seçer;
dört çözünürlükte kapaklı ve kapaksız oyunu ayrı doğrular. Kapaklı senaryoda
img complete/naturalWidth kontrolü de zorunludur. Odak, Escape ve kontrol
çakışması kontrolleri korunur. Üretim kodu veya güvenlik testi atlanmaz.
Fixture resmi Atlas uygulama simgesidir; gerçek oyun kapağı veya canlı kabul
olarak sunulmaz. Yeni exact-head CI sonucu ayrıca izlenmelidir.

Son takip: Kullanıcı tüm açık PR'ları kapatmayı tekrar istedi. #43 de kaynak
dalı korunarak, merge/release yapılmadan kapatılır. Bu belge bir tamamlanma
ilanı değildir; aşağıdaki gerçek hesap, artwork kapsama ve güvenlik eksikleri
açık kalır. Sonraki CI sonuçları branch SHA üzerinden izlenir.

PSN SDK oyun listesi iterator'ünde artık her yield'de iptal kontrolü ve bulunan
oyun sayısı progress'i var. İlk metadata isteği tamamlanmadan iptal edilemez;
rate-limit aşılarak paralel sorgu başlatılmaz. Bu, hız ölçümü yerine geçmez.
Console Mode aynı shell içinde belirgin gerçek kapak, okunaklı metin, akıştaki
alt kontroller ve mobil kaydırılabilir oyun şeridi kullanır. Olmayan kapak
üretilmez, hatalı kapak yüklemesinde img gizlenir. Yeni tema yoktur.

Kullanıcı 6 Kasım 2026'da açık PR birikimini kapatmayı istedi. Kodları tek tek
main veya geliştirme dalına körlemesine merge etmek yerine, son kaynak zinciri
ve #26 belgeleri tek inceleme PR #43 altında toplandı. Küçük commitlerin
geçmişi korunur; eski dallar silinmez. Yeni release veya sürüm artışı yok.

## İçerme kanıtı

| Önceki PR | Korunan kaynak / kapsam |
|---|---|
| #23 | 405664e — ortak Vault/Universe metadata, kompakt hero |
| #24 | 8ff03c6 — doğru görsel sayaçları ve açık metadata onayı |
| #25 | 9512d14 — provider setup/history ve native focus/history düzeltmesi |
| #26 | f562759 — kabul/devir belgeleri, yerel merge ile alındı |
| #38 | 1b78d07 — karışık PC profili offline archive koruması |
| #39 | da489e4 — ham JSON backup/restore ve hash koruması |
| #41 | dc577aa — tüm başarım çerçevesi, bağımsız pin |
| #42 | 3e008c4 — aynı edisyon kaynak adresinden cache recovery |
| #43 | d365609 — onaylı CSV TitleHub görsel kategorileri |

#1 geliştirme dalının main incelemesiydi; kapatılması kod silmez. #2 eski v5
dalıdır; eski dosyaları güncel kodun üstüne taşımak yok. Geliştirme tabanı
145accef, main 98f870b korunur. Birleştirme/yayın ayrıca yetki gerektirir.

## Kabul sınırları ve kalan öncelikler

1. Gerçek Xbox offline→online hatasının kök nedeni; yeniden başlatma çözüm kanıtı değil.
2. Kullanıcı arşivinde doğrulanmış kapak kapsamı; kod düzeltmesi kapsama ölçümü değil.
3. PSN ilk sync süresi, pagination/rate-limit/cancel ölçümü.
4. Yetkili Steam ve PSN gerçek hesap kabulü.
5. Console Mode düzeni ve fiziksel gamepad; yeni tema yok.
6. NVDA/ekran okuyucu fiziksel kabulü.
7. Alan bazlı provenance'ın eksik earned/date/DLC alanları.
8. Taşınabilir medya yedeği; JSON backup medya dosyalarını içermez.
9. Gerçek düşük donanım p95/RAM/CPU ölçümü ve bağımsız güvenlik incelemesi.
10. Yalnız doğrulanmış sinyallerden sınırlı Next Move; paid guides varsayılan kapalı.

Offline/online göstergesi özellikle ertelendi. Bu liste bitmiş özellik listesi
değildir. Sentetik test, native Windows CI ve gerçek hesap kabulü ayrı tutulur.

## Eşitleme sonrası hata ayrımı

Profil arşivi başarıyla kaydedildikten sonra görsel indirme başlatıcısı veya
isteğe bağlı rehber başlatıcısı hata verirse, kaydedilmiş profil artık bu nedenle
başarısız/erişimi bozulmuş olarak işaretlenmez. Hata ilgili media/guides geçmişine
gizli servis exception metni olmadan kaydedilir. Profil geçmişi ayrı kalır.
Profil geçmişi kaydı hata verse bile yeniden deneme kilidi finally ile bırakılır.

Yeni mock testi ağ hatası→aynı Controller ile yeniden eşitlemeyi, arşiv/not/pin
korunmasını ve hatadan sonraki verified durumunu kontrol eder. Diğer test iki
opsiyonel başlatıcıyı hata verdirerek hesap sonucunun bozulmadığını doğrular.
Bu, kullanıcının gerçek offline→online Xbox hatasının kök nedeninin bulunduğu
anlamına gelmez. Gerçek ağ/hesap kabulü hâlâ açık. Ücretli rehber tercihi değişmez.
