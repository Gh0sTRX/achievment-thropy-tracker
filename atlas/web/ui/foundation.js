/* v0.15 Foundation: a single navigation, honest onboarding and clear update blockers.
 * Uses the native app's existing render/navigation and never creates a second UI shell. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const extraPages = new Set(['achievements','timeline','artwork','account','updates','advanced']);

  function drawWelcome() {
    if (typeof DATA === 'undefined' || !DATA.library) return;
    const gamesList = Array.isArray(DATA.library.games) ? DATA.library.games : [];
    const items = Array.isArray(DATA.library.achievements) ? DATA.library.achievements : [];
    const welcome = byId('atlasWelcome');
    const summary = byId('atlasSourceSummary');
    if (!welcome || !summary) return;
    welcome.classList.toggle('hidden', gamesList.length > 0);
    document.body.classList.toggle('atlas-empty-library', gamesList.length === 0);
    summary.classList.toggle('hidden', gamesList.length === 0);
    if (gamesList.length) {
      const info = typeof SOURCE_STATUS !== 'undefined' ? SOURCE_STATUS : {};
      const provenance = typeof info.message === 'string' && info.message ?
        info.message : 'Yalnız yerel kayıtlardan hesaplanan sonuçlar';
      const text = String(gamesList.length) + ' oyun/sürüm · ' + String(items.length) +
        ' kayıtlı başarım. ' + provenance;
      if (summary.textContent !== text) summary.textContent = text;
      summary.dataset.state = info.state || 'stored';
    } else {
      const readiness = typeof PROVIDERS !== 'undefined' ? PROVIDERS : {};
      const display = (key, id) => {
        const node = byId(id);
        if (node) node.textContent = readiness[key] ?
          'Erişim ayarı var; canlı sorgu henüz doğrulanmadı' :
          'Erişim ayarı yok; gerekirse Gelişmiş ayarlardan yapılandır';
      };
      display('xbox', 'atlasWelcomeXboxStatus');
      display('psn', 'atlasWelcomePsnStatus');
    }
  }

  function drawUpdateBlockers() {
    const panel = byId('atlasUpdateBlockers');
    const stop = byId('atlasStopForUpdate');
    if (!panel || !stop) return;
    const blockers = typeof UPDATE_BLOCKERS === 'undefined' || !Array.isArray(UPDATE_BLOCKERS) ?
      [] : UPDATE_BLOCKERS.filter(x => typeof x === 'string' && x);
    panel.classList.toggle('hidden', blockers.length === 0);
    stop.classList.toggle('hidden', blockers.length === 0);
    if (blockers.length) {
      const text = 'Kurulum şu işlemleri bekliyor: ' + blockers.join(', ') +
        '. Durdurma isteği tamamlanınca güncellemeyi yeniden başlat.';
      if (panel.textContent !== text) panel.textContent = text;
    }
    // Do not permit the UI to start an install that the server would block anyway.
    if (typeof UPDATE !== 'undefined' && UPDATE.state === 'ready') {
      const install = byId('installUpdate');
      if (install) install.disabled = blockers.length > 0;
    }
  }

  function onboardingAction(kind) {
    if (typeof navigate !== 'function') return;
    navigate('account');
    if (kind === 'xbox' || kind === 'psn') {
      const select = byId('publicPlatform');
      if (select) {
        select.value = kind;
        select.dispatchEvent(new Event('change', {bubbles:true}));
      }
      const input = byId('publicUsername');
      input?.focus({preventScroll:true});
      input?.scrollIntoView({behavior:'auto',block:'center'});
    } else if (kind === 'csv') {
      const section = byId('atlasCsvImport');
      if (section) {
        section.open = true;
        section.scrollIntoView({behavior:'auto',block:'start'});
        byId('importGamertag')?.focus({preventScroll:true});
      }
    }
  }

  async function archiveAction(action) {
    const exportButton = byId('atlasArchiveExport');
    const restoreButton = byId('atlasArchiveRestore');
    const status = byId('atlasArchiveStatus');
    if (!exportButton || !restoreButton || !status || typeof api !== 'function') return;
    exportButton.disabled = true;
    restoreButton.disabled = true;
    try {
      if (action === 'export') {
        status.textContent = 'Arşiv hazırlanıyor…';
        const archive = await api('/api/archive/export', {});
        const data = new Blob([JSON.stringify(archive)], {type:'application/json'});
        const url = URL.createObjectURL(data);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'AchievementAtlas-Backup-' + new Date().toISOString().slice(0, 10) + '.json';
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 2000);
        status.textContent = 'Arşiv indirildi. Dosyayı özel ve güvenli bir konumda sakla.';
      } else {
        const file = byId('atlasArchiveFile')?.files?.[0];
        if (!file) throw new Error('Önce bir Atlas JSON arşivi seç.');
        if (file.size > 49_000_000) throw new Error('Arşiv dosyası 49 MB sınırını aşıyor.');
        let documentData;
        try { documentData = JSON.parse(await file.text()); }
        catch (_) { throw new Error('Seçilen dosya geçerli JSON değil.'); }
        const count = Array.isArray(documentData?.data?.library?.achievements) ?
          documentData.data.library.achievements.length : '?';
        if (!confirm('Bu işlem mevcut yerel kütüphaneyi ' + count +
          ' başarım kaydıyla değiştirecek. Önceki durum recovery klasöründe saklanacak. Devam?')) return;
        status.textContent = 'Bütünlük ve oyun kimlikleri doğrulanıyor…';
        const result = await api('/api/archive/restore', {archive:documentData, confirm:true});
        await reload();
        navigate('home');
        status.textContent = result.message;
        if (typeof toast === 'function') toast(result.message);
      }
    } catch (error) {
      status.textContent = error.message || 'Arşiv işlemi başarısız.';
      if (typeof toast === 'function') toast(status.textContent, true);
    } finally {
      exportButton.disabled = false;
      restoreButton.disabled = false;
    }
  }

  function init() {
    if (typeof render === 'function') {
      const original = render;
      render = function foundationRender() {
        const result = original.apply(this, arguments);
        drawWelcome();
        return result;
      };
    }
    if (typeof navigate === 'function') {
      const original = navigate;
      navigate = function foundationNavigate(destination) {
        const result = original.apply(this, arguments);
        if (extraPages.has(destination)) {
          const menu = byId('atlasMoreNav');
          if (menu) menu.open = true;
        }
        return result;
      };
    }
    if (typeof renderUpdates === 'function') {
      const original = renderUpdates;
      renderUpdates = function foundationRenderUpdates() {
        const result = original.apply(this, arguments);
        drawUpdateBlockers();
        return result;
      };
    }
    document.body.addEventListener('click', event => {
      const archiveButton = event.target.closest('#atlasArchiveExport, #atlasArchiveRestore');
      if (archiveButton) {
        archiveAction(archiveButton.id === 'atlasArchiveExport' ? 'export' : 'restore');
        return;
      }
      const button = event.target.closest('[data-atlas-onboard]');
      if (!button) return;
      const kind = button.dataset.atlasOnboard;
      if (kind === 'xbox' || kind === 'psn' || kind === 'csv') onboardingAction(kind);
    });
    if (window.uiLoaded) drawWelcome();
    if (typeof UPDATE !== 'undefined') drawUpdateBlockers();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, {once:true});
  } else {
    init();
  }
})();
