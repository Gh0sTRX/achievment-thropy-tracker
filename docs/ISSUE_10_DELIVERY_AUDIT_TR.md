# Issue #10 — kaynak teslimi ve doğrulama

Tarih: 5 Kasım 2026. Bu belge **yayımlanmamış kaynak değişikliklerini** açıklar. Son yayımlanan geliştirme paketi 0.15.1'dir. Main değiştirilmedi, yeni Development Release oluşturulmadı. Gerçek kullanıcı arşivi veya servis anahtarı bu çalışmada kullanılmadı/yüklenmedi.

## 1. Önceki durum

Başlangıç `codex/public-profile-trophies` commit'i `17ec8b2`. Önceki 0.15.1 yayın ve gerçek native eski→yeni güncelleme kanıtları PROJECT_HANDOFF.md'de durur. Yeni kırmızı PR kontrolleri yayın başarısıyla karıştırılmadı. Oyun kartı kütüphanedeki panele kaydırıyordu, PC yalnız plan etiketi taşıyordu; eski browser audit aktif olmayan `.au-*` overlay'i bekliyordu.

## 2. PR zinciri

| Parça | PR | Dal / hedef |
|---|---|---|
| A — CI | https://github.com/Gh0sTRX/achievment-thropy-tracker/pull/11 | fix/issue10-ci-stability → codex/public-profile-trophies |
| B — Universe / artwork | https://github.com/Gh0sTRX/achievment-thropy-tracker/pull/12 | feature/issue10-game-universe → A |
| C — PSN / Steam | https://github.com/Gh0sTRX/achievment-thropy-tracker/pull/13 | feature/issue10-pc-providers → B |
| D — kimlik / UX / arama | https://github.com/Gh0sTRX/achievment-thropy-tracker/pull/14 | feature/issue10-navigation-search → C |
| E — kontrolcü / performans / QA | PR bağlantısı PROJECT_HANDOFF.md ve GitHub'da | feature/issue10-controller-performance → D |

Bunlar birbirinin üzerine kurulu inceleme PR'larıdır. Feature dalı değişiklikleri main'e veya çalışma dalına otomatik birleştirilmedi. Ayrıntı belgeleri `docs/issue10/` altındadır.

## 3. Game Universe

`atlas/web/index.html`, `ultimate.js`, `ultimate.css`: tek native shell içinde `#/game/{kalıcı-id}`. Kapak, hero, logo, cihaz/edisyon ve dürüst kayıt ilerlemesi; Overview, Achievements/Trophies, DLC, Timeline, Goals, Artwork, Notes. Başarımlar 48 satır, inline detay, gizli isim koruması ve sabitleme kullanır. Geri/History/Escape/gamepad B önceki görünüm, platform/cihaz filtresi, kütüphane sayfası, kaydırma ve görünür kart odağına döner. Kaydedilmemiş not taslağı polling/render sırasında korunur. Sekmeler ARIA tablist/tabpanel, oklar/Home/End ve LB/RB ile değişir. Modal arama Escape'i oyun rotasını kapatmaz. Motion tek 270 ms sayfa geçişinden gelir; reduced motion kapatır.

## 4. Gerçek artwork ve önce/sonra

`artwork.py`, `media_sync.py`, `server.py`, `public_profiles.py`, `core.py`, `visuals.js`:

- Xbox TitleHub aday türleri, PSN title ikonları, resmi hesap listesinden gelen Steam AppID media adayları ve mevcut SteamGridDB korunur.
- Beş ayrı tür: cover/hero/banner/logo/screenshot. Başlık benzerliğinden otomatik çapraz platform/edisyon eşleştirmesi yoktur.
- SteamGridDB en fazla beş oyun adayı sunar; açık sürüm onayı kalıcı provider/ID/platform/edition/devices kaydına bağlanır. Aynı ID olsa bile edisyon değişince onaylı adaylar taşınmaz.
- Kullanıcı dosyası önceliklidir. Kayıp kullanıcı dosyası otomatik görselle ezilmez; yeniden seçim istenir.
- Güvenilir HTTPS host/redirect, MIME, byte, gerçek decode/piksel sınırı ve yeniden kodlama mevcut korumaları kullanılır. Steam başarım API adları hash tabanlı dosya adıyla birbirine çarpmaz; eski Xbox/PSN cache adları korunur.
- Kaynak/asset ID, orijinal URL, hak notu, kayıt zamanı ve indirme durumu saklanır. Hak notu dağıtım lisansı/onay belgesi yerine geçmez.
- Artwork Health gerçek cache sayıları, eksik türler, ilk eksik oyunlar ve toplu tekrar denemesi gösterir. Geçici 5xx/transport için en fazla üç deneme; 401/403/429 durur. Durdurma sonraki istekleri engeller, tamamlanan görselleri korur.

