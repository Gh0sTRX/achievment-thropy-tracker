# Achievement Atlas 0.16.3 — test adayı, yayımlanmadı

Artwork Rescue ve mevcut Console Mode kabul çalışmasıdır. Yayımlı Development
kanalı **0.16.2** olarak kalır; bu dosya veya CI artifact'ı yayın anlamına gelmez.

- Görsel Sağlığı: cover/hero/banner/logo/screenshot/ikon ayrımı; neden ve güvenli
  çözüm, tek oyun kontrolü, seçme ve targeted retry. İkon-only eksikler görünür.
- Cache ve recovery/reset, bilinen farklı Title ID/edisyon kaynağını uygulamaz;
  kullanıcı dosyaları ve eski dosya baytları silinmez.
- Console Mode → Game Universe → geri akışında seçili oyun ve kart odağı döner.
  Aynı shell/temalar korunur; kontrol kılavuzu okunabilirliği iyileştirilir.

Tam kabul matrisi: [v0.16.3 raporu](V0_16_3_ARTWORK_CONSOLE_ACCEPTANCE_TR.md).
Hedef üç oyunun gerçek artwork kapsamı ve fiziksel kontrolcü/TV/NVDA kabulü
beklenir; sentetik test gerçek oyun kanıtı değildir. Kullanıcı v0.16.2 Xbox/PSN/
Steam akışlarını geçti olarak bildirdi; bu tüm sağlayıcı senaryoları anlamına
gelmez. JSON yedek medya dosyalarını içermez. Bu aday da sertifikasızsa imzasızdır.

Yayın için yeni açık kullanıcı onayı gerekir. Main'e merge yapılmaz.
