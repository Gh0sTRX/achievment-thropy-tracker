# Oyun görselleri — 0.9

Bu sürüm mevcut Python/yerel HTTP uygulamasını korur. Yeni bir arayüz çatısına
geçilmedi. Kaynak kataloğu kullanıcının onayladığı COMMUNITY_ART_SOURCES.json
dosyasından gelir; katalog, her sağlayıcının güncel erişimini veya görsellerin
yeniden dağıtım iznini doğrulayan bir lisans değildir.

## Kendi wallpaper'ını kullan

1. Xbox veya PlayStation sekmesini seç.
2. Oyun Görselleri ekranında gerçek kütüphanendeki oyunu seç.
3. Görsel türünü seç: geniş arka plan, kapak, logo, banner veya ekran görüntüsü.
4. Bilgisayarımdan görsel seç düğmesinden PNG/JPEG/WebP dosyanı aç.
5. Gerekirse odak sürgüleri ve atmosfer seçeneğiyle yerleşimi ayarla; kaydet.

Dosya en fazla 8 MB / 16 megapiksel / 8192 piksel kenar uzunluğunda olabilir.
Gerçek dosya yapısı doğrulanır; animasyonlu veya bozuk görseller reddedilir.
Görseller en fazla 2560 piksele indirilip WebP olarak yerel önbelleğe kaydedilir.
EXIF yönü düzeltilir; EXIF metadata aktarılmaz. AI üretimi, genişletme veya
karakter ekleme yapılmaz. Metin gölgeleri, crop odağı ve tonlama CSS katmanıdır.

Yerel görseller eşitleme ve yeniden başlatma sonrasında korunur. Sıfırla,
seçtiğin kategoriye ait özel görseli kaldırır; varsa önceki API görseline döner.
Kaynak, sağlayıcı kimliği, kaynak bağlantısı, kullanım notu, boyut ve kayıt
zamanı metadata olarak saklanır. Çevrimdışıyken yerel önbellek kullanılabilir.
Düşük bellekli cihazlarda ortam arka planı kapatılır; azaltılmış hareket
tercihi animasyonları kapatır.

## Kaynaklar

Panelde 11 kaynak, yayıncı/mağaza/topluluk/veritabanı/retro grupları altında
listelenir. SteamGridDB dışındaki kartlar keşif bağlantılarıdır; otomatik
indirme entegrasyonu oldukları iddia edilmez. SteamGridDB aramasında seçilen
oyun ve sürüm oyuncu tarafından onaylanır. Başka platformun AppID'si mevcut
Xbox/PSN kimliğine yazılmaz. Yerel dosya otomatik bir topluluk sonucu tarafından
sessizce değiştirilmez; önce sıfırlama gerekir.

Xbox Gamerscore ve PlayStation kupa sayıları ayrı gösterilir. PC sağlayıcısı
planlanıyor durumundadır. Kaynak ikon sağlamadıysa yerine başka kupa ikonu
kullanılmaz; eksik görsel alanı gösterilir.

## Bağımsız önizleme

preview/atlas-cinematic-standalone.html tek başına açılabilir. CSS/JS ve kaynak
listesi dosyanın içindedir. Kendi wallpaper'ını seçebilirsin. Dosya sunucuya
gönderilmez ve sayfa kapatılınca seçimi kaybolur. Gerçek hesap bağlantısı,
oyun kütüphanesi veya ilerleme ölçümü içermez. Önceki v2 tasarım dosyaları ve
REAL_ART_SOURCES.json bu oturumda sağlanmadığından hayali 12 oyun eklenmedi.

Kurulum paketi ticari oyun görselleri içermez. Windows markalama ikonu,
uygulamanın mevcut altıgen/A işaretinden oluşturulmuştur.
