> **Yeni:** Kullanıcı adıyla Xbox / PlayStation profil eşitleme, özgün kupa ikonları ve kaynak bağlantılı Türkçe rehber akışı eklendi. Servis kurulumu ve canlı doğrulama sınırları: [Kurulum](docs/PUBLIC_PROFILES_TR.md). Aşağıdaki OAuth/CSV açıklamaları mevcut alternatif akışları anlatır.

# Achievement Atlas — Türkçe Başlangıç

Achievement Atlas, **herkesin kendi hesabıyla** kullanabileceği açık kaynak, yerel çalışan başarım takip ve öneri uygulamasıdır. Xbox ilk platformdur; ileride PlayStation bağlantısı için ayrı bir sağlayıcı tasarlanmıştır.

**Durum:** v0.5 ön sürüm. CSV içe aktarma ve yerel arayüz test edildi. Canlı Xbox OAuth ve otomatik ikon indirmeleri gerçek kullanıcı hesabıyla uçtan uca doğrulanmadı. Bu proje Microsoft, Xbox, Sony veya TrueAchievements ile ilişkili değildir.

## Kurulum

1. Windows'ta Python **3.11 veya üzeri** kur.
2. `BASLAT_TARAYICI.bat` dosyasını aç (varsayılan tarayıcıda açılır).
3. Masaüstü penceresini kullanmak istersen `pip install pywebview` sonrasında `BASLAT_WINDOWS.bat` çalıştır.
4. TrueAchievements'tan indirdiğin **kazanılmış** ve **kilitli** CSV dosyalarını uygulama üzerinden içe aktar.
5. Xbox Live'ı denemek için `XBOX_BILESENINI_KUR.bat` ile isteğe bağlı OpenXbox kütüphanesini kur, ardından uygulamada Microsoft girişini başlat.

## Başlıca özellikler

- Oyun kapağı ve wallpaper seçimi (SteamGridDB için **kendi API anahtarın** gerekir).
- API'nin sağladığı resmî başarım simgeleri için yerel önbellek.
- Hedef işaretleme, puan getirisine göre öneriler, bitmeye yakın oyunlar, veri kaynaklı risk uyarıları.
- İlerleme yüzdesi ancak gerçek API verisi varsa gösterilir. TA oranı süre veya zorluk değildir.
- Kullanıcı adı, oyun/başarım listesi veya Microsoft belirteci kaynak koduna gömülü değildir.

## Test

```bash
python -m unittest discover -s tests -v
```

Ağ servisi 403/429 döndürürse uygulama erişim kontrolünü aşmaya çalışmaz. Özgün oyun görselleri ve ikonlar açık kaynak paketinin içinde dağıtılmaz. Geliştirme katkısı için `CONTRIBUTING.md`, sağlayıcı planı için `docs/PROVIDERS.md` dosyasına bak.