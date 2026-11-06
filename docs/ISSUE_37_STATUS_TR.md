# #37 aşama durumu ve kapsam kapıları

6 Kasım 2026. Ürün: güvenilir offline arşiv + sınırlı hedef planlayıcısı. Kodun varlığı, mock, native CI ve gerçek kullanıcı kabulü ayrıdır. Main/development merge ve yeni Release yapılmadı; yayımlı sürüm 0.16.1 kaldı.

| İş | Durum | Kanıt / açık kapı |
|---|---|---|
| #22 ortak ikon/tarih/açıklama/satır | implemented, tested synthetic | #23/#24 CI başarılı; gerçek arşiv kapsaması ölçülmedi |
| Native history/focus | implemented, tested synthetic, tested native | #25 `9512d14`; Windows `42134533000`, unit PR `42134532809` başarılı; önceki `42107565658` hatası atlanmadı |
| Offline PC/mixed profil arşivi | implemented, tested synthetic | #38 `1b78d07`; 211 test; Windows `42135043746`, unit PR `42135043717` başarılı |
| Tarayıcı arşiv hash round-trip | implemented, tested synthetic | #39 `da489e4`; 215 test + gerçek UI indir/yükle akışı, Windows `42136068296`, unit PR `42136068478` başarılı |
| Tam fiziksel offline Windows | blocked / henüz tested real değil | Kullanıcı kendi Windows cihazında kopya arşivle test edebileceğini bildirdi; protokol hazır, sonuç bekleniyor |
| Xbox-first gerçek hesap | implemented adapter, tested mock, real acceptance blocked | Yetkili oturum bu ortamda yok; kullanıcının cihazındaki kabul ayrı yapılacak |
| Steam / PSN gerçek hesap | implemented adapter, tested mock, real acceptance blocked | Steam key/visibility ve yetkili kişisel PSN NPSSO/servis şartları gerekli; resmî Sony OAuth iddiası yok |
| Alan bazlı provenance | partially implemented | Kayıt kaynağı ve medya/icon metadata var; tüm alanlar için observed_at/precision/verification modeli tamamlanmadı |
| Taşınabilir tam medya yedeği | unimplemented | JSON export medya/credentials/profil geçmişini paketlemez; aynı klasörde medya hash koruması ayrı kanıt |
| Hızlı UX | partially implemented, tested synthetic/native | Arama/Universe/inline/back/keyboard/gamepad simülasyonu var; gerçek görev süresi, NVDA ve fiziksel gamepad kabulü bekler |
| Minimal Next Move #30 | unimplemented yeni MVP | Mevcut ratio/GS/description ağırlıklı önerici bu MVP sayılmaz. Önce arşiv/gerçek kabul; ardından yalnız pin/yakın tamamlama/gerçek tarih/belirsizlik, 1–3 açıklama |
| Güvenlik #32 | önlemler mevcut, bağımsız review unimplemented | Host/Origin/token/hash/DPAPI/image guard negatif testleri var; DNS/IP SSRF, fiziksel süreç tehdit modeli ve bağımsız inceleme tamamlanmadı |
| Performans #31 | tested synthetic kısmi | 5k/15k/40k, DOM sınırları, gzip/kısmi yenileme var; p95, RAM/CPU yüksek su işareti ve düşük donanım gerçek arşivi ölçülmedi |
| Windows dağıtım #33 | native CI kısmi kabul | Installer/update/rollback otomatik kontrolleri var; gerçek Windows 11/güç kesintisi/logon/AV kabulü ayrı, Authenticode yok |
| Açık kaynak sunumu #34 | planlandı | main README v0.5 / dev v0.16.1 farkı sürer; main/rename otomatik değiştirilmez |

## Bu tur çözülen kullanıcı problemleri

1. Başarıma programatik tıklama yanlış Vault rotasını ekliyordu; geri dönüş ve kart odağı bozuluyordu. Gerçek düğme anchor'ı ve render sonrası kimlikli odak geri yükleme düzeltildi. Windows native geçti.
2. Steam profili bulunan arşiv export veya restore recovery yedeği veremiyordu. Mevcut PC profili ve güvenli platform ad/uyarı alanları desteklendi.
3. Tarayıcı yedek dosyasını yeniden JSON'a çevirip 1.0→1/büyük sayı değişimiyle hash'i bozuyordu. Ham dosya indirme/restore; bozuk dosyayı tahmin edip geçirme yok.

## Kaynak ve inceleme sırası

#23 → #24 → #25; #25 üstüne #38 → #39. #26 yalnız güncel teslim/handoff belgeleridir; #25 üstünde kalır ve sonrasındaki bağımsız PR sonuçlarını referanslar. Hiçbiri otomatik birleştirilmedi. Geliştirme tabanı `145accef`, main `98f870b` korunur.

## Sonraki küçük işler / engeller

#39 Windows kapısı geçti. Sırada rızalı Windows/Xbox kabulü var. Sonra başarısız gerçek senaryoya göre küçük düzeltme veya alan bazlı provenance. Offline temel ve gerçek kabul kanıtı olmadan yeni Next Move/temalar büyütülmez. Kullanıcı kayıtları/credential rapora eklenmez. 30 saniye hedef bulma bir hipotezdir; süre veya kullanıcı faydası ölçülmedi.

## Doğrulanan son kaynaklar

- #25 `9512d149ae6e17b92cf01a4d1c6d8a380342ca5a`: Windows `42134533000` başarılı; 203 Python + native-sıra Chromium testi.
- #38 `1b78d0702f13df63d14e80de87f207e78faa4827`: Windows `42135043746`, unit PR `42135043717` ve push `42134971364` başarılı; 211 Python.
- #39 `da489e465b428f554341ff055c544338210a6d8e`: Windows `42136068296`, unit PR `42136068478` ve push `42135996726` başarılı; 215 Python, gerçek UI dosya indirme/restore Chromium testi. Native/frozen/DPAPI/installer/eski sürüm upgrade-rollback kontrolleri geçti. Shipped self-update testi mevcut yayımlı uygulamalar arasındadır; yeni PR binary'si yayımlanmış sayılmaz.
- PR39 Actions artifact `13465297813`, `AchievementAtlas-0.16.1-Windows-x64`, 78.734.670 byte; GitHub metadata digest `sha256:9c154020c1aeab049a8a53a782b196f57f01bb75ae8015a19672ec2b2fdb59fb`. ZIP bu ortamda indirilip içerik açılmış gibi raporlanmaz; CI/log/artifact kaydı kanıttır. Yayımlı Release değildir.
- Gerçek Windows/Xbox kabulü kullanıcı kendi cihazında yapabilecek; sonuç henüz gelmedi. Kabul formu: `ISSUE_37_WINDOWS_ACCEPTANCE_TR.md`.

Mevcut JSON export medya dosyalarını içermez. CSV ile aynı-platform public-profile arşivini karıştıran işlemler hâlâ koruma nedeniyle kısıtlanır; farklı hesapları otomatik birleştirme kaldırılmadı. Bu sınırlar tam taşınabilir medya yedeği veya tüm offline/online geçişlerin gerçek kullanıcıda tamamlandığı iddiasına dönüştürülmez.