| Ölçüm | Önce | Sonra | Kapsam |
|---|---:|---:|---|
| Beş türü sağlayan tek oyun fixture'ı | 0/5 (%0) | 5/5 (%100) | Mock ağ, gerçekten decode edilip yazılan test görseli |
| İkinci fixture indirmesi | — | 0 ağ çağrısı | Cache tekrar kullanımı |
| Gerçek kullanıcının kütüphanesi | Ölçülmedi | Ölçülmedi | Bu ortamda gerçek arşiv/servis oturumu yok |

Bu oran gerçek hesap için kapak başarısı değildir. CDN'de her AppID için her dosyanın bulunacağı varsayılmaz. IGDB kimlik/lisans erişimi tanımlanmadığından yeni IGDB bağlantısı eklenmedi; yetkisiz scraping veya AI artwork yapılmadı.

## 5. Xbox

Mevcut OpenXbox/Microsoft OAuth, XUID, Xbox 360 v1 / modern v2 ayrımı ve cihaz/edisyon kuralları korunur. Xbox Windows/iOS/Android oyunları Steam'e taşınmaz. CSV, eski kayıt ve kimlik regresyonları testlerle korunur. Yeni gerçek hesap testi yapılmadı; kaynak kodu bulunması canlı erişim kanıtı değildir.

## 6. PlayStation

Mevcut PSNAWP üzerinde PS3/Vita/PS4/PS5, bütün gruplar, gerçek earned/date/tier/progress/icon alanları korunur. SDK grup özeti alınır. Iterator yarıda kesilirse oyunun kısmi satırları atılır ve aynı oyuncunun eski title ID kaydı korunur. Auth/private/rate-limit güvenli hata verir. NPSSO existing DPAPI ayar sisteminde kalır. Yeni mock test dört cihazı ve kısmi iterator başarısızlığını kapsar. Gerçek NPSSO/hesap testi yapılmadı.

## 7. PC / Steam

`pc.py` sağlayıcı kaydı ve `steam.py` resmi Web API adaptörü eklendi. SteamID64/resmi vanity, GetOwnedGames, GetSchemaForGame v2 ve GetPlayerAchievements kullanılır. AppID+API-name kimliği, gerçek locked/earned/time/schema/icon; puan 0 ve kupa türü boş. Eksik kimlik veya earned bilgisi uydurulmaz. Gizli liste boş başarıya dönüştürülmez. Geçici oyun hataları eski kaydı korur; 401/403/429 bütün işi durdurur. Başka PC sağlayıcısının oyun kayıtları silinmez.

Anahtar yerel `ATLAS_STEAM_API_KEY` ayarı; Windows DPAPI, browser/export secret dışlama ve hata URL'lerini gizleme testlidir. Resmi API dokümanları incelendi. Gerçek Steam hesabı/anahtarıyla uçtan uca test yapılmadı. Diğer PC sağlayıcıları uygulanmış sayılmaz.

## 8. UX, kimlik ve rehberler

Ana menü Hub / Library / Vault / Goals / Profile; Museum diğer ekranlarda. Xbox/PSN/Steam/CSV ilk kurulum seçimi ve cihazdaki ayar ≠ doğrulanmış erişim ayrımı vardır. Son eşitleme görünür. Ctrl+K ve `/` yerel arama; cihaz/edisyon/DLC/hedef dahil, ok/Enter/Escape, 40 sonuç sınırı. Gizli ad/API kimliği spoiler kapalıyken indekslenmez.

Akıllı hedefler mevcut ölçülen ilerleme, sabitlenenler, yaklaşan kayıt tamamlamaları, kaynaklı nadirlik ve risk bayraklarını kullanır; hayali süre veya canlı sunucu garantisi yoktur. Brave/OpenAI otomatik ücretli üretimi varsayılan kapalı, açık tercih ve anahtarlar birlikte gerekir; elle başlatma ayrıdır. Rehber doğruluğu otomatik garanti edilmez.

