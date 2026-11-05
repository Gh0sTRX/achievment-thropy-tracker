# Steam eşitleme — yerel şema önbelleği

Bu değişiklik PR #15 üzerine ayrı dalda hazırlanmıştır; main veya yayımlanmış 0.15.1 paketini değiştirmez.

## Davranış

Resmi Steam `GetSchemaForGame` yanıtındaki oyun adı ve başarım metadata alanları cihazdaki `cache/steam-schemas/{AppID}-english.json` dosyasında 6 saat saklanır. Oyuncu kimliği, API anahtarı, kazanılma durumu ve tarihleri bu dosyaya yazılmaz. Cache kütüphane payload'ına ve JSON arşiv dışa aktarımına eklenmez.

Her eşitlemede GetOwnedGames ve her başarımlı oyunun GetPlayerAchievements sorgusu yeniden yapılır. Yeni/farklı API başarım kimliği görülürse şema bir kez zorunlu yenilenir; hâlâ uyuşmuyorsa eski profil verileri korunur. Başarımsız/boş şema kalıcı olarak yokluk kabul edilmez; boş başarım şeması sonraki eşitlemede yeniden sorgulanır. Daha önce başarımları bulunan oyun için gelen boş şema eski listeyi silmez; kısmi hata olarak korunur.

“Tam yenile” seçeneği cache'i atlar. Süresi dolmuş/gelecek tarihli, yanlış AppID/dil/sürüm veya bozuk cache tekrar indirilir. Cache yazılamazsa başarılı profil sorgusu başarısız sayılmaz. Ağ/auth/429 ve iptal davranışları korunur; erişim kısıtı eski şemadan sahte başarıya çevrilmez.

## Ölçüm ve test

100 oyunlu mock API senaryosunda ilk eşitleme **201**, cache sıcak eşitleme **101** çağrı yaptı. İkinci turda 100 oyuncu başarım sorgusunun tamamı yapıldı; kayıtların kimlikleri ve değerleri korundu. Bu yaklaşık %50 daha az toplam çağrıdır; gerçek hesabın indirme süresinde %50 hız garantisi değildir.

Testler: sıcak cache ve değişen earned; TTL/force/bozuk dosya/gelecek tarih/yanlış AppID/sürüm/bozuk şema; yeni başarım kimliğiyle refresh; disk yazma hatası; boş şema; güvenli AppID yolu; 100 oyun çağrı bütçesi. Gerçek Steam API anahtarı veya hesap kullanılmadı.

Önceki teknik borçlardan şema tekrar indirme maliyeti ele alındı. Sınırlı paralel Steam sorguları ve büyük /api/data payload'ı ayrı işler olarak kalır. Gereksiz paralellik veya hız limiti aşma eklenmedi.
