# Atlas v0.15 — Yerel Arşiv ve Kurtarma (Foundation dilimi)

**Durum:** PR #5 geliştirmesi, yeni bir release değildir. `main` ve v0.14.1 Development kurulumu değişmedi.

## Kullanıcı akışı

**Hesap & Veri → Yerel arşiv · yedekle / geri yükle**

- **Arşivi dışa aktar:** O anda etkin `library.json` içeriği ve izinli `state.json` alanları tek bir JSON dosyasına indirilir; oyun/başarım ID’leri, kaynak/edition bilgisi, gerçek kazanım tarihleri ve kullanıcı tercihleri korunur.
- **Yedekten geri yükle:** Kullanıcı bir Atlas JSON arşivi seçer, mevcut verilerin değişeceği konusunda onay verir. Önce biçim, SHA-256, oyun/başarım anahtarları, platform bağları ve kayıt sınırları kontrol edilir. Hatalı dosyalar diske yazılmaz.
- **Önceki kaydı kurtar:** Restore işleminden **önce** `<veri klasörü>/recovery/pre-restore-*.json` oluşturulur. İşlem iki JSON arasındaki yazmada yarıda kalırsa `.atlas-restore-pending.json` işaretçisiyle sonraki açılışta eski kayıtlar geri yazılır. Kullanıcı kurtarma dosyasını silmemelidir.
- **Güvenlik:** Servis tokenları/ayarları, OAuth/NPSSO bilgisi, medya/ikon önbelleği ve geçmiş profil `profiles/` dosyaları taşınmaz. Dışa aktarılan JSON yine de gamertag, Online ID, achievement ilerlemesi ve notlar gibi **kişisel veriler** içerir; herkese açık GitHub deposuna konulmamalıdır.

## API

- `POST /api/archive/export` — mevcut kaydın veri arşivini döndürür. Gövde `{}`; Host/Origin ve `X-Atlas-Token` zorunlu.
- `POST /api/archive/restore` — `{"archive": <export sonucu>}` kabul eder. Açık UI onayı istemci tarafındadır; servis son bütünlük doğrulamasını her koşulda tekrar yapar.
- Diğer istekler için mevcut 12 MB sınır korunur. Restore isteği için 50 MB; arşivin kanonik veri kısmı için 48 MB sınırı uygulanır.

## Test kapsamı

`tests/test_archive.py`: round-trip, veri kapsamı, token alanlarını dışlama, hash bozulması, farklı platform bağı, tekrarlı ID, yerel rollback, yarım kalan restore sonrası başlangıç onarımı, HTTP token zorunluluğu ve etkin senkronizasyon sırasında restore engeli.

`tests/test_foundation_ui.cjs` ve GitHub Actions, shell derlenmesini ve yeni arayüz bağlarını korumalıdır.

## Bilinçli sınırlar

Bu dilim **yalnızca arşiv geri yüklemesinin** iki JSON dosyalı işlemini kurtarma kaydıyla korur; uygulamanın diğer bütün `save()` yolları henüz tam transaction günlüğüne taşınmadı. Hesap/oturum tokenları taşınmadığından yeni cihazda servisler yeniden doğrulanmalı. Geçmiş `profiles/` dosyaları ve yerel artwork cache bu arşivin parçası değildir. Anlık backup, başarımın API’de güncel olduğu garantisi değildir. Fiziksel Windows yükseltme/geri alma (0.13/0.14.1 → v0.15), güç kesilmesi testi ve büyük gerçek kullanıcı arşivinde elle test gereklidir.

## Sonraki adımlar

1. Bu değişiklikleri test/Windows installer sonucuna göre düzelt; büyük gerçek arşiv ve sürüm geçişi sınamalarını yap.
2. Xbox XUID / gamertag ve PSN account ID / Online ID kimliğini, CSV farklı edition ve DLC ayrımlarını doğrula.
3. Tüm kalıcı yazmaları versiyonlu snapshot/transaction modeline taşı.
4. Windows başarısız güncelleme ve rollback matrisini tamamla.
5. PR #4 ve #5'i doğru sırada incele; onaysız merge, development yayın ve `main` güncellemesi yok.