Atlas'ın bağımsız logosu korundu. Microsoft/Valve/Sony resmî marka belgeleri incelendi; bu projeye verilmiş dağıtım izni bulunmadığından orijinal vendor logoları pakete eklenmedi, renkli metin etiketleri kullanıldı. Ayrıntılı kaynaklar D belgesinde.

## 9. Kontrolcü, erişilebilirlik ve mimari

Tek Gamepad API polling zinciri: analog/dpad yön, A aç, B inline/modal/rota geri, X hedef, Y arama, LB/RB Universe sekmesi veya platform. Görünür menü/header/transfer kontrolleri de odak adaylarıdır; select filtreleri yukarı/aşağı ile değişir. Donanım yoksa klavye çalışır. Fiziksel gamepad ve OS metin girişi/yerel confirmation dialogları ayrıca doğrulanmalıdır.

Shell/Foundation/Motion/Inline artık render/navigate fonksiyonlarını üst üste sarmalamaz; `atlas:before-render`, `atlas:render`, `atlas:navigate`, `atlas:update-status` olaylarını dinler. Çekirdek+Ultimate arasında tek orchestrator uzatımı kalır. Eski `ui/ultimate.js/css` aktif sayfaya yüklenmez; tarihî/prototip kaynaklar korunur. Eski overlay'e bakan Playwright audit native testlere dönüştürüldü.

## 10. Performans ölçümleri

Sentetik Chromium, 1440×900, dış internet istekleri kapalı, bu Linux ortamında tek koşu. Gerçek hesap indirme veya Windows cihaz performansı değildir; CI donanımında değişebilir. Sonuçlar `work/audit/browser-results.json` ve CI artifact'ında yeniden üretilir.

| Başarım | Oyun | Hub script+layout | Library script+layout | Sıcak Library | İlk arama | Payload |
|---:|---:|---:|---:|---:|---:|---:|
| 5.000 | 100 | 10,4 ms | 47,0 ms | 38,8 ms | 46,4 ms | 2,05 MB |
| 15.000 | 300 | 11,7 ms | 66,4 ms | 27,8 ms | 105,0 ms | 6,12 MB |
| 40.000 | 800 | 37,4 ms | 43,3 ms | 23,3 ms | 197,9 ms | 16,33 MB |

Game DOM ≤80, arama ≤40, başarım sayfası ≤48. Oyun/başarım indeksleri, scope ve progress cache'i dizi/revision/platform/device değişiminde yenilenir. Sunucu öneri/istatistik hesaplarını revision bazında tekrar kullanır. Aynı revision'daki status tekrarlarında 4 rank hesabı tekrar yapılmaz; save/revision değişimiyle geçersiz kılınır. 40k backend status: ilk 513,61 ms, sonraki 225,17/209,41 ms; kalan deepcopy/JSON payload maliyeti ölçülebilir borçtur. Arama indeksindeki oyun etiketleri tekrar normalize edilmez; aynı ortamın önceki ölçümündeki 361 ms ilk arama 197,9 ms'ye indi. Bu tek koşu karşılaştırması istatistiksel benchmark değildir.

## 11. Güvenlik ve gizlilik

PRIVACY.md Steam akışı ve CDN'leriyle güncellendi. API anahtarları dışa aktarılmaz; kaynak koduna/test fixture'larına gerçek token eklenmedi. Yerel Host/Origin/CSRF koruması, güvenli görsel doğrulama, kurulum hash/provenance ve rollback kontrolleri atlanmadı. Authenticode sertifikası/SignPath onayı varmış gibi gösterilmez. Sigstore/GitHub köken doğrulaması Windows imzası değildir. Main ve gerçek kullanıcı verileri korunur.

## 12. Test sonuçları ve Windows

