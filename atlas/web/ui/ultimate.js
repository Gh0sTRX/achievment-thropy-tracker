/* Achievement Atlas Ultimate — progressive, local-first cinematic experience.
 * Uses existing application data/functions; no fake unlocks, images or platform connections.
 * All artwork comes from the user's existing, allow-listed game library/cache.
 */
(() => {
  'use strict';
  const KEY = 'achievement-atlas-ultimate-v5';
  const MODES = ['cinematic', 'blades', 'nxe', 'xmb'];
  const PLATFORMS = ['all', 'xbox', 'psn', 'pc'];
  const VIEWS = ['hub', 'library', 'game', 'quests', 'hall', 'timeline', 'artwork'];
  const $u = (id) => document.getElementById('au-' + id);
  const html = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const showNum = (v) => Number(v || 0).toLocaleString('tr-TR');
  const clamp = (n, min, max) => Math.max(min, Math.min(max, Number(n) || 0));
  const fileKey = (id) => String(id || '').slice(0, 120);
  const sample = () => typeof DATA !== 'undefined' && DATA.library && (DATA.library.platform === 'demo' || ((DATA.library.games || []).length>0 && DATA.library.games.every(g => g.platform === 'demo')));
  const isX = (p) => ['xbox','xbox360','xboxone','series'].includes(String(p || '').toLowerCase());
  const platformKey = (g) => {
    const p = String(g.platform || '').toLowerCase();
    if (isX(p)) return 'xbox';
    if (['ps','psn','playstation','ps4','ps5'].includes(p)) return 'psn';
    if (['pc','steam','gog','epic'].includes(p)) return 'pc';
    return p === 'demo' ? 'demo' : 'other';
  };
  let indexedLibrary=null,indexedItems=null,indexedGames=null,grouped=new Map(),statsIndex=new Map(),allGames=[];
  function indexData(){
    const lib=typeof DATA==='undefined'?null:DATA.library;
    if(lib!==indexedLibrary||lib?.games!==indexedGames||lib?.achievements!==indexedItems){indexedLibrary=lib;indexedGames=lib?.games;indexedItems=lib?.achievements;allGames=lib?.games||[];grouped=AtlasModel.index(lib?.achievements||[]);statsIndex=new Map([...grouped].map(([id,items])=>[id,AtlasModel.progress(items)]));}
  }
  const gamesInLibrary=()=>{indexData();return allGames;};
  const achievementsFor=id=>{indexData();return grouped.get(id)||[];};
  const gameStats=id=>{indexData();return statsIndex.get(id)||AtlasModel.progress([])};
  const recommendations = () => Object.values(typeof PLATFORM_REPORTS==='undefined'?{}:PLATFORM_REPORTS).flatMap(x=>x.recommendations||[]).filter((r,i,a)=>a.findIndex(x=>x.achievement_id===r.achievement_id)===i);
  const userPins = () => new Set(typeof DATA === 'undefined' ? [] : DATA.state?.pins || []);
  const artworkStyle = (g, kind = 'hero') => {
    if (!g) return '';
    // Use the existing app's safe artwork pipeline; never interpolate arbitrary web URLs.
    if (typeof artStyle !== 'function') return '';
    return artStyle(g, kind) || (kind === 'hero' ? artStyle(g, 'cover') : '');
  };
  const safeDate=text=>AtlasModel.date(text);
  const day = (date) => `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
  let prefs;
  try { prefs = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (_) { prefs = {}; }
  prefs.mode = MODES.includes(prefs.mode) ? prefs.mode : 'cinematic';
  prefs.platform = PLATFORMS.includes(prefs.platform) ? prefs.platform : 'all';
  prefs.motion = prefs.motion === 'reduce' ? 'reduce' : 'auto';
  prefs.focus = typeof prefs.focus === 'string' ? prefs.focus : '';
  prefs.view = VIEWS.includes(prefs.view) ? prefs.view : 'hub';
  prefs.lighting = prefs.lighting && typeof prefs.lighting === 'object' ? prefs.lighting : {};
  let opened = false;
  let consoleMode = false;
  let consoleReturn=null;
  let focusReturn = null;
  let gamesFiltered = [];
  let activeIndex = 0;
  let gamepadLoop = 0;
  let lastPadAction = 0;
  let lastPressed = false;
  let padConnected=null;
  let hallFilter = 'all';
  let timelineDays = 90;
  let search = '';
  let searchTimer=0,lastBackdropCSS=null;
  let gamePage=0,libraryPage=0;
  const persist = () => { try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch (_) {} };
  const relevant = () => gamesInLibrary().filter(g => prefs.platform === 'all' || platformKey(g) === prefs.platform);
  const activeGame = () => relevant().find(g => g.id === prefs.focus) || relevant()[0] || null;
  const platformName = (p) => ({all:'ATLAS UNIFIED',xbox:'XBOX EXPERIENCE',psn:'PLAYSTATION EXPERIENCE',pc:'PC EXPERIENCE'})[p] || 'ATLAS';
  const navTitle = (v) => ({hub:'ATLAS HUB',library:'LIBRARY',game:'GAME UNIVERSE',quests:'QUEST BOARD',hall:'HALL OF FAME',timeline:'UNLOCK TIMELINE',artwork:'ARTWORK STUDIO'})[v] || 'ATLAS';

  function createShell() {
    if (document.getElementById('au-root')) return;
    const top = document.querySelector('.top-right');
    const trigger = document.createElement('button');
    trigger.className = 'au-trigger';
    trigger.type = 'button';
    trigger.textContent = '✦ ATLAS ULTIMATE';
    trigger.setAttribute('aria-label', 'Atlas Ultimate arayüzünü aç');
    trigger.addEventListener('click', open);
    if (top) top.insertBefore(trigger, top.firstChild); else document.body.prepend(trigger);
    const root = document.createElement('div');
    root.id = 'au-root';
    root.className = 'au-root';
    root.hidden = true;
    root.innerHTML = `
      <div class="au-ambient" aria-hidden="true"><div class="au-ambient-image" id="au-backdrop"></div></div>
      <div class="au-layout">
        <aside class="au-sidebar">
          <div class="au-mark"><img src="/brand/atlas-mark.svg" width="42" height="42" alt="Atlas"><div><b>ACHIEVEMENT <em>ATLAS</em></b><small>ULTIMATE EXPERIENCE</small></div></div>
          <nav class="au-navigation" id="au-nav" aria-label="Ultimate sayfaları"></nav>
          <div class="au-sidebar-foot"><span>LOCAL FIRST • NO FABRICATED STATS</span><button type="button" data-au-action="return">← Klasik arayüze dön</button></div>
        </aside>
        <div class="au-main">
          <header class="au-header">
            <div class="au-header-left"><span class="au-live" id="au-live">●</span><span id="au-location">ATLAS HUB</span></div>
            <div class="au-header-right">
              <label class="au-sr" for="au-platform">Platform</label>
              <select id="au-platform" aria-label="Platform seçimi"><option value="all">Tümü</option><option value="xbox">Xbox</option><option value="psn">PlayStation</option><option value="pc">PC</option></select>
              <label class="au-sr" for="au-mode">Tema</label>
              <select id="au-mode" aria-label="Görünüm teması"><option value="cinematic">Cinematic</option><option value="blades">360 Blades</option><option value="nxe">360 NXE</option><option value="xmb">PS3 XMB</option></select>
              <button type="button" class="au-chip au-console-launch" data-au-action="console">▣ Console Mode</button>
              <button type="button" class="au-icon" data-au-action="return" aria-label="Atlas Ultimate kapat">✕</button>
            </div>
          </header>
          <main id="au-content" class="au-content" tabindex="-1" aria-live="polite"></main>
        </div>
      </div>
      <dialog class="au-console" id="au-console" aria-label="Console Mode">
        <div class="au-console-image" id="au-console-image"></div>
        <div class="au-console-top"><b>ATLAS <span>CONSOLE</span></b><button type="button" data-au-action="exit-console">✕ Çıkış <small>Esc / B</small></button></div>
        <div class="au-console-center"><span id="au-console-platform">OYUN KÜTÜPHANESİ</span><h1 id="au-console-title">—</h1><p id="au-console-stats">—</p><button type="button" data-au-action="console-open">OYUN DETAYLARINI AÇ ↗</button></div>
        <div class="au-console-rail" id="au-console-rail"></div>
        <div class="au-console-guide">← → / D-PAD: OYUN SEÇ • ENTER / A: AÇ • ESC / B: ÇIK <span id="au-pad-status" role="status"></span></div>
      </dialog>`;
    document.body.appendChild(root);
    root.addEventListener('click', onClick);
    root.addEventListener('change', onChange);
    root.addEventListener('input', onInput);
    document.addEventListener('keydown', onKeyDown,true);
    $u('console').addEventListener('cancel',e=>{e.preventDefault();closeConsole()});
    const navs = [ ['hub','◈','Komuta Merkezi'], ['library','▦','Oyun Kütüphanesi'], ['game','▧','Game Universe'], ['quests','✧','Quest Board'], ['hall','♛','Hall of Fame'], ['timeline','◷','Zaman Çizelgesi'], ['artwork','◉','Artwork Studio'] ];
    $u('nav').innerHTML = navs.map(([view,icon,title]) => `<button type="button" class="au-nav-link" data-au-view="${view}"><span>${icon}</span><b>${title}</b></button>`).join('');
  }
  function updateTheme() {
    const root = $u('root');
    root.dataset.platform = prefs.platform;
    root.dataset.skin = prefs.mode;
    root.dataset.reduce = prefs.motion;
    $u('platform').value = prefs.platform;
    $u('mode').value = prefs.mode;
    $u('location').textContent = navTitle(prefs.view);
    $u('live').textContent = typeof DATA !== 'undefined' && DATA.status?.connected ? '● SERVİS OTURUMU' : '● YEREL KAYITLAR';
    $u('nav').querySelectorAll('[data-au-view]').forEach(b => b.classList.toggle('current', b.dataset.auView === prefs.view));
    const g = activeGame();
    const nextBackdropCSS = g ? artworkStyle(g) : '';
    if(nextBackdropCSS !== lastBackdropCSS){
      const backdrop=$u('backdrop');
      const noMotion=prefs.motion==='reduce'||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
      if(lastBackdropCSS && !noMotion){
        backdrop.parentNode.querySelectorAll('.au-ambient-fading').forEach(el=>el.remove());
        const fading=backdrop.cloneNode(false);
        fading.removeAttribute('id');
        fading.classList.add('au-ambient-fading');
        backdrop.parentNode.insertBefore(fading,backdrop.nextSibling);
        requestAnimationFrame(()=>fading.classList.add('au-fade-out'));
        window.setTimeout(()=>fading.remove(),570);
      }
      backdrop.style.cssText=nextBackdropCSS;
      if(!nextBackdropCSS)backdrop.style.backgroundImage='none';
      lastBackdropCSS=nextBackdropCSS;
    }
    const adj = lighting(g);
    $u('backdrop').style.setProperty('--au-brightness',String(adj.brightness));
    $u('backdrop').style.setProperty('--au-blur',adj.blur+'px');
    $u('backdrop').style.backgroundPosition = adj.focus+'% center';
  }
  function lighting(g) {
    const a = g && prefs.lighting[fileKey(g.id)] || {};
    return {brightness:clamp(a.brightness ?? 64,25,100),blur:clamp(a.blur ?? 0,0,12),focus:clamp(a.focus ?? 50,0,100)};
  }
  const totalFor = (items) => items.reduce((acc,g) => {const p=gameStats(g.id);return {games:acc.games+1,earned:acc.earned+p.earned,total:acc.total+p.total,points:acc.points+(platformKey(g)==='xbox'?p.earnedG:0)}}, {games:0,earned:0,total:0,points:0});
  const metric = (label,value,footer='') => `<div class="au-metric"><small>${html(label)}</small><strong>${html(value)}</strong><span>${html(footer)}</span></div>`;
  const percentage = (p) => p.total > 0 ? `${(100*p.earned/p.total).toFixed(1)}%` : '—';
  const gameCard = (g,small=false) => {const p=gameStats(g.id);const style=artworkStyle(g,'cover');return `<button type="button" class="au-game-card ${small?'au-game-small':''}" data-au-game="${html(g.id)}" aria-label="${html(g.name)} detaylarını aç">
    <span class="au-card-art" style="${html(style)}"><span class="au-card-initial">${html(g.name[0]||'A')}</span></span>
    <span class="au-card-copy"><b>${html(g.name)}</b><small>${html(platformKey(g).toUpperCase())} · ${p.earned}/${p.total} · ${percentage(p)}</small><span class="au-progress"><i style="width:${clamp(p.ratio,0,100)}%"></i></span></span></button>`;};
  function renderHub() {
    const filtered = relevant();
    const g = activeGame();
    const totals = totalFor(filtered);
    const noData = !filtered.length;
    let hero = `<div class="au-featured"><div class="au-featured-art" style="${html(artworkStyle(g))}"></div><div class="au-featured-shadow"></div>
      <div class="au-featured-copy"><span class="au-kicker">✦ ${html(platformName(prefs.platform))} / FOCUS GAME</span>
      <h1>${html(g?.name || 'Bu platformda oyun bulunamadı')}</h1>
      <p>${g ? `${gameStats(g.id).earned} / ${gameStats(g.id).total} kayıtlı başarım kazanıldı. ${html(sample()?'Demo veri · gerçek hesap değil':'Verilerin bu bilgisayarda saklanıyor.')}` : 'Mevcut kütüphaneye oyun ekleyerek sinematik vitrini etkinleştir.'}</p>
      <div class="au-featured-actions">${g?`<button type="button" class="au-primary" data-au-game="${html(g.id)}">OYUN EVRENİNİ AÇ ↗</button>`:''}<button type="button" class="au-secondary" data-au-view="library">KÜTÜPHANE</button></div>
      ${g?`<div class="au-hero-progress"><span>${percentage(gameStats(g.id))} · KAYITLI İLERLEME</span><i style="width:${clamp(gameStats(g.id).ratio,0,100)}%"></i></div>`:''}
      </div></div>`;
    if (noData && prefs.platform !== 'all') hero += '<div class="au-banner">Bu platform için gerçek veri sağlayıcısı bağlı değil veya oyun bulunamadı. Bu görünümde veri yok. PC/Steam planlanıyor; PSN için servis erişimi gerekir.</div>';
    const recent = filtered.filter(g=>gameStats(g.id).left > 0).sort((a,b)=>gameStats(b.id).ratio-gameStats(a.id).ratio).slice(0,6);
    const pinned = recommendations().filter(r=>userPins().has(r.achievement_id)).slice(0,3);
    const cards = recent.length ? recent.map(g => gameCard(g,true)).join('') : '<p class="au-empty">Bitmemiş oyun kaydı bulunamadı.</p>';
    return `<section class="au-hub"><div class="au-sup"><span>YOUR GAME UNIVERSE</span><span>${sample()?'DEMO MOD — GERÇEK KAZANIM DEĞİL':'REAL LIBRARY DATA'}</span></div>
    ${hero}<div class="au-metrics">${metric('OYUNLAR',showNum(totals.games),'Kayıtlı oyunlar')}${metric('KAZANILAN',showNum(totals.earned),`${showNum(totals.total)} kayıt içinden`)}${metric('XBOX GAMERSCORE',['psn','pc'].includes(prefs.platform)?'—':showNum(totals.points),['psn','pc'].includes(prefs.platform)?'Bu platformda Gamerscore yok':'Yalnız Xbox kazanımları')}${metric('TAMAMLAMA',totals.total?`${(totals.earned/totals.total*100).toFixed(1)}%`:'—','İçe aktarılmış kayıtlara göre')}</div>
    <div class="au-section-heading"><div><span>CONTINUE YOUR HUNT</span><h2>Yarım kalan <em>maceralara dön</em></h2></div><button data-au-view="library">TÜMÜNÜ GÖR ↗</button></div>
    <div class="au-shelf">${cards}</div>
    <div class="au-bottom-grid"><div class="au-panel"><span class="au-kicker">PINNED OBJECTIVES</span><h3>Hedef panosu</h3>${pinned.length?pinned.map(r=>`<div class="au-goal"><b>${html(r.achievement)}</b><span>${html(r.game)}</span></div>`).join(''):'<p class="au-empty">Henüz sabitlenmiş öneri bulunmuyor.</p>'}<button data-au-view="quests">HEDEFLERE GİT ↗</button></div>
    <div class="au-panel"><span class="au-kicker">YOUR LEGACY</span><h3>Koleksiyon vitrini</h3><p>Gerçek kütüphanende tüm kaydedilmiş başarımları kazanılmış oyunları ve geçmişini gör.</p><button data-au-view="hall">HALL OF FAME ↗</button></div></div></section>`;
  }
  function renderLibrary() {
    const a = relevant().filter(g => String(g.name||'').toLocaleLowerCase('tr').includes(search.toLocaleLowerCase('tr')));
    libraryPage=Math.max(0,Math.min(libraryPage,Math.ceil(a.length/60)-1));
    return `<div class="au-page-head"><span class="au-kicker">ALL YOUR WORLDS</span><h1>Oyun <em>kütüphanesi</em></h1><p>Gerçek kütüphane kayıtları ve kullanıcı tarafından seçilmiş kapaklar.</p></div>
    <label class="au-search-label">OYUN ARA <input id="au-search" data-au-search placeholder="Oyun ismi..." value="${html(search)}"></label>
    <div class="au-gallery">${a.length?a.slice(libraryPage*60,(libraryPage+1)*60).map(g=>gameCard(g)).join(''):'<div class="au-empty">Eşleşen oyun bulunamadı. Başka platform seç veya CSV içe aktar.</div>'}</div>
    ${a.length>60?`<div class="au-tabs"><button data-au-library-page="-1" ${libraryPage===0?'disabled':''}>← Önceki</button><span>${libraryPage+1} / ${Math.ceil(a.length/60)}</span><button data-au-library-page="1" ${libraryPage>=Math.ceil(a.length/60)-1?'disabled':''}>Sonraki →</button></div>`:''}`;
  }
  function renderGame() {
    const g=activeGame();
    if(!g)return `<div class="au-empty au-big-empty">Oyun seçilmedi. Kütüphanene veri ekleyebilirsin.</div>`;
    const p=gameStats(g.id), arr=achievementsFor(g.id),pins=userPins();
    const sorted=[...arr].sort((a,b)=>Number(!!b.unlocked)-Number(!!a.unlocked));
    gamePage=Math.max(0,Math.min(gamePage,Math.ceil(sorted.length/50)-1));
    const rows=sorted.slice(gamePage*50,(gamePage+1)*50).map(a=>`<div class="au-ach-row">${AtlasModel.secret(a)?'<span class="ach-icon missing-art">?</span>':imgIcon(a)}<div class="au-ach-name"><button class="ach-open" data-ach="${html(a.id)}" aria-expanded="false">${html(AtlasModel.secret(a)?'Gizli başarım':a.name)}</button><small>${a.unlocked?'KAZANILDI':'KİLİTLİ'} · ${platformKey(g)==='xbox'?showNum(a.points)+' G':'Başarım kaydı'}${pins.has(a.id)?' · HEDEF':''}</small></div><button type="button" data-au-pin="${html(a.id)}" aria-label="${pins.has(a.id)?'Sabitlemeyi kaldır':'Hedefi sabitle'}" aria-pressed="${pins.has(a.id)}">${pins.has(a.id)?'★':'☆'}</button></div>`).join('');
    return `<div class="au-game-hero"><div class="au-game-hero-art" style="${html(artworkStyle(g))}"></div><div class="au-game-hero-shade"></div>
      <div class="au-game-hero-body"><span class="au-kicker">${html(platformKey(g).toUpperCase())} / GAME UNIVERSE</span><h1>${html(g.name)}</h1><p>${html(deviceLabel(g))} · ${p.earned} / ${p.total} başarım · ${percentage(p)} · ${platformKey(g)==='xbox'?showNum(p.remainingG)+' G kayıtta kaldı':'Platforma göre kalan hedefler'}</p>
      <div class="au-featured-actions"><button class="au-primary" data-au-action="native-game">KLASİK OYUN DETAYI ↗</button><button class="au-secondary" data-au-view="artwork">GÖRSELİ AYARLA</button></div></div></div>
      <div class="au-metrics">${metric('KAZANILAN',p.earned,p.total+' toplam')}${metric('İLERLEME',percentage(p),'Mevcut kayıtlar')}${metric('KALAN',p.left,'Kayıtlı başarımlar')}${metric('GAMERSCORE',platformKey(g)==='xbox'?showNum(p.earnedG):'—', platformKey(g)==='xbox'?'Kazandığın G':'Xbox dışı platform')}</div>
      <div class="au-section-heading"><div><span>ACHIEVEMENT VAULT</span><h2>Oyun <em>başarımları</em></h2></div></div>
      <div class="au-ach-list">${rows||'<div class="au-empty">Bu oyun için başarım kaydı yok.</div>'}</div>${arr.length>50?`<div class="au-tabs"><button data-au-page="-1" ${gamePage===0?'disabled':''}>← Önceki</button><span>${gamePage+1} / ${Math.ceil(arr.length/50)}</span><button data-au-page="1" ${gamePage>=Math.ceil(arr.length/50)-1?'disabled':''}>Sonraki →</button></div>`:''}`;
  }
  function renderQuests() {
    const ids=new Set(relevant().map(g=>g.id)), pins=userPins();
    const recs=recommendations().filter(r=> ids.has(r.game_id));
    const list=recs.slice().sort((a,b)=>Number(pins.has(b.achievement_id))-Number(pins.has(a.achievement_id))).slice(0,30);
    return `<div class="au-page-head"><span class="au-kicker">YOUR NEXT MOVE</span><h1>Quest <em>Board</em></h1><p>Mevcut öneri motoruna ve gerçek kayıtlarına bağlı hedefler.</p></div><div class="au-quest-grid">${list.length?list.map(r=>`<article class="au-quest"><span class="au-kicker">${pins.has(r.achievement_id)?'★ PINNED':'✦ RECOMMENDED'}</span><h3>${html(r.achievement)}</h3><p>${html(r.game)}</p><div class="au-quest-bottom"><span>${platformKey(relevant().find(g=>g.id===r.game_id)||{})==='xbox'?showNum(r.points)+' G':'KUPA'}</span><button type="button" data-ach="${html(r.achievement_id)}">BAŞARIMI AÇ ↗</button></div></article>`).join(''):'<div class="au-empty">Bu platformda önerilecek kilitli başarım yok.</div>'}</div>`;
  }
  function renderHall() {
    const filtered=relevant(), achieved=filtered.filter(g=>{const p=gameStats(g.id);return p.total>0 && p.earned===p.total});
    const collect=filtered.filter(g=>gameStats(g.id).earned>0);
    const selected=hallFilter==='complete'?achieved:hallFilter==='platinum'?filtered.filter(g=>achievementsFor(g.id).some(a=>a.unlocked&&a.platform==='psn'&&a.trophy_type==='platinum')):collect;
    return `<div class="au-page-head"><span class="au-kicker">YOUR GAMING LEGACY</span><h1>Hall of <em>Fame</em></h1><p>Ödül vitrini sadece mevcut kayıtlardan oluşturulur. Tam oyun kapsamı doğrulanmadıkça tamamlanma yalnızca içe aktarılan liste içindir.</p></div>
    <div class="au-hall-head"><span class="au-kicker">COLLECTION ROOM</span><div class="au-hall-count">${showNum(achieved.length)} <small>KAYITLARDA TAMAMLANDI</small></div></div>
    <div class="au-tabs">${[['all','Koleksiyon'],['complete','Kayıtlarda %100'],['platinum','Platin kupalar']].map(([k,name])=>`<button type="button" data-au-hall="${k}" aria-pressed="${k===hallFilter}">${name}</button>`).join('')}</div>
    <div class="au-gallery">${selected.length?selected.slice(0,80).map(g=>gameCard(g)).join(''):'<div class="au-empty">Bu filtrede doğrulanmış kayıt yok. Platin için kazanılmış PSN platinum kaydı gerekir.</div>'}</div>
    <p class="au-disclaimer">%100 etiketi, yalnızca yerel kütüphanedeki başarımların tamamının kazanıldığını gösterir; oyunun bütün resmî DLC/başarımlarının mevcut olduğunu kanıtlamaz.</p>`;
  }
  function renderTimeline() {
    const all=relevant().flatMap(g=>achievementsFor(g.id)).filter(a=>a.unlocked&&safeDate(a.unlock_time));
    const end=new Date();end.setHours(24,0,0,0);
    const begin=new Date(end);begin.setDate(begin.getDate()-timelineDays);
    const size=timelineDays===30?1:timelineDays===90?7:30,arr=[];
    for(let start=new Date(begin);start<end;){const next=new Date(start);next.setDate(next.getDate()+size);if(next>end)next.setTime(end.getTime());arr.push({start:new Date(start),end:new Date(next),n:0});start=next;}
    for(const a of all){const d=safeDate(a.unlock_time);if(d>new Date())continue;const bin=arr.find(b=>d>=b.start&&d<b.end);if(bin)bin.n++;}
    const maximum=Math.max(1,...arr.map(x=>x.n)),total=arr.reduce((s,b)=>s+b.n,0);
    return `<div class="au-page-head"><span class="au-kicker">THE STORY OF YOUR UNLOCKS</span><h1>Başarım <em>zaman çizelgesi</em></h1><p>Yalnız geçerli, kazanılmış tarihli kayıtlar. Eksik tarihler sayılmaz.</p></div><div class="au-tabs">${[30,90,365].map(v=>`<button data-au-range="${v}" aria-pressed="${v===timelineDays}">${v} GÜN</button>`).join('')}</div><div class="au-panel"><p>${total} tarihli kayıt · ${size===1?'Günlük':size===7?'Haftalık':'30 günlük'} gruplar · Yerel takvim</p>${total?`<div class="au-chart" role="img" aria-label="${total} kayıtlı kazanım">${arr.map(b=>`<div class="au-chart-bin"><i style="height:${100*b.n/maximum}%" title="${day(b.start)}: ${b.n}"></i></div>`).join('')}</div>`:'<p class="au-empty">Bu dönemde geçerli tarihli kazanım yok.</p>'}<details><summary>Tarihleri tablo olarak göster</summary><table><thead><tr><th>Başlangıç</th><th>Kazanım</th></tr></thead><tbody>${arr.map(b=>`<tr><td>${day(b.start)}</td><td>${b.n}</td></tr>`).join('')}</tbody></table></details><p class="au-muted">Yalnız yerel kayıt kapsamı. Belirsiz tarihler tahmin edilmez.</p></div>`;
  }
  function renderArtwork() {
    const g=activeGame();if(!g)return '<div class="au-empty au-big-empty">Önce kütüphanene oyun ekle.</div>';
    const p=lighting(g);
    return `<div class="au-page-head"><span class="au-kicker">ARTWORK LIGHTING LAB</span><h1>Wallpaper <em>Atmosphere</em></h1><p>Gerçek artwork dosyasına dokunmadan karartma, bulanıklaştırma ve odak noktası değiştir. Bu ayarlar yalnızca kendi tarayıcında saklanır.</p></div>
      <div class="au-art-preview"><div style="${html(artworkStyle(g))}" class="au-art-image" id="au-art-image"></div><span>${html(g.name)}</span></div>
      ${[['brightness','Görsel parlaklığı',25,100,p.brightness,'%'],['blur','Bulanıklık',0,12,p.blur,'px'],['focus','Yatay odak',0,100,p.focus,'%']].map(([key,label,min,max,value,unit])=>`<div class="au-slider"><label for="au-${key}">${label} <output id="au-output-${key}">${value}${unit}</output></label><input type="range" id="au-${key}" data-au-lighting="${key}" min="${min}" max="${max}" value="${value}"></div>`).join('')}
      <div class="au-featured-actions"><button type="button" data-au-action="native-artwork" class="au-primary">GERÇEK ARTWORK SEÇ ↗</button><button type="button" data-au-action="reset-lighting" class="au-secondary">AYARLARI SIFIRLA</button><button type="button" data-au-action="motion" class="au-secondary">${prefs.motion==='reduce'?'HAREKETİ ETKİNLEŞTİR':'HAREKETİ AZALT'}</button></div>
      <p class="au-disclaimer">Kaynak resimler, mevcut Achievement Atlas görsel önbelleğinden veya izin verilen sağlayıcılardan gelir. Yapay zekâ tarafından görsel üretilmez.</p>`;
  }
  function render() {
    if(!opened)return;
    indexData();
    updateTheme();
    const views={hub:renderHub,library:renderLibrary,game:renderGame,quests:renderQuests,hall:renderHall,timeline:renderTimeline,artwork:renderArtwork};
    $u('content').innerHTML=(views[prefs.view]||renderHub)();
    window.dispatchEvent(new CustomEvent('atlas:ultimate-render'));
    const ap=$u('art-image');const g=activeGame();if(ap&&g){const a=lighting(g);ap.style.filter=`brightness(${a.brightness}%) blur(${a.blur}px)`;ap.style.backgroundPosition=a.focus+'% center';}
  }
  function open() {createShell();focusReturn=document.activeElement;closeInline();opened=true;document.getElementById('app').inert=true;$u('root').setAttribute('role','dialog');$u('root').setAttribute('aria-modal','true');$u('root').setAttribute('aria-label','Atlas Ultimate');$u('root').hidden=false;document.body.classList.add('au-lock');render();$u('content').focus({preventScroll:true});}
  function close() {clearTimeout(searchTimer);closeConsole();opened=false;$u('root').hidden=true;document.body.classList.remove('au-lock');document.getElementById('app').inert=false;focusReturn?.focus?.({preventScroll:true});}
  function go(view) {if(!VIEWS.includes(view))return;closeInline();prefs.view=view;persist();render();$u('content').scrollTop=0;$u('content').focus({preventScroll:true});}
  function focusGame(gid){if(!relevant().some(g=>g.id===gid))return;closeInline();gamePage=0;prefs.focus=gid;prefs.view='game';persist();render();}
  function onClick(e) {
    const libraryButton=e.target.closest('[data-au-library-page]');if(libraryButton){libraryPage+=Number(libraryButton.dataset.auLibraryPage);return render();}
    const pageButton=e.target.closest('[data-au-page]');if(pageButton){gamePage+=Number(pageButton.dataset.auPage);return render();}
    const inline=e.target.closest('[data-ach]');if(inline){e.stopPropagation();expandInline(inline.dataset.ach,inline);return;}
    const t=e.target.closest('[data-au-action],[data-au-view],[data-au-game],[data-au-hall],[data-au-range],[data-au-pin],[data-au-quest],[data-au-console-index]');if(!t)return;
    if(t.dataset.auView) return go(t.dataset.auView);
    if(t.dataset.auGame) return focusGame(t.dataset.auGame);
    if(t.dataset.auHall){hallFilter=t.dataset.auHall;return render();}
    if(t.dataset.auRange){timelineDays=Number(t.dataset.auRange);return render();}
    if(t.dataset.auConsoleIndex!==undefined){activeIndex=Number(t.dataset.auConsoleIndex);return renderConsole();}
    if(t.dataset.auPin){e.stopPropagation();const id=t.dataset.auPin;const state=userPins().has(id);if(typeof api!=='function')return;api('/api/pin',{id,pinned:!state}).then(()=>reload()).then(()=>render()).catch(()=>{if(typeof toast==='function')toast('Hedef kaydedilemedi.',true);});return;}
    if(t.dataset.auQuest){const id=t.dataset.auQuest;close();if(typeof jumpAch==='function')jumpAch(id);return;}
    const action=t.dataset.auAction;
    if(action==='return')return close();
    if(action==='console')return openConsole();
    if(action==='exit-console')return closeConsole();
    if(action==='console-open'){const g=gamesFiltered[activeIndex];if(g){closeConsole();focusGame(g.id);}return;}
    if(action==='native-game'){const g=activeGame();if(g&&typeof openGame==='function'){close();switchPlatform(platformKey(g));openGame(g.id);}return;}
    if(action==='native-artwork'){const g=activeGame();if(typeof navigate==='function'){close();if(g&&typeof switchPlatform==='function')switchPlatform(platformKey(g));navigate('artwork');if(g&&document.getElementById('artGame')){document.getElementById('artGame').value=g.id;renderVisuals();}}return;}
    if(action==='reset-lighting'){const g=activeGame();if(g){delete prefs.lighting[fileKey(g.id)];persist();render();}return;}
    if(action==='motion'){prefs.motion=prefs.motion==='reduce'?'auto':'reduce';persist();render();}
  }
  function onChange(e){if(e.target.id==='au-platform'){prefs.platform=PLATFORMS.includes(e.target.value)?e.target.value:'all';prefs.focus='';persist();render();}
    if(e.target.id==='au-mode'){prefs.mode=MODES.includes(e.target.value)?e.target.value:'cinematic';persist();render();}}
  function onInput(e){if(e.target.dataset.auSearch!==undefined){const pos=e.target.selectionStart;search=e.target.value;libraryPage=0;clearTimeout(searchTimer);searchTimer=setTimeout(()=>{if(!opened||prefs.view!=='library')return;const focused=document.activeElement?.id==='au-search';render();if(focused){$u('search')?.focus();$u('search')?.setSelectionRange(pos,pos)}},100);return;}
    const field=e.target.dataset.auLighting;if(!field)return;const g=activeGame();if(!g)return;const a=lighting(g);a[field]=Number(e.target.value);prefs.lighting[fileKey(g.id)]=a;persist();updateTheme();
    const preview=$u('art-image');if(preview){preview.style.filter=`brightness(${a.brightness}%) blur(${a.blur}px)`;preview.style.backgroundPosition=a.focus+'% center';}
    const output=$u('output-'+field);if(output)output.textContent=e.target.value+(field==='blur'?'px':'%');}
  function openConsole(){if(!opened)return;gamesFiltered=relevant();if(!gamesFiltered.length){if(typeof toast==='function')toast('Bu platformda oyun bulunamadı.',true);return;}activeIndex=Math.max(0,gamesFiltered.findIndex(g=>g.id===prefs.focus));consoleReturn=document.activeElement;consoleMode=true;$u('console').showModal();$u('root').querySelector('.au-layout').inert=true;renderConsole();gamepadTick();$u('console').querySelector('[data-au-action="exit-console"]').focus();}
  function closeConsole(){if(!consoleMode)return;consoleMode=false;$u('console').close();$u('root').querySelector('.au-layout').inert=false;cancelAnimationFrame(gamepadLoop);gamepadLoop=0;lastPressed=false;if(consoleReturn?.isConnected)consoleReturn.focus({preventScroll:true});else $u('content').focus({preventScroll:true});}
  function stepConsole(step){if(!gamesFiltered.length)return;activeIndex=(activeIndex+step+gamesFiltered.length)%gamesFiltered.length;renderConsole();}
  function renderConsole(){if(!consoleMode)return;const g=gamesFiltered[activeIndex];if(!g)return;
    $u('console-image').style=artworkStyle(g);
    $u('console-title').textContent=g.name;$u('console-platform').textContent=platformName(platformKey(g));
    const p=gameStats(g.id);$u('console-stats').textContent=`${p.earned} / ${p.total} başarım • ${percentage(p)} kayıtlı ilerleme`;
    const range=[...new Set([activeIndex-2,activeIndex-1,activeIndex,activeIndex+1,activeIndex+2].map(i=>(i+gamesFiltered.length)%gamesFiltered.length))];
    $u('console-rail').innerHTML=range.map(i=>{const x=gamesFiltered[i];return `<button type="button" class="au-console-card ${i===activeIndex?'selected':''}" data-au-console-index="${i}" aria-label="${html(x.name)}" aria-current="${i===activeIndex}"><span style="${artworkStyle(x,'cover')}"></span><b>${html(x.name)}</b></button>`;}).join('');
    prefs.focus=g.id;persist();updateTheme();
  }
  function gamepadTick(){if(!consoleMode)return;
    try {const pads=navigator.getGamepads?.()||[];const p=Array.from(pads).find(p=>p&&p.connected);
      if(padConnected!==!!p){padConnected=!!p;$u('pad-status').textContent=p?' • GAMEPAD BAĞLI':' • KLAVYE İLE DEVAM EDEBİLİRSİN';}
      if(p){const left=!!(p.buttons[14]?.pressed || p.axes[0]<-.7),right=!!(p.buttons[15]?.pressed || p.axes[0]>.7);const confirm=!!p.buttons[0]?.pressed,back=!!p.buttons[1]?.pressed;
        const now=performance.now();const pressed=left||right||confirm||back;if(pressed&&(!lastPressed||((left||right)&&!confirm&&!back&&now-lastPadAction>260))){
          lastPadAction=now;if(back){closeConsole();return;}if(confirm){const g=gamesFiltered[activeIndex];closeConsole();if(g)focusGame(g.id);return;}if(left)stepConsole(-1);else if(right)stepConsole(1);
        } lastPressed=pressed;
      }else lastPressed=false;
    } catch (_) {} gamepadLoop=requestAnimationFrame(gamepadTick);
  }
  function onKeyDown(e){if(e.altKey&&e.code==='KeyC'){e.preventDefault();if(!opened)open();if(consoleMode)closeConsole();else openConsole();return;}
    if(!opened)return;
    if(e.key==='Tab'&&!consoleMode){const list=[...$u('root').querySelectorAll('button,input,select,a[href]')].filter(x=>!x.disabled&&x.getClientRects().length);const first=list[0],last=list.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}
    if(consoleMode){if(e.key==='Tab'){const list=[...$u('console').querySelectorAll('button:not([disabled])')];if(list.length){const index=list.indexOf(document.activeElement);if(e.shiftKey && index<=0){e.preventDefault();list[list.length-1].focus();}else if(!e.shiftKey && index===list.length-1){e.preventDefault();list[0].focus();}}}if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();closeConsole();} else if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();stepConsole(e.key==='ArrowLeft'?-1:1);} else if(e.key==='Enter' && !e.target.closest('button')){e.preventDefault();const g=gamesFiltered[activeIndex];closeConsole();if(g)focusGame(g.id);}return;}
    if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();close();}
  }
  document.addEventListener('DOMContentLoaded',createShell,{once:true});
  if(document.readyState!=='loading')createShell();
  // Expose a tiny debugging surface, no personal data or tokens.
  window.AtlasUltimate={open,close,refresh:render,parseUnlockDate:safeDate,isOpen:()=>opened,showAchievement:id=>{const a=(DATA.library.achievements||[]).find(x=>x.id===id);if(!a)return;const g=gamesInLibrary().find(g=>g.id===a.game_id);if(!g)return;prefs.platform=platformKey(g);focusGame(g.id);gamePage=Math.floor(achievementsFor(g.id).slice().sort((a,b)=>Number(!!b.unlocked)-Number(!!a.unlocked)).findIndex(x=>x.id===id)/50);render();const button=[...$u('content').querySelectorAll('[data-ach]')].find(b=>b.dataset.ach===id);if(button)expandInline(id,button)}};
})();
