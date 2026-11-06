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
    const achievements = achForGame(g.id);
    const unlocked = achievements.filter(a => a.unlocked).length;
    subtitle.textContent = (g.device_label || g.platform || 'Oyun') + ' · ' +
      unlocked + ' / ' + achievements.length + ' kayıtlı başarım · ' +
      (achievements.length ? (100 * unlocked / achievements.length).toFixed(1) + '%' : 'ilerleme yok');
    const url = visualUrl(g, 'hero') || visualUrl(g, 'banner') ||
      visualUrl(g, 'screenshot') || visualUrl(g, 'cover');
    backdrop.style.backgroundImage = url ? cssUrl(url) : 'none';
    backdrop.style.backgroundPosition = String(Number(g.art_theme?.x ?? 50)) + '% ' +
      String(Number(g.art_theme?.y ?? 38)) + '%';
    const cover = $native('atlasConsoleCover'), coverUrl = visualUrl(g, 'cover');
    cover.hidden = !coverUrl;
    cover.onerror = () => { cover.hidden = true; };
    if (coverUrl) { cover.src = coverUrl; cover.alt = (g.name || 'Oyun') + ' kapağı'; }
    else { cover.removeAttribute('src'); cover.alt = ''; }
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
    ensureController();
  }

  function focusDirection(dx,dy) {
    if($native('atlasSearch')?.open){const input=$native('atlasSearchQuery');input.dispatchEvent(new KeyboardEvent('keydown',{key:dy<0?'ArrowUp':'ArrowDown',bubbles:true}));return}
    const root=document.querySelector('dialog[open]')||document.body;
    const nodes=[...(root?.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select,textarea')||[])].filter(n=>n.getClientRects().length&&!n.closest('[inert]'));
    if(!nodes.length)return;const selected=document.activeElement,rect=selected?.getBoundingClientRect();
    let best=null,score=Infinity;
    if(nodes.includes(selected)&&rect){const x=rect.left+rect.width/2,y=rect.top+rect.height/2;
      for(const node of nodes){if(node===selected)continue;const r=node.getBoundingClientRect(),vx=r.left+r.width/2-x,vy=r.top+r.height/2-y,forward=dx?vx*dx:vy*dy;if(forward<=2)continue;const distance=forward+Math.abs(dx?vy:vx)*2;if(distance<score){score=distance;best=node}}
    }
    (best||nodes[0]).focus();
  }
  function shoulder(direction) {
    if(page==='universe'&&!$native('atlasConsole')?.open){const tabs=[...document.querySelectorAll('#universe [data-tab]')],i=tabs.findIndex(n=>n.getAttribute('aria-selected')==='true');const next=tabs[(Math.max(0,i)+direction+tabs.length)%tabs.length];next?.click();next?.focus();return}
    const platforms=['all','xbox','psn','pc'],i=platforms.indexOf(ACTIVE_PLATFORM);switchPlatform(platforms[(i+direction+platforms.length)%platforms.length]);
    if($native('atlasConsole')?.open){stage=scopedGames();active=0;if(stage.length)showGame();else closeConsole()}
  }
  function controllerAction(action) {
    const consoleOpen=Boolean($native('atlasConsole')?.open),search=$native('atlasSearch');
    if(action==='back'){if(consoleOpen)closeConsole();else if(search?.open)search.close();else if(document.querySelector('.inline-achievement'))closeInline();else if(page==='universe')window.AtlasGameRoute.back();else if(history.state?.page)history.back();else navigate('home');return}
    if(action==='search'){if(consoleOpen)closeConsole();window.AtlasSearch?.open();return}
    if(action==='previous-tab'||action==='next-tab'){shoulder(action==='previous-tab'?-1:1);return}
    if(action==='pin'){const focus=document.activeElement,host=focus?.closest('.achievement-row,.suggest,.inline-achievement');const button=focus?.matches('[data-pin]')?focus:host?.querySelector('[data-pin]');button?.click();return}
    if(action==='accept'){if(consoleOpen)focusGame(stage[active]?.id);else if(search?.open)$native('atlasSearchQuery').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));else document.activeElement?.click();return}
    if(!consoleOpen&&document.activeElement?.tagName==='SELECT'&&['up','down'].includes(action)){const control=document.activeElement;control.selectedIndex=Math.max(0,Math.min(control.options.length-1,control.selectedIndex+(action==='up'?-1:1)));control.dispatchEvent(new Event('change',{bubbles:true}));return}
    if(consoleOpen){step(action==='left'||action==='up'?-1:1);return}
    focusDirection(action==='left'?-1:action==='right'?1:0,action==='up'?-1:action==='down'?1:0);
  }
  function ensureController(){if(!raf)raf=requestAnimationFrame(pollController)}
  function pollController() {
    raf=0;
    const dialog=$native('atlasConsole');let pad;
    try{pad=Array.from(navigator.getGamepads?.()||[]).find(p=>p&&p.connected)}catch(_){}
    gamepadConnected=Boolean(pad);
    $native('atlasControllerStatus').textContent=pad?'Gamepad bağlı · A aç · B geri · X hedef · Y ara · LB/RB sekme/platform':'Klavye kullanılabilir';
    if(pad){const pressed=i=>Boolean(pad.buttons[i]?.pressed);let action=pressed(1)?'back':pressed(3)?'search':pressed(2)?'pin':pressed(4)?'previous-tab':pressed(5)?'next-tab':pressed(0)?'accept':pressed(14)||pad.axes[0]<-.7?'left':pressed(15)||pad.axes[0]>.7?'right':pressed(12)||pad.axes[1]<-.7?'up':pressed(13)||pad.axes[1]>.7?'down':null;
      const time=performance.now(),repeat=['left','right','up','down'].includes(action);
      if(action&&(!held||(repeat&&time-lastMove>260))){lastMove=time;controllerAction(action)}held=Boolean(action);
    }else held=false;
    if(pad||dialog?.open)ensureController();
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
    ensureController();
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
    window.addEventListener('gamepadconnected',ensureController);
    window.addEventListener('gamepaddisconnected',ensureController);
    $native('timeline')?.addEventListener('click', e => {
      const button = e.target.closest('[data-atlas-range]');
      if (!button) return;
      timelineRange = Number(button.dataset.atlasRange);
      drawTimeline();
    });
    window.addEventListener('atlas:render',()=>{refreshAppearance();if(page==='timeline')drawTimeline()});
    window.addEventListener('atlas:navigate',event=>{if(event.detail.destination==='timeline')$native('breadcrumb').textContent='BAŞARIM ZAMAN ÇİZELGESİ'});
    refreshAppearance();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
  window.AtlasConsole = {open:openConsole, close:closeConsole, isOpen:() => Boolean($native('atlasConsole')?.open)};
})();