- Yerel Python: **160 test geçti, 0 başarısız** (son kaynak test turu; takip eden değişiklikte sayı yeniden doğrulanmalı).
- Dört Node süiti geçti: model/edition/spoiler, art transition/cancel/bounded cache, unified shell, foundation.
- JS syntax: app, ultimate, ui/ultimate ve diğer aktif modüller kontrol edildi.
- Chromium: dört çözünürlükte rota/back/forward/deep-link/odak/not taslağı; native arama; 16 tema×çözünürlük/high-contrast/ARIA tab/identity bileşimi; simüle Gamepad API A/RB/X/Y/B; 5k/15k/40k performans ve cache invalidation geçti. Browser page error 0; fixture XSS çalışmadı.
- A: Unit tests **42066272591** ve Windows installer **42066272796** başarılı; native self-update başarılı; yayın işleri atlandı.
- B: Unit/Windows **42066432637 / 42066432834** başarılı.
- C/D ilk Windows koşusu eski `PC planned-state` smoke beklentisinde durdu. Beklenti gerçek Steam girişini doğrulayacak şekilde düzeltildi, yeniden koşular GitHub Actions'ta izlenir.
- E için gerçek Windows penceresinde sentetik Game Universe/tab/search/back/focus smoke eklendi. Bu belgenin ilk commit'inde E CI sonucu beklenir; tamamlanmadan başarılı build iddia edilmez. Son durum PR kontrolü/Actions'tan okunmalıdır.
- Fiziksel gamepad, fiziksel elektrik kesintisi/logon ve gerçek Xbox/PSN/Steam hesabı doğrulanmadı.

## 13. Kalan önemli on eksik ve önerilen sıra

| Öncelik | Dosya / alan | Eksik ve kullanıcı etkisi | Kanıt / mevcut kapsam | Çözüm ve zorluk |
|---|---|---|---|---|
| High | public_profiles.py / steam.py | Gerçek servis/hesap erişimi kanıtı yok | SDK/mock testleri var, operatör oturumu yok | Sahibi tarafından yetkilendirilmiş yerel kabul matrisi; orta |
| High | steam.py:fetch | Steam çok oyunlu profilde sıralı ağ sorguları yavaş olabilir | Kaynakta başlık başına schema+player, hız simülasyonu canlı değil | Ölçülmüş sınırlı paralellik + provider rate-limit; orta |
| High | server.py:status, app.js:reload | 40k tam JSON ≈16,33 MB, deepcopy/parse maliyeti | Chromium/backend ölçümleri | Revision bazlı kısmi veri API'si, sayfalı detail fetch; yüksek |
| High | Windows/update / CODE_SIGNING_POLICY.md | Authenticode yok, indirme itibar uyarıları sürebilir | Mevcut imzasız paket politikası | Onaylı sertifika/SignPath süreci, güvenlik atlamadan; dış bağımlılık |
| Medium | pc.py / core.py:apply_public_profile | Birden fazla PC sağlayıcı hesabının UI seçimi henüz yok | Steam kaydı ve diğer provider oyunlarını koruma testi var | Provider-scoped profil seçimi/geçmişi; orta |
| Medium | steam.py / Universe DLC | Steam schema DLC sahipliği/gruplarını sağlamaz | API alanları incelendi; uydurma grup yok | Resmî erişilebilir DLC metadata kaynağı + kullanıcı onayı; orta |
| Medium | Steam artwork / media_sync.py | Her AppID'de her CDN artwork türü bulunmaz | Mock cache ve güvenli missing durumu var | Gerçek hesap coverage örneklemi, izinli alternatif match; orta |
| Medium | ui/shell.js / desktop.py | Fiziksel kontrolcü, OS metin/confirmation girişi ve ekran okuyucu manuel kabul eksik | Standart API simülasyonu/ARIA otomasyonu var | Windows fiziksel cihaz + NVDA/VoiceOver manuel matris; orta |
| Medium | apply_update.ps1 | Fiziksel güç kesintisi ve gerçek Windows logon kurtarması doğrulanmadı | 8 fresh-process crash ve RunOnce registry testleri var | İzole VM güç/logon kabul testi; yüksek |
| Low | Platform branding / ui assets | Üretici logo izni doğrulanmadı; metin kimliği kullanılıyor | Resmî marka belgeleri ve lisans notu var | Hak sahibinden yazılı izin/uygun lisans; dış bağımlılık |

Öncelik: E Windows/native kabulünü yeşile getirme → gerçek hesapları sahibinin cihazında doğrulama → Steam schema önbelleği/paralellik → kısmi payload API'si → fiziksel gamepad/ekran okuyucu → imzalama. Yeni release ancak ayrı açık yayın talebiyle hazırlanmalıdır.
