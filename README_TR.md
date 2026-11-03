# Achievement Atlas 0.9 — Türkçe Kurulum

Windows 10/11 64 bit için hazır **Setup.exe** ve **Portable.zip** paketleri hazırlanır.
Hazır paketlerde Python kurman gerekmez. Arayüz Microsoft Edge WebView2 ile kendi masaüstü penceresinde açılır. Setup masaüstü/Başlat menüsü kısayolu ve
kaldırıcı ekler; portable sürümde klasörü çıkarıp AchievementAtlas.exe açılır.
Paketler imzasız ön sürümdür. Kurulumun ayrıntıları [KURULUM.txt](KURULUM.txt) içinde.

0.7 sürümü eski demo kayıtlarını otomatik temizler ve Xbox oturumundan sonra gerçek başarımları otomatik indirir. [Kaynak incelemesi ve düzeltme](docs/COMMUNITY_SOURCES_TR.md).

Kaynak kod ZIP için Python 3.11+ gerekir: `KUR_WINDOWS.bat` dosyasını çalıştır.
Bu betik uygulamaya özel `.venv` oluşturur, Xbox ve PSN bileşenlerini kurar ve
uygulamayı açar. Sonraki açılışlarda `BASLAT_WINDOWS.bat` kullanılır.

## İlk kullanım

Hesap & Veri ekranında platformunu seç, kullanıcı adını yaz ve **Profilimi yenile** düğmesine bas. Kayıtlı erişimler otomatik kullanılır. Teknik servis seçenekleri isteğe bağlı **Gelişmiş ayarlar** ekranındadır. Xbox / PSN için hedef
oyuncunun hesabını bağlaman gerekmez; işletmeciye ait bir servis erişimi gerekir.
**Paket hazır servis hesabı veya API anahtarı içermez.** Bunlar olmadan canlı
kupa sorgulaması çalışmaz; TrueAchievements CSV aktarımı kullanılabilir.
Mevcut Xbox oturumun varsa uygulama onu kullanır; oturum dosyası yolunu yeniden
girmen gerekmez.

Türkçe rehberler isteğe bağlı Brave Search ve OpenAI servislerini kullanır;
ücretli çağrılar yapabilir. Otomatik rehber varsayılan kapalıdır. Kaynaklar,
Türkçe notlar ve özgün kupa ikonları yerel saklanır. Oyun detayındaki **Bu oyunu
tamamla** eksik kupaları ve kayıtlı notları gösterir. Zorluk kanıtı olmadan
"en kolay" etiketi verilmez.

[Servis kurulumu, yerel veri ve sınırlar](docs/PUBLIC_PROFILES_TR.md)

Gh0sTRX55 hesabının gerçek verileriyle canlı eşitleme doğrulanmadı. Bu proje
Microsoft, Sony veya TrueAchievements ile ilişkili değildir.

## Geliştirici

`python -m unittest discover -s tests -v`

Windows paketi `.github/workflows/windows-package.yml` ile Windows üzerinde
üretilir. Derlenmiş uygulamanın HTTP arayüzü, SDK içe aktarımları ve DPAPI ayar
döngüsü test edilir; ardından kurulum ve kaldırma testi yapılır.

## Gerçek oyun görselleri

Oyun Görselleri ekranında kendi dosyanı oyununa ata; arka plan atmosferi, odak ve
tema otomatik/elle seçilebilir. 11 kaynak kartı erişim koşullarıyla listelenir.
SteamGridDB aramasında sürüm eşleşmesi onaylanır. Oyun görselleri pakete gömülü
değildir; PC sağlayıcısı planlanıyor olarak gösterilir.
