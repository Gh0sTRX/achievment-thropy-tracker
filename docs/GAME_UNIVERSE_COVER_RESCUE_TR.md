# Game Universe · tüm kütüphane kapak kurtarma

## Kapsam

Bu çalışma **Minecraft / Cold War / Asphalt'a özel değildir**. Xbox, PlayStation,
Steam ve yerel CSV üzerinden tutulmuş **tüm oyun/sürüm kayıtlarını** Game Universe
için ele alır. Kütüphanenin çok büyük olması nedeniyle eksikler 20 kayıtlık
sayfalarda gösterilir. Uygulama/servis kayıtları (Netflix gibi) oyun kapsamına
girmez; kullanıcı arşivinden silinmez.

## Uygulamada

**Oyun Görselleri → Game Universe · Tüm oyun kapaklarını tamamla**:
1. **Tüm kapakları tara:** Her oyunun yerelde açılabilen gerçek `cover`
   dosyasını say; eksik oyunları sıralı ve sayfalı göster. Sırf kaynak URL'si
   bulunması bir görselin indirildiği anlamına gelmez.
2. **Doğrulanmış kapakları indir:** Yalnız önceden eşleşmiş, güvenli HTTPS
   sağlayıcı URL'si olan kapakları tüm kütüphane için indir; mevcut kapakları,
   kullanıcı dosyalarını, hero/logo/banner ve başarım ikonlarını değiştirme.
   İşlem arka plandadır; sonra tekrar tara. 401/403/429 engelleri aşılmaz.
3. **Eşleştir / kapak seç:** Kaynaksız oyun için aynı yerel oyun kaydını
   görsel çalışma alanına yükle. SteamGridDB API anahtarı varsa oyunu ara,
   çıkan isimlerin *gerçek oyun/edisyon* olduğunu elle kontrol edip onayla,
   galeriden kapağı seç. Ya da kendi dosyanı seç. SteamGridDB araması otomatik
   yanlış isim/edisyon eşleşmesi yapmaz.
4. Game Universe içindeki Görseller sekmesinden **Tüm Game Universe
   kapaklarını yönet** düğmesi aynı envantere götürür.

## Gizlilik, güven ve garanti sınırı

- Veri kaynağı olmayan, adı benzer ama edisyonu farklı kayıt için resim uydurulmaz.
- Kullanıcının yerel kapak seçimi, önceki pin/notlar/kazanımlar korunur.
- Gerçek kapak kaynağı/API anahtarı olmayan kayıtlar toplu indirmeyle otomatik
  tamamlanamaz; gerekçeleri ve eşleştirme yolu görünürdür.
- Kullanıcının özel Windows veri klasörü ve gerçek hesapları bu geliştirme
  sırasında okunmadı. Kütüphanedeki **gerçek kapsama yüzdesi henüz ölçülmedi**.
- Görseller açık kaynak depoya paketlenmez veya yeniden dağıtılmaz.
- Bu branch Development Release değildir. Release/main değişikliği için ayrı
  kullanıcı onayı ve fiziksel cihazda kabul gerekir.

## Testler

`tests/test_game_universe_cover_queue.py`:
- 27 oyun ve üç sağlayıcıyla (Xbox/PSN/Steam) 20+6 sayfalama,
- cover-only indirmede diğer görsellerin ve ikonların korunması,
- Title ID uyuşmazlığı ve kullanıcı görselinin ezilmemesi.

`tests/test_cover_inventory_ui.cjs`:
- 20+6 eksik oyun sayfalama, genel toplam, seçili oyunun cover
  çalışma alanına yönlendirilmesi ve yalnız kapak indirme isteği.

Bu testler gerçek servis kapaklarını doğrulamaz; gerçek Game Universe arşivinde
tarama ve güvenli eşleştirme hâlâ Windows kabul adımıdır.
