# #37: tarayıcıdan indirilen arşivin hash bütünlüğü

6 Kasım 2026. Ayrı takip PR'ı; #38'in offline arşiv testleri üzerine.

## Gerçek uygulama hatası

Uygulamanın export düğmesi JSON yanıtını `response.json()` ile okuyup `JSON.stringify()` ile yeniden yazıyordu. Python'un hash'e dahil ettiği `1.0` değeri JavaScript'te `1` olur; büyük tam sayılar da yuvarlanabilir. Restore düğmesi de dosyayı yeniden serialize ediyordu. Geçerli export, tarayıcı round-trip'inden sonra `Arşiv değiştirilmiş, eksik veya çok büyük` hatasına düşebiliyordu. Yalnız Python ile yapılan round-trip bu farkı yakalamıyordu.

## Dar düzeltme

- Export dosyası sunucunun JSON metninden doğrudan Blob olur; sayılar yeniden yazılmaz.
- Dosya importunda JSON parse yalnız önizleme/kayıt sayısı içindir. Onaydan sonra aynı ham metin POST edilir.
- Mevcut restore rotası, `X-Atlas-Archive-Confirm: restore` ile ham dosya kipini destekler. Eski `{archive,confirm}` istemcileri çalışmaya devam eder.
- Host/Origin, oturum token'ı, explicit confirmation, request/file boyutları, veri şeması, SHA256 ve recovery kontrolü aynen korunur. Hash kontrolü gevşetilmez.
- Export JSON kompakt yazılır; canonical veri sınırı ile dosya/HTTP boyut sınırları arasında gereksiz boşluk şişmesi olmaz. Format/migrasyon değişmez.

## Kanıt

Dört yeni yerel HTTP testi: `1.0` ve `9007199254740993` değerlerinin hash ile round-trip'i, token/Origin/onay zorunluluğu, bozulmuş veya JS gibi yuvarlanmış verinin reddi, eski API uyumu.

Yeni Chromium testi gerçek UI indir/yükle düğmelerini ve dosya seçimini kullanır: CSV → mevcut kapaktan arka plan/tarih/kaynak → not/pin → sayfayı yeniden aç → arşivi indir → not/pini değiştir → aynı dosyayı geri yükle → CSV'yi tekrar içe aktar. Not/pin/tarih/kimlikler ve aynı klasördeki görsel byte hash'i korunur. Dış HTTPS istekleri engellenir. Fixture temizlendikten sonra boş arşiv native history testi tekrar geçer.

Yerelde 215 Python testi geçti. Yeni offline tarayıcı, native sıra, metadata ve kısmi aktarım senaryoları geçti. Windows exact-head sonucu ayrıca raporlanır. Bunlar sentetik veridir; gerçek hesap, fiziksel gamepad veya gerçek kullanıcının interneti kesilmiş Windows kabulü değildir.

## Sınırlar

Daha önce başka bir araçla yeniden yazılıp hash'i bozulmuş dosyayı tahmin ederek onarmıyoruz. Orijinal veriler duruyorsa bu düzeltmeli uygulamadan yeniden export gerekir. Bozuk dosya mevcut arşivin üzerine yazılmaz.

JSON yedek hâlâ medya dosyalarını/credentials'ı içermez. Yerel görselin aynı klasörde korunması, başka cihaza tam medya yedeği anlamına gelmez. Yeni sürüm veya main/development merge yapılmaz.
