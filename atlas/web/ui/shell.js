/* Native Achievement Atlas appearance and dedicated Console Mode.
   No second app shell: navigation, account state and achievement data remain in the original app.
   Artwork is read only through the existing verified visualUrl/visualStyle helpers. */
(() => {
  'use strict';
  const SKINS = ['cinematic', 'blades', 'nxe', 'xmb'];
  const $native = id => document.getElementById(id);
  const safeSkin = value => SKINS.includes(value) ? value : 'cinematic';
  const safeName = value => String(value || '').replace(/[&<>"']/g, char => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[char]));
  let stage = [], active = 0, returnFocus = null, raf = 0;
  let held = false, lastMove = 0, gamepadConnected = false;
  let timelineRange = 90;

  function refreshAppearance() {
    const value = safeSkin(DATA?.state?.ui?.theme_skin);
    document.body.dataset.skin = value;
    const select = $native('atlasThemeSkin');
    if (select && select.value !== value) select.value = value;
  }

  function scopedGames() {
    // The native platform and device tabs remain the only data filters.
    return typeof games === 'function' ? games() : [];
  }

  function focusGame(id) {
    const g = stage.find(item => item.id === id);
    if (!g) return;
    closeConsole();
    // The native game detail is the sole destination; do not open a duplicate Ultimate screen.
    if (typeof openGame === 'function') openGame(g.id);
  }

  function showGame() {
    const g = stage[active];
    if (!g) return;
    const title = $native('atlasConsoleTitle');
    const subtitle = $native('atlasConsoleSubtitle');
    const backdrop = $native('atlasConsoleArtwork');
    title.textContent = g.name || 'Oyun';
    const achievements = (DATA.library.achievements || []).filter(a => a.game_id === g.id);
    const unlocked = achievements.filter(a => a.unlocked).length;
    subtitle.textContent = (g.device_label || g.platform || 'Oyun') + ' · ' +
      unlocked + ' / ' + achievements.length + ' kayıtlı başarım · ' +
      (achievements.length ? (100 * unlocked / achievements.length).toFixed(1) + '%' : 'ilerleme yok');
    const url = visualUrl(g, 'hero') || visualUrl(g, 'banner') ||
      visualUrl(g, 'screenshot') || visualUrl(g, 'cover');
    backdrop.style.backgroundImage = url ? cssUrl(url) : 'none';
    backdrop.style.backgroundPosition = String(Number(g.art_theme?.x ?? 50)) + '% ' +
      String(Number(g.art_theme?.y ?? 38)) + '%';
    const rail = $native('atlasConsoleRail');
    const indices = [];
    for (let n = -2; n <= 2 && indices.length < stage.length; n++) {
      const index = (active + n + stage.length) % stage.length;
      if (!indices.includes(index)) indices.push(index);
    }
    rail.innerHTML = indices.map(index => {
      const item = stage[index];
      return '<button type="button" class="atlas-console-card ' +
        (index === active ? 'selected' : '') +
        '" data-atlas-game-index="' + index + '" aria-current="' +
        (index === active ? 'true' : 'false') +
        '" aria-label="' + safeName(item.name) + '">' +
        '<span class="atlas-console-cover"></span><b>' +
        safeName(item.name) + '</b></button>';
    }).join('');
    rail.querySelectorAll('[data-atlas-game-index]').forEach(button => {
      const item = stage[Number(button.dataset.atlasGameIndex)];
      const url = visualUrl(item, 'cover');
      button.querySelector('.atlas-console-cover').style.backgroundImage = url ? cssUrl(url) : 'none';
    });
    $native('atlasConsoleCount').textContent = (active + 1) + ' / ' + stage.length;
  }

  function step(direction) {
    if (!stage.length) return;
    active = (active + direction + stage.length) % stage.length;
    showGame();
  }

  function closeConsole() {
    const dialog = $native('atlasConsole');
    if (!dialog?.open) return;
    dialog.close();
    cancelAnimationFrame(raf);
    raf = 0;
    held = false;
    gamepadConnected = false;
    document.body.classList.remove('atlas-console-open');
    if (returnFocus?.isConnected) returnFocus.focus({preventScroll:true});
  }

  function pollController() {
    const dialog = $native('atlasConsole');
    if (!dialog?.open) return;
    try {
      const pads = navigator.getGamepads?.() || [];
      const pad = Array.from(pads).find(p => p && p.connected);
      if (Boolean(pad) !== gamepadConnected) {
        gamepadConnected = Boolean(pad);
        $native('atlasControllerStatus').textContent = pad ?
          'Gamepad bağlı' : 'Klavye kullanılabilir';
      }
      if (pad) {
        const left = Boolean(pad.buttons[14]?.pressed || pad.axes[0] < -0.7);
        const right = Boolean(pad.buttons[15]?.pressed || pad.axes[0] > 0.7);
        const accept = Boolean(pad.buttons[0]?.pressed);
        const back = Boolean(pad.buttons[1]?.pressed);
        const any = left || right || accept || back;
        const time = performance.now();
        if (any && (!held || ((left || right) && !accept && !back && time - lastMove > 260))) {
          lastMove = time;
          if (back) { closeConsole(); return; }
          if (accept) { focusGame(stage[active]?.id); return; }
          if (left) step(-1); else if (right) step(1);
        }
        held = any;
      } else held = false;
    } catch (_) {
      // Browsers without Gamepad API can still use the keyboard.
    }
    raf = requestAnimationFrame(pollController);
  }

  function openConsole() {
    const dialog = $native('atlasConsole');
    if (!dialog || dialog.open) return;
    stage = scopedGames();
    if (!stage.length) {
      if (typeof toast === 'function') toast('Önce bu platforma ait bir oyun yükle.', true);
      return;
    }
    const preferred = selectedGame || DATA?.state?.ui?.focus_game_id;
    active = Math.max(0, stage.findIndex(g => g.id === preferred));
    returnFocus = document.activeElement;
    held = false;
    gamepadConnected = false;
    $native('atlasControllerStatus').textContent = 'Klavye kullanılabilir';
    showGame();
    dialog.showModal();
    document.body.classList.add('atlas-console-open');
    dialog.querySelector('[data-atlas-console="open"]').focus({preventScroll:true});
    raf = requestAnimationFrame(pollController);
  }

  function onKey(event) {
    if (event.altKey && event.code === 'KeyC') {
      event.preventDefault();
      if ($native('atlasConsole')?.open) closeConsole(); else openConsole();
      return;
    }
    if (!$native('atlasConsole')?.open) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      step(event.key === 'ArrowLeft' ? -1 : 1);
    } else if (event.key === 'Enter' && !event.target.closest('button')) {
      event.preventDefault();
      focusGame(stage[active]?.id);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      closeConsole();
    }
  }

  function timelineRows(range) {
    const current = new Date(), today = new Date(current.getFullYear(), current.getMonth(), current.getDate() + 1);
    const earliest = new Date(today);
    earliest.setDate(earliest.getDate() - range);
    const stepDays = range === 30 ? 1 : range === 90 ? 7 : 30;
    const bins = [];
    for (let start = new Date(earliest); start < today;) {
      const next = new Date(start);
      next.setDate(next.getDate() + stepDays);
      if (next > today) next.setTime(today.getTime());
      bins.push({start:new Date(start),end:new Date(next),count:0});
      start = next;
    }
    const ids = new Set(scopedGames().map(g => g.id));
    const now = new Date();
    for (const achievement of DATA.library.achievements || []) {
      if (!achievement.unlocked || !ids.has(achievement.game_id)) continue;
      const date = AtlasModel.date(achievement.unlock_time);
      if (!date || date < earliest || date >= today || date > now) continue;
      const entry = bins.find(b => date >= b.start && date < b.end);
      if (entry) entry.count += 1;
    }
    return bins;
  }

  function drawTimeline() {
    const panel = $native('atlasTimelineChart');
    if (!panel) return;
    const bins = timelineRows(timelineRange);
    const max = Math.max(1, ...bins.map(b => b.count));
    const total = bins.reduce((sum, b) => sum + b.count, 0);
    $native('atlasTimelineTotal').textContent = total + ' tarihli kazanım (kayıtlı kapsam)';
    panel.innerHTML = '';
    const table = $native('atlasTimelineRows');
    table.innerHTML = '';
    const format = day => day.toLocaleDateString('tr-TR', {day:'2-digit',month:'short',year:'numeric'});
    for (const bin of bins) {
      const col = document.createElement('div');
      col.className = 'atlas-timeline-bin';
      col.title = format(bin.start) + ': ' + bin.count;
      col.setAttribute('aria-label', col.title);
      const bar = document.createElement('i');
      bar.style.height = (100 * bin.count / max) + '%';
      col.appendChild(bar);
      panel.appendChild(col);
      const tr = document.createElement('tr');
      const date = document.createElement('td');
      const amount = document.createElement('td');
      date.textContent = format(bin.start);
      amount.textContent = String(bin.count);
      tr.append(date, amount);
      table.appendChild(tr);
    }
    document.querySelectorAll('[data-atlas-range]').forEach(button => {
      button.setAttribute('aria-pressed', String(Number(button.dataset.atlasRange) === timelineRange));
    });
  }

  function init() {
    const select = $native('atlasThemeSkin');
    select?.addEventListener('change', () => {
      const skin = safeSkin(select.value);
      document.body.dataset.skin = skin;
      // The API stores only a cosmetic preference, never modifies account data or artwork.
      if (typeof savePreferences === 'function') savePreferences({theme_skin:skin});
    });
    const dialog = $native('atlasConsole');
    $native('atlasConsoleButton')?.addEventListener('click', openConsole);
    dialog?.addEventListener('cancel', e => {e.preventDefault(); closeConsole();});
    dialog?.addEventListener('click', e => {
      const action = e.target.closest('[data-atlas-console]')?.dataset.atlasConsole;
      if (action === 'close') closeConsole();
      if (action === 'previous') step(-1);
      if (action === 'next') step(1);
      if (action === 'open') focusGame(stage[active]?.id);
      const card = e.target.closest('[data-atlas-game-index]');
      if (card) {active = Number(card.dataset.atlasGameIndex); showGame();}
    });
    document.addEventListener('keydown', onKey, true);
    $native('timeline')?.addEventListener('click', e => {
      const button = e.target.closest('[data-atlas-range]');
      if (!button) return;
      timelineRange = Number(button.dataset.atlasRange);
      drawTimeline();
    });
    const previousRender = render;
    render = function unifiedRender() {
      previousRender();
      refreshAppearance();
      if (page === 'timeline') drawTimeline();
    };
    const previousNavigate = navigate;
    navigate = function unifiedNavigate(target) {
      previousNavigate(target);
      if (target === 'timeline') $native('breadcrumb').textContent = 'BAŞARIM ZAMAN ÇİZELGESİ';
    };
    refreshAppearance();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
  window.AtlasConsole = {open:openConsole, close:closeConsole, isOpen:() => Boolean($native('atlasConsole')?.open)};
})();
