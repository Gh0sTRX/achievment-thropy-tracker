# #37 ilk kalite kapısı: native history / focus

6 Kasım 2026. Kapsam #22/#25 ve #33'ün başarısız Windows kontrolüdür; yeni özellik, arşiv migrasyonu veya yayın yok.

## Kanıtlanan problem

#25 kaynak `1512997624fd6ad1954fbf9f9f093460ba70b474`, Windows koşusu `42107565658`, job `127526967929`: `Native history/focus restoration failed`. Python/Chromium geçişi native kabulün yerine sayılmadı.

Boş yerel arşivde Windows smoke testinin aynı programatik sırası Chromium'da tekrarlandı. Başarım düğmesinin `.click()` çağrısı odak vermediği için `expandInline` aktif öğeden satırı bulamıyor ve `#achievements` rotasını ekliyordu. Geri dönmek `#games` yerine Universe'e dönüyordu. Ayrıca arka plan yenilemesi kart DOM'unu değiştirince odak body'ye düşüyordu.

## Düzeltme

- Delegated click gerçek düğmeyi `jumpAch` → `expandInline` zincirine taşır; klavye/gamepad davranışı korunur.
- Render yalnız kaldırdığı odaklı kayıt düğmesini aynı `data-gid`/`data-ach`/`data-pin` değerli görünür düğmeye geri taşır; başka kontrolün yeni odağını çalmaz. `preventScroll` kullanılır.
- Boş fixture ve `test_native_history.cjs`, Windows smoke testinin gerçek JS senaryosunu yeniden kullanır. Programatik inline → arama → geri → async reload sırası, fazladan history olmaması ve kalıcı kart odağı assert edilir.
- Mevcut metadata testi programatik tıklama ve yeniden çizim sonrası odağı da doğrular.
- Windows başarısızlığında desktop/frozen test raporları da artifact'a eklenir. Test kapatılmadı ve süre sınırları artırılmadı.

## Sonuç / sınır

Yerelde 203 Python testi; dört Node suite; yeni native-sıra Chromium testi, metadata, dört çözünürlükte Universe, kısmi aktarım ve 5k/15k/40k/gamepad simülasyonu geçti. Windows exact-head sonucu PR #25'te ayrıca doğrulanacak. Gerçek kullanıcı hesabı, fiziksel gamepad ve NVDA kabulü değildir. Mevcut dört tema, veri formatı, kazanımlar, notlar, tarihler, pinler ve görsel dosyaları değiştirilmedi. Main/development merge ve Release yapılmaz.
