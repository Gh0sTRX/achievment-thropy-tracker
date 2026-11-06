# Xbox oturum yenileme yarış durumu

## Doğrulanan kök neden

`authenticated_client` token dosyasını SDK yenilemesinden önce kilitsiz
okuyordu. Hesap bağlantı testi, profil eşitlemesi ve kimlik keşfi farklı HTTP
iş parçacıklarından aynı dosyaya erişebiliyor. Üç iş parçacıklı mock SDK testi
önce başarısız oldu: her yenileme aynı `0` neslini okuyup `1` kaydetti; beklenen
son nesil `3` idi. Sabit `.pending` yolu da uygulama içi yazarlarda ortaktı.
Bu test gerçek token kullanmaz veya token içeriği yazdırmaz.

## Düzeltme

Süreç içi threading.Lock, yalnız dosyayı okuma → SDK refresh → XUID kontrolü →
atomik kaydetme aralığını sıraya alır. Her bekleyen işlem dosyayı kilidi aldıktan
sonra okur. Aynı uygulamanın ayrı asyncio.run döngüleri bulunduğundan asyncio.Lock
kullanılmaz. Beklerken asenkron kısa aralıklarla iptal kontrol edilir; thread
event loop'u bloklanmaz. Hata/iptal sonrası yalnız sahip olunan kilit bırakılır.
Başarım/oyun API sorguları başlamadan kilit bırakılır; tüm sync seri yapılmaz.

## Testler ve sınırlar

Dört mock regresyon: paralel üç thread/güncel token; ağ hatasında dosyayı koruma
ve aynı süreçte yeniden deneme; iptal edilmiş bekleyicinin başkasının kilidini
bırakmaması; API context'i açıkken ikinci refresh'in çalışabilmesi.

Gerçek Microsoft/XSTS veya refresh-token rotasyon politikası test edilmedi.
Bu, kullanıcının offline→online hatasının tek/kesin nedeni değildir. Dış SDK/CLI
süreçleri bu süreç içi kilide katılmaz; kullanıcı hesap değiştirme, token süresi,
servis rate-limit ve gerçek kimlik kabulü hâlâ ayrıca doğrulanmalıdır. Aktif
refresh isteğini zorla kesme veya otomatik hesap değiştirme eklenmedi.
Kişisel arşiv ve ayarlar migrasyonu yok; ücretli servis çağrısı yok.
