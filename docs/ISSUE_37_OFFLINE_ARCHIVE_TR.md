# #37 / #36: yerel arşiv sözleşmesi — dar düzeltme

6 Kasım 2026. #25 history/focus düzeltmesinin üzerine ayrı PR. Kapsam: yedek/export/restore doğrulayıcısı ve offline regresyonlar. Yeni sağlayıcı, tema, Next Move veya büyük veri migrasyonu yok.

## Yeniden üretilen sorunlar

1. Steam adaptörü `public_profiles.pc` kaydı oluşturuyor, fakat arşiv doğrulayıcısı yalnız `xbox`/`psn` kabul ediyordu. Karma arşivin dışa aktarımı başarısızdı. Önceki durumda PC profili varsa, restore işleminin koruyucu yedeği de oluşturulamıyordu.
2. `provider_inputs` ve `sync_warnings_by_platform` export allowlist'inde değildi. Restore sonrası platforma ait yerel kullanıcı adı veya uyarı kapsamı kaybolabiliyordu.

İlk test turunda PC profilinin export ve recovery-backup hataları ile taşınabilir adların kaybı yeniden üretildi. Tarih testindeki ilk sıra varsayımı kayıt kimliğiyle sorguya düzeltildi; tarih kaybı bug'ı olarak sunulmadı.

## Sonuç

- Mevcut `pc` profili kabul edilir; desteklenmeyen platform ve bozuk profil reddedilir.
- Platforma ait kullanıcı adları ve kapsamlı uyarılar doğrulanarak taşınır. Yeni zorunlu alan yok; eski v1 arşivleri desteklenir. Bazı eski uygulama sürümleri PC profilini zaten reddettiğinden geriye dönük binary kabulü vaat edilmez.
- Servis sırları ve `provider_access` canlı erişim durumu taşınmaz. Restore başka cihazda oturumu doğrulamış gibi göstermez.
- Format ve kütüphane dosyaları kontrolsüz migrate edilmez; doğrulama/hash/recovery mekanizması korunur.

## Test sınırı

Sentetik Python senaryoları: Xbox/PSN/Steam profil round-trip; güvenli ad/uyarı alanları; sır ve canlı erişim durumunun dışarı çıkmaması; ağ bağlantısı yasaklı çekirdekte tekrarlı CSV import, not/pin/tarih, yeniden açılış ve restore; mevcut yerel görsel dosyasının byte hash'inin korunması; mock bağlantı kesilmesinde arşivin kullanılabilir kalması; bilinmeyen/bozuk profil ve alanların reddi.

Bu test interneti fiziksel olarak kesilmiş gerçek Windows kullanıcı kabulü veya gerçek Xbox/Steam/PSN hesabı değildir. Windows CI ve gerçek kullanıcı kabulü ayrı raporlanır.

**Medya sınırı değişmedi:** JSON export yerel medya dosyalarını, credentials'ı ve geçmiş profil dosyalarını paketlemez. Aynı klasörde restore mevcut görseli korur; başka cihaza tam medya taşıma tamamlanmış değildir. Arayüzdeki dışa aktarım açıklaması bu sınırı zaten belirtir. Güvenli tam medya yedeği ayrı bir çalışma/negatif güvenlik testi gerektirir.
