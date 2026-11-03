# Achievement Atlas — Cinematic UI 2.1 / Gerçek görsel kaynakları

## Hedef
Önceki sinematik UI v2 tasarımını temel al. Xbox / PlayStation / PC seçimine göre oyuncunun **gerçek oyunlarından gelen görsellerin** her sayfada atmosfer oluşturmasını sağla. Yapay zekâ tarafından üretilmiş görsel veya uydurulmuş oyun karakteri kullanma.

Mevcut veri işlevlerini (TrueAchievements CSV, OpenXbox deneysel bağlantı, öneriler, pin, ikon önbelleği, yerel HTTP sunucu) KORU. Uygulamayı sırf görsellik için yeni framework'e göç ettirme. `atlas/web/index.html`, `style.css`, `app.js`, `atlas/artwork.py`, `atlas/server.py`, `atlas/core.py` üzerinden mümkün olan en az değişikliği yap.

## Yeni paket dosyaları
- `spec/COMMUNITY_ART_SOURCES.json`: gerçek araştırılmış 11 görsel kaynağı ve erişim koşulları.
- `spec/REAL_ART_SOURCES.json`: 12 demo oyun için önceki Steam CDN adresleri. Aday URL'lerin hepsi tek tek doğrulanmış değildir.
- `preview/index.html`, `ui.css`, `ui.js`: v2.1 kaynak keşfi panelli sinematik önizleme.
- `preview/atlas-cinematic-standalone.html`: tek HTML dosya (CSS/JS gömülü).
- `assets/achievement-atlas.ico`: Windows EXE markası.

## Gerçek görsel arama/önbellek stratejisi
1. Oyunun platformu ve sürümünü doğru eşleştir: Xbox 360/One/Series, PS3/4/5, Steam/GOG/Epic gibi sürümler farklı olabilir. Eşleşme kararını oyuncuya doğrulat; Steam AppID farklı platformların title ID'si değildir.
2. Kullanıcının seçtiği yerel görsele ilk önceliği ver. Yoksa resmî fan kit, Xbox/PlayStation tanıtım sayfaları veya mağaza görseli. Sonra SteamGridDB kullanıcı seçim paneli, izinleri doğrulanmış topluluk kaynakları, en sonda görselsiz degradeli arka plan. Kaynakları sabit bir siteye kilitleme.
3. `hero`, `cover`, `logo`, `banner`, `screenshot`, `achievement icon` kategorilerini ayrı kaydet; `LocalAppData/AchievementAtlas/artwork/` altında oyun ID'ye göre cache'le. Boyut/dosya türü/bozuk dosya kontrolü ve değiştir/sıfırla komutları ekle.
4. Orijinal görsele AI üreteci / AI genişletme / karakter ekleme uygulama. Yerleştirme, crop, gradient overlay, blur ve parlaklık tonlaması CSS ile yapılabilir. Gerçek görsele uygun safe zone bırak; yüzleri ve logoları rastgele kesme.
5. Tema seçimini sadece yeşil/mavi renge bağlama. Oyunun atmosferini belirleyen hero görseline göre vignette, text contrast, accent (örneğin Gears koyu kırmızı, Halo soğuk yeşil, Forza parlak turuncu, God of War buz mavisi, Ghost of Tsushima kızıl/siyah) uygula. Görseli hem ana bannerda hem çok düşük opaklıklı ambient background'da kullan.
6. Başarım ikonlarını yalnızca gerçek kaynaktan gelen URL varsa göster. PSN için bronz, gümüş, altın, platin kategorilerini (gerçek veri varsa) destekle; örnek veriden sahte platin üretme.
7. Xbox/PS/PC verilerini tek istatistikte karıştırma: Gamerscore PSN kupa puanı değildir, Steam achievement ayrı kategori. Tema UI çalışırken sağlayıcı bağlantıları yoksa `Planlanıyor` olarak göster.
8. Site başlıklarını/limitlerini aşmak için engel atlatma yok. Resmî API key gerekiyorsa kullanıcının anahtarını iste, anahtarı istemciye gömme. Görsel atfı/source_url/rights_note/provider_id'yi metadata olarak sakla. Telif durumunu aşırı garantileyen ifade kullanma. Kamuya açık repoya görüntüleri zorla commit etme.
9. Windows EXE oluşturuluyorsa `achievement-atlas.ico`yu packager'a bağla. Uygulamanın başlığında artık yalnızca Xbox yazmasın.
10. Aşağıdaki testleri koru/ekle: `python -m unittest discover -s tests -v`, `node --check atlas/web/app.js`; platform switch, boş/bozuk görsel, bulunamayan oyun, yanlış sürüm, çevrimdışı cache, erişilebilirlik, düşük RAM koşulları.

## Kaynak ayrımları
- **Xbox resmî:** https://www.xbox.com/tr-TR/wallpapers — Halo / Gears / Forza için Xbox'ın gerçek wallpaper galerisi.
- **PlayStation resmî:** https://www.playstation.com/tr-tr/god-of-war/community/ — God of War Ragnarök wallpaper, logo ve banner fan kitleri.
- **PC resmî/mağaza:** Steam Store ve kullanıcının seçtiği ürün.
- **Çok platformlu topluluk:** SteamGridDB, LaunchBox Games Database, IGDB.
- **Homebrew/retro:** Libretro thumbnails, EmuMovies, GameTDB, ScreenScraper.

**Önemli:** Açık kaynak kodun MIT lisansı, kaynaklarına ait olmayan oyun görsellerine otomatik lisans vermez. Kaynaklar erişilebilir olsa bile görsellerin yeniden dağıtım koşullarını ayrıca değerlendir.

## Kabul kriterleri
- Önizlemenin görünümü sinematik v2'den geriye gitmesin; görsel stüdyosunda 11 kaynak gruplara ayrılarak bağlantılarıyla görünür olsun.
- Oyuncu tek tıkla kendi yerel wallpaper'ını seçebilsin ve o oyun için görsel önizlemesi değişsin.
- Önizleme gerçek hesap entegrasyonu varmış gibi davranmasın; yalnız tasarım demosu kalsın.
- Sırf tema için gerçek veriler, başarımlar veya kimlik bağlantıları zarar görmesin.
