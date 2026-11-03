# Kullanıcı adıyla Xbox / PlayStation takibi

Oyuncu **Hesap & Veri → Kullanıcı adıyla kupa getir** bölümünde platformunu seçip
Gamertag / Online ID girer. Microsoft veya Sony oturumu açması gerekmez.
Aynı isim iki platformda ayrı ayrı sorgulanır. Bu işlem hesap sahipliğini doğrulamaz;
herkese açık profil görüntülemesidir. Uygulama halen localhost üzerinde çalışır;
çok kullanıcılı bir internet servisi olarak yayımlanmış değildir.

## Veri servisini kuran işletmeci için

Herkese açık profil, anonim API anlamına gelmez. Sunucu tarafındaki sağlayıcı için
işletmeciye ait bir servis oturumu gerekir. Anahtarları veya oturum dosyalarını
kaynak koduna, GitHub'a veya sohbete koyma. Ayarlar artık Hesap & Veri → İlk kurulum ekranından yerel olarak kaydedilebilir.
Windows sürümünde DPAPI ile Windows kullanıcısına bağlı şifrelenir. Diğer
sistemlerde dosya erişimi yalnız kullanıcıya açıktır. Ortam değişkenleri yerel
ayarlardan önceliklidir; .env otomatik yüklenmez.

### Xbox

- `pip install -r requirements-xbox.txt`
- İşletmeci kendi yetkili OpenXbox oturumunu önceden kurar (mevcut Microsoft ile
  bağlan akışı da kullanılabilir).
- `ATLAS_XBOX_TOKEN_FILE`: bu OpenXbox OAuth JSON dosyasının mutlak yolu.
  Uygulamada daha önce Microsoft oturumu açıldıysa kayıtlı OpenXbox oturumu
  otomatik kullanılır; bu alanı tekrar doldurmak gerekmez.
- Servis oturumu yenilenir; hedef oyuncu Gamertag üzerinden XUID'ye çözülür.
  Başarımlar servis hesabından değil **hedef XUID** üzerinden okunur.
- 360 ve yeni nesil oyun geçmişi ve başarımlar continuationToken ile sayfalanır.
  Erişim hatasında işlem durur ve eski kütüphane korunur.

### PlayStation

- `pip install -r requirements-psn.txt` (PSNAWP 3.x).
- `ATLAS_PSN_NPSSO`: işletmeciye ait servis hesabının NPSSO değeri; oyuncudan alınmaz.
- Oturum süresi ve erişim gereksinimleri için
  [PSNAWP dokümantasyonu](https://github.com/isFakeAccount/psnawp) esas alınır.
- Online ID → account ID çözülür. SDK tüm oyun/kupa sayfalarını, DLC gruplarını ve
  kazanılma durumunu okur. PSN'nin gizlediği oyunlar ve özel veriler getirilemez.
- Oturum yenileme PSNAWP tarafından yapılır; bu sürüm PSNAWP istemcisini işler
  arasında kalıcı tutmaz. Servis hesabının oturum yaşam döngüsü işletmecinin sorumluluğundadır.

Arayüzde **ayarlı** görünmesi yalnızca ortam değişkeninin varlığını gösterir;
başarılı yetkilendirme veya canlı doğrulama anlamına gelmez. Sağlayıcılar resmî
ortaklık API'leri değildir; erişim ve şemaları değişebilir.

## Özgün kupa görselleri

API'nin verdiği HTTPS ikon adresleri saklanır ve kasada görüntülenir. Görünen
ikonlar yerel önbelleğe alınabilir. Xbox / Microsoft ve PlayStation CDN alan
adları doğrulanır; sayısal Xbox 360 imageId değerinden adres uydurulmaz. Kaynak
ikon sağlamıyorsa arayüz genel yer tutucu gösterir. Tüm platformları, bütün
rehberleri ve görselleri eksiksiz kapsayan tek bir ortak havuz kullanılmaz.

## Otomatik Türkçe rehberler

İşletmeci `BRAVE_SEARCH_API_KEY` ve `OPENAI_API_KEY` ayarlar.
`ATLAS_GUIDE_MODEL` isteğe bağlıdır; varsayılan `gpt-4.1-mini`.
Bunlar ücretli servislere istek gönderebilir: her yeni kupa için bir web araması ve
bir model isteği yapılır. Anahtarlar ayarlıysa ve kullanıcı otomatik rehber seçeneğini açmışsa profil
eşitlemesinden sonra tüm kupalar için otomatik araştırma başlar. Bu seçenek
varsayılan kapalıdır. İşlem ekrandan durdurulabilir; devam eden istek tamamlanır. Eksik rehberler oyun detayından tekrar
hazırlanabilir. İşlemler sırayla çalışır; ilk servis hatasında durur.

Arama sonuçlarının kısa alıntıları ve API kazanma koşulu üzerinden Türkçe çeviri
ve kısa adımlar üretilir. Tam rehber sayfaları indirilip kopyalanmaz. Başlık, URL,
üretim zamanı ve model kaydedilir. Model çıktısı **yapay zekâ özeti** olarak
etiketlenir; canlı olarak doğrulanmış rehber sayılmaz. Kaynak yetersizse adım
listesi boş kalabilir. Bir kaynak bağlantısı olması, modelin her adımının doğru
olduğunu garanti etmez. Süre/zorluk/sunucu durumu uydurulmaz.

**Bu oyunu tamamla** düğmesi yalnızca eksik kupaları ve kayıtlı Türkçe notları
listeler. Ölçülen ilerlemesi yüksek kupalar öne çıkar. Zorluk kanıtı olmadan
"en kolay" iddiası yapılmaz; bu sürüm doğal dil sohbet botu içermez.

## Yerel kayıt ve sınırlar

- Tam profil başarıyla alınınca aktif platform kayıtları değiştirilir. Diğer
  platform korunur. Eski demo kayıtları uygulama açılışında kaldırılır.
- Farklı oyuncuların kazanımları birleştirilmez. Aynı oyuncunun daha önce
  kazanılmış kupaları geri alınmaz.
- Başarılı profiller uygulamanın veri klasöründe `profiles/` altında saklanır;
  eski kullanıcı adı yeniden sorgulandığında kazanımları/notları geri yüklenir.
- Kayıtlar yerel JSON dosyalarıdır. Kullanıcı adıyla arşiv oluşturulduktan sonra CSV aktarımı engellenir;
  CSV yolu için ayrı bir veri klasörü kullanılır.
- API 401/403/429 veya ağ hatasında erişim kontrolünü aşma denenmez. Eksik oyun
  listesi başarı gibi sunulmaz; ancak sağlayıcının gizlediği veriler saptanamaz.

## Doğrulama

`python -m unittest discover -s tests -v`

Sağlayıcı testleri sahte ağ/SDK yanıtları kullanır. Gh0sTRX55 için canlı kupa
listesi bu ortamda doğrulanmadı: servis kimlik bilgileri yok; hedef oyun API
alan adları mevcut ağ izin listesinde bulunmuyor. Bir kullanıcının gerçek oyun/ilerleme
verileri örnek veri diye kaynak koduna eklenmedi.
