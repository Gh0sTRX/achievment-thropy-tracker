# Achievement Atlas 0.16.2 Development — Türkçe Kurulum

Güncelleme: uygulama → Diğer ekranlar → Güncellemeler → Kontrol et → İndir →
Kur ve yeniden başlat. [0.16.2 değişiklikleri ve sınırlar](docs/RELEASE_NOTES_0_16_2_TR.md).

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

## İndirme, gizlilik ve kod imzalama

Windows EXE sürümleri [GitHub Releases](https://github.com/Gh0sTRX/achievment-thropy-tracker/releases) üzerinden yayımlanacaktır. SignPath Foundation başvurusu **gönderildi fakat henüz onaylanmadı**. Elle yüklenen EXE, geçerli bir dijital imza doğrulanmadıkça **imzasız** kabul edilmelidir. SignPath imzası için doğrulanabilir GitHub Actions sürüm derlemesi ayrıca hazırlanmalıdır.

- [**Code signing policy / Kod imzalama politikası**](CODE_SIGNING_POLICY.md)
- [**Privacy Policy / Gizlilik politikası**](PRIVACY.md)
- [Security / Güvenlik bilgileri](SECURITY.md)

**Onay sonrasında kullanılacak atıf:** Free code signing provided by SignPath.io, certificate by [SignPath Foundation](https://signpath.org/).

Her sürümün GitHub Release açıklamasında politika bağlantıları ve o EXE'nin gerçekten imzalı mı imzasız mı olduğu açıkça belirtilmelidir.

## Test

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

## Uygulama içi güncelleme

0.12'den itibaren geliştirme kanalı etkindir. Windows sertifikası yerine GitHub
OIDC/Sigstore derleme kökeni kanıtı ve SHA256 doğrulanır. Yalnız belirlenmiş
depo/workflow/dallar kabul edilir. İlk 0.12 kurulumu bir kez yapılmalıdır;
sonraki güncellemeler uygulamadaki Güncellemeler ekranından yapılabilir.
Bu, ilk indirmedeki Chrome/SmartScreen uyarısını kaldırmaz ve OS korumalarını
atlatmaz. Ayrıntılar: [Güncelleme kanalı](docs/UPDATES_TR.md).

## 0.13 Ultimate arayüzü

Atlas Hub, üç kütüphane düzeni, sağdan açılan başarım detayı, Hedef Panosu,
Koleksiyon Müzesi ve yerel oyuncu profili eklendi. Tema rengi ile veri filtresi
ayrıdır; Xbox 360 / Windows / mobil ve PS3 / PS4 / PS5 / Vita kimlikleri korunur.
Görsel Stüdyosu kapak, hero ve logo seçimiyle odak/karartma/bulanıklık ayarlarını
cihazda saklar. Gerçek oyun görselleri dağıtıma gömülmez.

0.12 Setup kuruluysa **Güncellemeler → Güncellemeyi indir → Kur ve yeniden başlat**
yoluyla 0.13 alınabilir. [Uygulama ve doğrulama raporu](docs/ULTIMATE_IMPLEMENTATION_TR.md).

## 0.14 / Ultimate V5

Üstteki **Atlas Ultimate** düğmesi Cinematic / Blades / NXE / XMB görünümünü açar.
Kupa ayrıntıları her iki arayüzde de satır altında açılır. İşlem durum çubuğundan
profil/görsel/rehber indirmeleri durdurulabilir. **Tam yenile**, kısa süreli
kupa önbelleğini kullanmadan sorgular. [Değişiklikler ve testler](docs/ULTIMATE_V5_INTEGRATION.md).


## 0.14.1 — V5.1 bakım güncellemesi

- Otomatik Türkçe rehber üretimi **varsayılan kapalıdır**. Brave ve OpenAI servislerinin otomatik kullanımı için açık izin gerekir. Elle rehber başlatma ayrıdır ve servis kullanımı maliyet oluşturabilir.
- Eski kütüphane migrasyonu öncesi yedekleme; bozuk JSON'da fail-closed açılış; API durum/revision tutarlılığı; güvenli tarih ayrıştırma ve artwork crossfade/fallback düzeltmeleri.
- Xbox/PSN canlı profil sorgulama servis oturumu gerektirir ve gerçek hesapta uçtan uca doğrulanmış değildir. PC/Steam hesabı bağlama henüz yoktur.
- Yayın kanalı: **development prerelease**, Windows Authenticode imzası garanti değildir. GitHub/Sigstore köken kanıtı uygulamanın kendi güncelleme doğrulaması içindir, Windows yayıncı sertifikası değildir.

[0.14.1 sürüm notları](docs/RELEASE_NOTES_0_14_1_TR.md) · [V5.1 denetimi](docs/ATLAS_V5_1_INTEGRATION_AUDIT_TR.md)


## Birleşik yerel temalar ve Foundation (0.15.0 Preview)

PR #4 ve PR #5, `integration/atlas-v015` dalında birleştirildi; ikinci Atlas Ultimate uygulama katmanı devre dışı bırakıldı. Cinematic, 360 Blades, 360 NXE ve PS3 XMB görünümü asıl masaüstü arayüzünün üst çubuğundan seçilir. Her tema aynı Atlas Hub, Oyun Kütüphanesi, Başarım Kasası, Hedef Panosu, Koleksiyon Müzesi, Zaman Çizelgesi, Oyuncu Profili, Oyun Görselleri ve Güncellemeler ekranlarını biçimlendirir. Platform filtresi ve renk kimliği temalardan ayrıdır. Console Mode, `Alt+C` veya üstteki düğmeyle açılan tek bağımsız tam ekran deneyimdir. Bu 0.15.0 Preview derlemesi GitHub Release'te yayımlanmış sürüm değildir. Hesap & Veri ekranında doğrulamalı JSON dışa aktarma / geri yükleme vardır. Normal library/state kayıtları çökme kurtarma günlüğü kullanır; Xbox/PSN kimlikleri kalıcı sağlayıcı ID'siyle ayrılır; tema/sekme/oyun geçişleri hareket azaltma ayarına saygılıdır. Gerçek Windows 0.14.1→0.15.0 yükseltme/rollback, fiziksel gamepad ve gerçek Xbox/PSN testi henüz ayrıca yapılmalıdır. 

[Foundation teknik planı](docs/V015_FOUNDATION_PLAN_TR.md) · [Arşivleme](docs/V015_ARCHIVE_RECOVERY_TR.md) · [Kimlik, journal, animasyonlar](docs/V015_IDENTITY_STORAGE_MOTION_TR.md)
