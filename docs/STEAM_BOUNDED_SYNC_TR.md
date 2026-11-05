# Steam — sınırlı paralel eşitleme

PR #16 üzerine ayrı geliştirme: `feature/steam-bounded-sync`. Main ve yayımlanmış pakete dokunulmaz; yeni Release oluşturulmaz.

## Değişiklik

Steam oyunları tek tek beklenmek yerine en fazla üç işçiyle, üç oyunluk gruplar halinde işlenir. Kütüphanenin tamamı executor kuyruğuna doldurulmaz. Bir oyunun şema ve oyuncu başarım istekleri kendi içinde sıralıdır. Her işçiye doğru hedef hesap, şema cache'i, force tercihi ve durdurma bağlamı taşınır. Sonuçlar kaynak oyun sırasına göre toplanır; ilerleme bildirimi tek ana akıştan monoton artar. Xbox/PSN ve aynı isimli edisyonlar bu akışa dahil edilmez.

401/403/429 veya beklenmeyen hata mevcut gruba durdurma sinyali verir; sonraki grup başlatılmaz. Devam eden HTTP istekleri mevcut timeout sınırında tamamlanır, sonraki istekler engellenir. Asıl auth/rate-limit hatası, diğer işçilerin iptal hatasıyla örtülmez. Kullanıcı durdurması da yeni grupları engeller. Sıradan oyun bazlı geçici hata önceki kaydı koruyan partial snapshot'a dönüşür; diğer oyunlar devam eder.

Önceki altı saatlik metadata cache'i, her seferinde güncel oyuncu sorgusu, boş şemada kayıt koruma ve kaynak kimlikleri korunur. Eşzamanlılık sağlayıcının kotasını kaldırmaz; hız limiti aşılmaya çalışılmaz ve 429 otomatik tekrar edilmez.

## Doğrulama

- Üç işçinin bariyerle gerçekten üst üste çalıştığı, eşzamanlılığın üç olduğu ve sonuç sırasının korunduğu test edildi.
- Context/force/cache/stop aktarımı, ilk grupta iptal, 429'un gerçek hata olarak korunması, kısmi oyun hatası ve tekrarlı ID'lerin isteklerden önce reddi test edildi.
- Gerçek Controller eşitleme işinde 403 sonrası arşiv dosyası, not ve pinlerin değişmediği; medya işinin başlamadığı doğrulandı.
- Tüm Python regresyonları: **175 test geçti**. Eski 100 oyunluk 201→101 istek bütçesi testleri de korunur.

Sentetik benchmark: 30 oyun, her şema/oyuncu mock isteğine 5 ms gecikme, üç tekrar. Bir işçi medyan **312,44 ms**, üç işçi medyan **106,44 ms**. Bu kontrollü testte yaklaşık 2,9 kat iyileşmedir; gerçek Steam hesabının hız garantisi değildir. Gerçek API anahtarı/hesap kullanılmadı.

Tekrar üretim: `python tests/benchmark_steam_sync.py`. Zaman ölçümüne göre kırılgan CI assertion yoktur; birim testleri bariyer/işçi sayısı/kimlik ve veri korumasını doğrular. Son CI/Windows durumu ilgili PR kontrolünden okunmalıdır.
