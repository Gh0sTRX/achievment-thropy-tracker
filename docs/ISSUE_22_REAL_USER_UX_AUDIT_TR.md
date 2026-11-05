# Issue #22 — v0.16.1 gerçek kullanım düzeltmeleri

5 Kasım 2026. Bu belge kaynak PR'larını anlatır; yeni kurulum sürümü yayımlanmadı. Gerçek kullanıcının Windows deneyimindeki sorunlar Issue #22'den alındı. Özel arşiv, ekran görüntüsü, kimlik veya oturum bilgisi repoya eklenmedi.

## Teslim zinciri

- [#23 — Ortak başarım satırı ve kompakt görsel](https://github.com/Gh0sTRX/achievment-thropy-tracker/pull/23): `fix/22-achievement-universe` → `codex/public-profile-trophies`.
- [#24 — Gerçek görsel metrikleri ve onaylı zenginleştirme](https://github.com/Gh0sTRX/achievment-thropy-tracker/pull/24): #23 üzerine küçük fark, `fix/22-media-provenance`.
- [#25 — Hesap kurulumu, platform ayrımı, geçmiş ve veri koruma](https://github.com/Gh0sTRX/achievment-thropy-tracker/pull/25): #24 üzerine küçük fark, `fix/22-provider-setup-history`.

İnceleme sırası #23 → #24 → #25; sonraki PR tabanı önceki PR dalıdır, böylece aynı dosyaların bütün geçmişi tekrar değerlendirilmez. Hiçbiri birleştirilmedi. Main ve geliştirme dalı korunur; uygulama sürümü 0.16.1 kalır, publish marker kullanılmaz.

## Kök neden ve dosya düzeyinde sonuç

| Sorun | Kök neden / düzeltme | Dosyalar |
|---|---|---|
| Universe'de eksik metadata | Ayrı sade satır yerine Vault ile ortak bileşen; ikon, açıklama, gerçek tarih, kaynak, puan/kupa türü, ölçülen ilerleme, pin ve spoiler | `atlas/web/achievement_row.js`, `ultimate.js`, `inline.js` |
| İkon URL'si yokken yerel ikon kaybı | Uzak URL koşulu kaldırıldı; yerel önbellek önce denenir, sonra izinli uzak kaynak ve erişilebilir fallback | `app.js`, `artwork.py` |
| Tarih uydurma riski | AtlasModel güvenli tarih ayrıştırması; kilitlide tarih yok; tarih yok/geçersiz/belirsizse açık bilgi; yalnız gün varsa saat üretilmez; raw değer ayrıntıda korunur | `achievement_row.js`, `inline.js`, mevcut `dates.py` |
| Büyük boş hero | Decode edilen hero→banner→screenshot→kapak; kapak uyarlaması açık etiketli; görsel yoksa 36px alan ve neden açıklaması | `achievement_row.js`, `ultimate.css`, `visuals.js` |
| CSV görselleri | CSV resmî title ID, ikon ve açıklama sağlamaz. Gizli Xbox keşif kontrolleri görünür yapıldı; keşif HTTP rotası yanlışlıkla tam sync çağırıyordu, ayrıldı. Cihaz/edisyon/Title ID etiketli açık onay, SGDB ilk beş adayında kaynak ve hedef cihaz etiketi | `server.py`, `app.js`, `index.html` |
| Eksik metadata zenginleştirme | Yetkili Xbox hesabı ve seçili title/edisyon; isim/puan yalnız öneri, her başarım kimliği kullanıcı tarafından seçilip onaylanır. Profil/arşiv değişirse eski batch reddedilir; farklı hesaptan tarih alınmaz | `enrichment.py`, `server.py`, `achievement_row.js` |
| Yanlış medya sayaçları | Planlanan/işlenen kayıt; denenen/indirilen/önbellekte/kaynaksız/başarısız/engellenen/atlanan/durdurulan ayrı. Decode doğrulaması, 401/403/429 sınıflaması, dört ikonluk paralellik, güvenli retry/stop | `media_sync.py`, `artwork.py` |
| PSN/Steam kurulum engeli | Uygulama içi adımlar, resmî bağlantılar, PSN kendi yetkili oturum onayı, gizli alan, DPAPI, ayrı kaydet/test/eşitle; bağlantı testi kütüphane veya ücretli rehber çağırmaz | `accounts.py`, `provider_setup.js`, `settings.py` mevcut koruması |
| Platform karışması | Ayrı ad/kimlik/son erişim durumu ve platform etiketli işler. Kayıt varlığı oturum kanıtı değildir. Steam/PSN hata türü güvenli biçimde korunur | `accounts.py`, `pc.py`, `public_profiles.py`, `app.js`, `visuals.js`, `server.py` |
| Sarı bant / işlem gürültüsü | Global bant gizli, transfer yalnız Hesap & Veri içinde. Tamamlanan ayrıntılar Eşitleme Geçmişi'nde; dört başarısız oyun tam listelenir, ilk üç dışındakiler +N ile belirtilir. Bildirim alt köşede kısa | `provider_setup.js`, `inline.js`, `app.js`, `ultimate.css` |
| Eski uygulamalar oyun sayılması | Muhafazakâr tür sınıflaması, Oyunlar/Uygulamalar/Tümü filtresi; kayıt silinmez, uygulamalar oyun önerisine ve otomatik art indirmesine alınmaz | `catalog.py`, `recommendations.py`, `media_sync.py`, `ultimate.js` |
| Veri korunması | Aynı oyuncunun CSV kimlikleri API kimliğiyle sessizce değiştirilmez. Açıklama/ikon/raw tarih boş sağlayıcı yanıtıyla silinmez; not/pin/yerel görsel ve onaylı eşleşme korunur. Farklı ilk CSV oyuncusu reddedilir. Profil arşivinde pinler saklanır | `core.py`, `server.py` |
| Windows kabul | Paket içindeki gerçek WebView2 smoke testine PSN sihirbazı, gizli alan, global bant yokluğu, sentetik Universe açıklama/tarih/ikon öğesi/inline ve kompakt alan kontrolü eklendi | `desktop.py` |

CSV ve API'den aynı oyuna ait ayrı kimlikler varsa veri kaybetmemek için otomatik birleştirilmez; kapsamdaki kaynak kayıtlar ayrı kalabilir. Bu durum tam oyun/DLC sahipliği veya tekil oyun sayısı kanıtı değildir. Bağlayıcı kimlik/edisyon onayı olmadan otomatik kanonikleştirme yapılmaz.

## Görsel kapsamı: gerçek ve sentetik ayrımı

- **Gerçek gözlem:** Issue #22, kullanıcının sıfır kaydedilen görsel ve eksik kapak/ikon sorununu bildiriyor. Bu oturumda özel kullanıcı arşivi alınmadı; gerçek hesapta önce/sonra yüzdesi ölçülmedi.
- **Sentetik sıfır-kaynak testi:** 1 CSV oyunu × 5 kategori + 1 başarım ikonu = 6 planlanan; 0 denenen, 0 indirilen, 6 kaynaksız. Bu başarısız indirme veya %100 kapsama diye sunulmaz.
- **Sentetik önbellek:** Uzak URL'siz geçerli yerel ikon 1 önbellekte, 0 yeni indirme olarak sayılır. Bozuk dosya önbellek sayılmaz.
- **Sentetik sağlayıcı varlıkları:** Beş kategori için test PNG'si döndüren mock sağlayıcıda 5 gerçek doğrulanmış yerel dosya oluşur; tekrar çağrıda ağ isteği yapılmaz. Bu dosya projenin işareti/test geometrisidir, oyun artwork'ü değildir.
- 401/403/429 ayrı engel; 404/bozuk MIME/görsel ayrı başarısızlık; stop ve yeniden deneme kontrol edilir. Sağlayıcı hatasının URL/anahtar içeriği rapora taşınmaz. Yerel kullanıcı dosyası korunur.
- Görsel Sağlığı gerçek decode edilmiş dosyaları, kaynak URL'lerini, kategori durumlarını ve son kontrol zamanını gösterir. Medya geçmişinde ilk 200 ayrıntı + tam sayaçlar tutulur; kesilme açık belirtilir. Profil hatalarının oyun listesi tamdır.

## Yerel doğrulama

- **201 Python testi** hedeflenen son tur (çıktı ve CI sonucu teslim kanıtında kesinleştirilir). Yeni dosyalar: `test_issue22_media.py`, `test_issue22_accounts.py`; önceki tarih/CSV/Xbox/PSN/Steam/restore/update testleri korunur.
- Dört Node suite ve `app.js`, `ultimate.js`, `ui/ultimate.js` ile yeni modüllerin syntax kontrolleri geçti.
- Gerçek Chromium, sentetik HTTP: `test_issue22_metadata.cjs`, `test_issue22_setup.cjs`; 1920×1080, 1440×900, 980×640, 390×844. Gerçek yerel ayar kaydı + mock PSN/Steam bağlantı yanıtı; sırların geri gösterilmemesi, ad/durum ayrımı, dört başarısız oyun/+1, app filtresi, gerçek cache ikonu, tarih/spoiler, inline odak, kapak/boş fallback.
- Mevcut Game Universe/back/forward/deep-link/not taslağı, Ctrl+K, 16 tema/ekran kombinasyonu, gzip/kısmi yenileme/yanıt sıralaması, gamepad API simülasyonu ve azaltılmış hareket geçti. Fiziksel gamepad/NVDA testi değildir.
- PowerShell native düğme eşlemesi geçti; Windows CI DPAPI, frozen native UI, kurulum, eski sürüm üzerine yükseltme/geri alma ve stok yayımlı uygulamanın güncelleme akışını ayrıca çalıştırır. PR build'i yayımlanmış güncelleme değildir.

Sentetik tek yerel ölçüm, gerçek internet eşitleme hızı değildir:

| Başarım | Gzip byte | Kütüphane çizim ms | Sıcak çizim ms | İlk arama ms | Oyun / arama DOM |
|---|---:|---:|---:|---:|---|
| 5.000 | 88.492 | 38,4 | 21,8 | 52,4 | 80 / 40 |
| 15.000 | 264.923 | 45,6 | 25,1 | 75,0 | 80 / 40 |
| 40.000 | 696.710 | 41,1 | 23,6 | 160,4 | 80 / 40 |

v0.16.1'in yaklaşık 697 KB / 40k ilk aktarım büyüklüğü korunur; değişmeyen kütüphanede dizileri yeniden göndermeyen protokol regresyon testi geçti. Önceki tek ölçüm ile CPU zamanından kesin hızlanma yüzdesi çıkarılmaz.

## Gerçek Windows / hesap kabul listesi — hâlâ kullanıcı ortamında gerekli

- [ ] İzinli gerçek Xbox hesabında Cold War / Asphalt 9 metadata ve cihaz/edisyon eşleşmesi.
- [ ] Kullanıcının mevcut 0.16.1 arşivinin kopyasıyla gerçek önbellek/kaynak kapsamı ve pin/not/tarih karşılaştırması.
- [ ] Kendi yetkili PSN oturumuyla süresi dolma/özel profil ve PS3/PS4/PS5/Vita gerçek kabulü.
- [ ] Gerçek Steam anahtarıyla görünür/gizli oyun ayrıntıları ve 401/403/429 kabulü.
- [ ] Fiziksel gamepad, NVDA, Windows oturum açma ve güç kesintisi.

Anahtarsız/oturumsuz üçüncü taraf profillerinin bütün verisini getirme vaadi verilmez. Steam OpenID özel veriye erişim sağlamaz. PSNAWP resmî Sony OAuth değildir. Windows imzası/SignPath onayı bu görevle çözülmüş sayılmaz. Artwork lisansı/kapsamı her sağlayıcıya bağlıdır; yeni scraping veya yapay oyun görseli yoktur. Ücretli rehberler açıkça seçilmedikçe kapalıdır.

## Teslim kanıtları

Son CI koşuları ve kalan başarısızlıklar burada doğrulandıktan sonra kaydedilir. Kaynak kod hazır olması canlı entegrasyonun çalıştığı kanıtı değildir.
