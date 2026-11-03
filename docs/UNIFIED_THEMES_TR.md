# Achievement Atlas — Birleşik yerel tema mimarisi (taslak)

## Ürün kararı

**Tek arayüz, tek gezinme ve tek veri kaynağı.** Önceki ayrı "✦ Atlas Ultimate" tam ekran uygulama kabuğu artık yüklenmez. Cinematic, Xbox 360 Blades-inspired, Xbox 360 NXE-inspired ve PS3 XMB-inspired seçenekleri üst çubuktan seçilir ve **aynı** Atlas Hub / Library / Game Universe / Achievements / Quest Board / Hall of Fame / Unlock Timeline / Profile / Artwork / Settings / Updates arayüzünü biçimlendirir.

Tema değişimi renkleri, kartları, kenar menüsünü, arka planı, tipografik vurguları ve XMB geniş masaüstü düzenini etkiler. Xbox / PSN / PC platform seçimi ile platform renk kimliği **ayrı işlevlerdir**, tema değiştirmek veri sorgusu başlatmaz veya hesapları birleştirmez.

Console Mode isteğe bağlı tam ekran **dialog** olmaya devam eder; ok tuşları veya Gamepad API ile gerçek kütüphanedeki oyunları dolaşır ve seçim **yerel Game Universe detayına** açılır. Alt+C aç/kapat; Enter/A aç, Esc/B kapat. Fiziksel gamepad doğrulaması ayrıca yapılmalıdır.

## Kod mimarisi

- \`atlas/web/index.html\`: tek uygulama HTML kabuğu, üst çubuk tema seçici ve Console Mode dialog.
- \`atlas/web/ui/shell.css\`: bütün yerel ekranlara uygulanabilir dört farklı görünüm; oluşturulan oyun resimleri veya telifli varlıklar paketlenmez.
- \`atlas/web/ui/shell.js\`: tema tercihlerini mevcut \`/api/preferences\` ile kaydeder; yerel Console Mode ve kayıtlı tarihlerin ortak Timeline sayfasını çalıştırır.
- \`atlas/preferences.py\`: geriye dönük uyumlu \`theme_skin\` değeri yalnız \`cinematic\`, \`blades\`, \`nxe\`, \`xmb\` seçeneklerini kabul eder; mevcut tema/filtre değerleri silinmez.
- \`atlas/server.py\`: iki yeni güvenli, **exact allowlist** statik rota.
- \`atlas/web/ui/ultimate.js\` ve \`ui/ultimate.css\` Git geçmişi / referans için kalır ancak canlı sayfaya **yüklenmez**. Kopya uygulama kabuğu ve onun bağımsız localStorage tema state'i artık devreye girmez.

## Test ve kullanıcı doğrulama

1. Tek üst çubuk ve tek sol menü olduğunu kontrol et; ikinci \`au-root\` DOM öğesi oluşmamalı.
2. Dört temadan her birine geç; Hub, Library, Kasa, Hedefler, Müze, Zaman Çizelgesi, Profil, Görseller ve Güncellemeler sayfalarını gez.
3. Seçili tema uygulama yeniden açıldıktan sonra da kalmalı; Xbox/PSN hesap ve oyun filtreleri değişmemeli.
4. 30/90/365 günlük Timeline yalnız geçerli gerçek tarihlerden hesaplanmalı; boş kütüphane sahte sayı üretmemeli.
5. Console Mode'da keyboard/gamepad simülasyonu ve odak dönüşü; yerel oyun detayına geçişi test et.
6. Görsel yokken CSS fallback; gerçek art varsa yalnız güvenli \`visualUrl\` pipeline; \`prefers-reduced-motion\` çalışmalı.
7. Python testleri, Node \`--check\`, CI Windows build / frozen app ve installer testlerini çalıştır.
8. Kod doğruysa kullanıcı testi sonrası ana geliştirme dalına merge edilebilir. \`main\` ve Development Release **bu PR ile değiştirilmez**.

## Sınırlar

Yeni görünüm katmanı herhangi bir Xbox/PSN/Steam veri sağlayıcısı eklemez; hesap erişimi sınırları aynıdır. Tema bir kozmetik tercih olduğundan kütüphanenin oyun/achievement kimlikleri değişmez. Bu dalda SignPath onayı veya Windows Authenticode imzası varsayılmaz. Gerçek oyun görselleri oluşturulmaz; mevcut güvenli sağlayıcı önbelleği ve kullanıcı seçimleri kullanılır.
