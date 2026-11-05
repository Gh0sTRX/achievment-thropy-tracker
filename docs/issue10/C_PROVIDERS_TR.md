# Issue 10 — PSN / PC sağlayıcıları

## Uygulama

PC ayrı ekosistem, `atlas/pc.py` sağlayıcı kaydıdır. İlk uygulama `atlas/steam.py`: SteamID64/resmi vanity çözümü, GetOwnedGames, GetSchemaForGame v2, GetPlayerAchievements. AppID + API adı kimlikleri kullanılır. Puan 0, kupa türü boş: Gamerscore/platin dönüşümü yok. Başarımsız oyun şeması, gizlilik, anahtar yokluğu, 401/403/429, yanlış hesap, eksik kazanılma bilgisi ve ağ hataları güvenli biçimde durur. Oyun bazlı geçici hata aynı oyuncunun eski oyununu korur. Diğer PC sağlayıcı kayıtları Steam eşitlemesiyle silinmez. Gerçek sahiplik UI tarafından çıkarılmaz. API anahtarı mevcut DPAPI ayar kanalına eklenir; arşive/status yanıtına secret olarak yazılmaz. Steam API yönlendirmeleri reddedilir ve ağ hata URL'leri gösterilmez.

PSNAWP mevcut adaptöründe oyun başına satırlar artık atomik hazırlanır: bir iterator yarıda hata verirse o oyunun yarım kupaları içeri girmez, eski title ID korunur. Kimlik yokluğu tüm işlemi reddeder; auth/private/rate limit hataları durur. PS3/PS4/PS5/Vita cihaz kimlikleri, tüm gruplar, kupa türleri ve kazanılma bilgileri korunur. Gerçek SDK `trophy_groups_summary` ile grup adları/açıklamaları alınır. `limit=None` SDK pagination davranışını korur.

## Kanıt ve sınır

Yeni mock testler: Steam resmi identity/schema eşleştirmesi, yanlış hesap, özel profil, hız sınırı, kısmi hata ve diğer PC sağlayıcısını koruma, iptal, kötü URL, secret sızıntısı; PSN dört cihaz ve yarıda kesilen iterator.

Gerçek Xbox/PSN/Steam oturumu bu ortamda yok. Gerçek hesabın indirme hızı, canlı SDK davranışı veya gerçek artwork kapsamı doğrulanmadı. Steam şu anda sıralı sorgular kullanır; büyük hesaplarda sınırlı paralellik/kalıcı schema önbelleği ayrıca ölçülmelidir. Yeni PC sağlayıcılarının eklenmesinde profil seçimi çoklu sağlayıcı hesabına genişletilmelidir; Steam dışı entegrasyon yapılmış sayılmaz.

## Resmi kaynaklar (5 Kasım 2026 incelendi)

- https://partner.steamgames.com/doc/webapi/IPlayerService — GetOwnedGames ve görünürlük
- https://partner.steamgames.com/doc/webapi/ISteamUserStats — kazanımlar ve schema v2
- https://partner.steamgames.com/doc/webapi/ISteamUser — vanity çözümü
- Yüklü PSNAWP User.trophies / trophy_titles / trophy_groups_summary imzaları incelendi; canlı çağrı yapılmadı.
