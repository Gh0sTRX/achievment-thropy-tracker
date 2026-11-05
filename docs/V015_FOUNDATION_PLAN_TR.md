# Achievement Atlas v0.15 Foundation — Ürünleşme Planı

**Durum (5 Kasım 2026):** 0.15.0 Development Windows Setup yayımlandı; PR #4/#5/#6/#7 birleştirildi. Aşağıdaki ilk dilim ve eski sıra maddeleri tarihsel plandır; güncel devam kaydı PROJECT_HANDOFF.md içindedir.
**Taban:** feature/unified-native-themes (PR #4).
**Ana geliştirme:** codex/public-profile-trophies (PR #1).
**Son yayın:** v0.15.0 Development. Ana dal olan main değiştirilmez.

## Ürün amacı

Oyuncu uygulamayı açtığında üç sorusuna kolay cevap bulmalı:

- Hangi oyun ve başarım kayıtlarım var?
- Sıradaki anlamlı hedef ne?
- Kayıtlarımın kaynağı ve kapsama güvenilirliği ne?

Tema ve Console Mode işlevi yardımcı olur; ayrı ikinci uygulama yaratılmaz.

## İlk Foundation diliminde uygulananlar

1. Birinci düzey gezinme: Atlas Hub, Kütüphane, Hedefler, Müze, Profil. Başarım Kasası, Zaman Çizelgesi, Görseller, Hesap & Veri ve Güncellemeler Diğer ekranlar altında durur. Sayfalar ve yönlendirmeler silinmez.
2. Boş kütüphane için üç yol: Xbox Gamertag, PlayStation Online ID, kazanılmış/kilitli TrueAchievements CSV. Servis ayarı varsa yalnız ayarlı olduğu söylenir, canlı doğrulandığı iddia edilmez.
3. Kütüphanesi dolu kullanıcıya oyun/sürüm sayısı, başarım kaydı ve sunucunun bildirdiği veri kaynağı/durumu gösterilir. Sahte veri üretilmez.
4. Güncelleme sırasında aktif profil, rehber, görsel, ikon, eski Xbox ve oturum görevleri ayrı adlarıyla gösterilir. Durdur düğmesi mevcut cooperative cancellation API'siyle çalışır; aktif iş bitmeden kurulum zorlanmaz.
5. Yerel tema görünümü ve Console Mode PR #4'e bağlıdır. Temalar Xbox/PSN veri filtresini değiştirmez.

Kod haritası: atlas/web/ui/foundation.js, foundation.css, atlas/web/index.html, atlas/web/app.js, atlas/server.py; test dosyaları tests/test_foundation_ui.cjs ve tests/test_update_blockers.py.

## Kullanıcı kabul testleri

- Boş data dizininde ilk açılış: doğru üç düğme, servis erişimi açıklaması; CSV seçimi doğru iki dosyalı formu açar.
- Gerçek veri yüklendiğinde onboarding kartı gizlenir ve durum şeridi görünür; oyun kimlikleri değişmez.
- Beş ana ve beş ikincil sayfa navigasyonu, hash route, odak, mobil ve XMB yatay düzeni.
- Güncellemede profil, rehber, görsel, ikon ve Xbox oturum işleri aktifse türü açıklanır; iş durmadan kuruluma izin verilmez.
- CI: Python 3.11/3.12/3.13 Ubuntu ve Windows; JS kontrolleri; Windows frozen app ve installer.
- Fiziksel gamepad, gerçek Xbox/PSN hesap erişimi, ekran okuyucu, Windows eski→yeni yükseltme ve rollback gerçek sistemde ayrıca doğrulanmalı.

## Kalan öncelikli ihtiyaçlar

P0: gerçek Xbox/PSN hesaplarıyla uçtan uca test; karma oyuncu/servis kimlik ayrımı; aynı adlı CSV edisyon kayıtlarının kaynağa dayalı eşlenmesi.
P0: çoklu JSON dosyaları için transaction/snapshot, dışa aktarma ve güvenli geri yükleme ekranı, bozuk dosya onarımı.
P0: Windows VM üstünde 0.13/0.14.1'den güncelleme ve başarısız rollback matrisi.
P1: 40 bin başarımda tam JSON yükü (yaklaşık 16 MB sentetik ölçüm), delta API ve toplu kayıt.
P1: gerçek artwork kapsama/edition doğruluğu, physical gamepad ve ekran okuyucu kontrolleri.
P2: gerçek Steam/PC başarım sağlayıcısı; rehber üretimi kota/maliyet ve kaynak doğrulaması.

## Geliştirme sırası

1. PR #4'ün kullanıcı deneyimi ve Windows kurulum testi; uygun görülürse ana geliştirme dalına birleştirme.
2. Bu Foundation PR'ını PR #4 üstüne inceleme ve regression; PR #4 birleşince Foundation dalını yeniden tabanlama.
3. Gerçek Xbox/PSN erişim testleri ve veri kapsam doğrulama.
4. Yerel arşiv export/restore, crash-safe transaction ve updater rollback.
5. Performans, artwork kapsaması, daha sonra Steam/PC.

**Yayın ilkesi:** PR'ın testlerden geçmesi, yeni sürümün yayımlandığı veya gerçek hesaba bağlandığı anlamına gelmez. main ve GitHub Development Release yalnız uygun inceleme/test sonrasında ayrı işlemle değiştirilir. Gerçek oyun görselleri dışında AI yapımı oyun görseli kullanılmaz.
