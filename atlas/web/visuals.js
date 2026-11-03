'use strict';
let ACTIVE_PLATFORM='xbox', VISUAL_SOURCES=null, PLATFORM_REPORTS={};
const visualThemes={ember:'#e8a18b',ice:'#99cff1',forest:'#b8e5a2',dusk:'#c8b2eb',sunrise:'#f4c483'};
function visualUrl(game,kind='hero'){
 if(!game)return '';
 const value=game[kind+'_url'];
 if(value==='local')return localArt(kind,game.id)+'?v='+encodeURIComponent(game.artwork_meta?.[kind]?.saved_at||DATA.state.sync_at||'1');
 try{const url=new URL(value);const hosts=['steamgriddb.com','xboxlive.com','xbox.com','microsoft.com','s-microsoft.com','playstation.net','playstation.com'];if(url.protocol==='https:'&&!url.username&&!url.password&&hosts.some(h=>url.hostname===h||url.hostname.endsWith('.'+h)))return url.href}catch(e){}
 return '';
}
function cssUrl(url){return 'url('+encodeURI(url).replace(/[()'"<>\s\\]/g,c=>'%'+c.charCodeAt(0).toString(16))+')'}
function visualStyle(game,kind='cover'){
 const url=visualUrl(game,kind);if(!url)return '';
 const theme=game.art_theme||{};
 return `background-image:${cssUrl(url)};background-position:${Number(theme.x??50)}% ${Number(theme.y??38)}%`;
}
function applyAtmosphere(game){
 const hero=visualUrl(game,'hero')||visualUrl(game,'banner')||visualUrl(game,'screenshot');
 const theme=game?.art_theme||{};
 const accent=visualThemes[theme.preset]||game?.artwork_meta?.hero?.accent||game?.artwork_meta?.cover?.accent||({xbox:'#b8e5a2',psn:'#99cff1',pc:'#c8b2eb'})[ACTIVE_PLATFORM];
 document.documentElement.style.setProperty('--lime',accent);
 document.documentElement.style.setProperty('--green',accent);
 document.documentElement.style.setProperty('--ambient-image',hero?cssUrl(hero):'none');
 document.documentElement.style.setProperty('--ambient-position',`${Number(theme.x??50)}% ${Number(theme.y??38)}%`);
 document.body.dataset.platform=ACTIVE_PLATFORM;
 document.body.classList.toggle('has-atmosphere',!!hero);
 $('atmosphereCredit').textContent=hero?`${game.name} · ${(game.artwork_meta?.hero||game.artwork_meta?.banner||{}).provider==='user_file'?'Yerel görsel':(game.artwork_meta?.hero||{}).provider||'Oyun görseli'}`:'Görsel seçilmedi · Sade arka plan';
}
function renderPlatform(){
 if(PLATFORM_REPORTS[ACTIVE_PLATFORM]){RECS=PLATFORM_REPORTS[ACTIVE_PLATFORM].recommendations||[];INSIGHTS=PLATFORM_REPORTS[ACTIVE_PLATFORM].insights||{}}
 document.querySelectorAll('.platform-tabs [data-platform]').forEach(b=>{b.classList.toggle('active',b.dataset.platform===ACTIVE_PLATFORM);b.setAttribute('aria-pressed',String(b.dataset.platform===ACTIVE_PLATFORM))});
 const g=gameById(selectedGame)||games().find(g=>visualUrl(g,'hero'))||games()[0];
 applyAtmosphere(g);
 $('platformNote').textContent=ACTIVE_PLATFORM==='pc'?'PC sağlayıcısı planlanıyor. Bağlantı veya başarım verisi varmış gibi gösterilmez.':`${ACTIVE_PLATFORM==='xbox'?'Xbox':'PlayStation'} kütüphanesi · İstatistikler yalnız bu platforma ait`;
 $('scoreLabel').textContent=ACTIVE_PLATFORM==='psn'?'KAZANILAN KUPALAR':ACTIVE_PLATFORM==='pc'?'STEAM BAŞARIMLARI':'GAMERSCORE';
}
function switchPlatform(platform){
 ACTIVE_PLATFORM=platform;selectedGame=null;achPage=0;
 $('gameDetail').classList.add('hidden');$('achGame').value='all';$('achSearch').value='';$('gameSearch').value='';
 $('publicPlatform').value=platform==='psn'?'psn':'xbox';
 render();
}
async function loadVisualSources(){
 if(VISUAL_SOURCES)return;
 try{const r=await fetch('/api/art/sources');if(!r.ok)throw Error('Kaynak listesi yüklenemedi');VISUAL_SOURCES=await r.json();renderSourceCards()}catch(e){$('artSources').textContent=e.message}
}
function renderSourceCards(){
 if(!VISUAL_SOURCES)return;
 const groups={publisher:'Resmî yayıncı kaynakları',storefront:'Mağazalar',community:'Topluluk arşivleri',metadata:'Oyun veritabanları',homebrew:'Retro ve homebrew'};
 $('artSources').innerHTML=Object.entries(groups).map(([kind,title])=>`<section><h3>${title}</h3><div class="source-grid">${VISUAL_SOURCES.providers.filter(p=>p.category===kind).map(p=>`<article class="source-card"><div class="source-kicker">${esc(p.platforms.join(' / ').toUpperCase())}</div><h4>${esc(p.name)}</h4><p>${esc(p.notes)}</p><small>${p.id==='steamgriddb'?'Uygulama içi arama destekleniyor':'Keşif bağlantısı · otomatik entegrasyon yok'}</small><p class="muted">Erişim: ${esc(({public:'Herkese açık sayfa',public_browser:'Tarayıcıdan görüntüleme',public_repository:'Herkese açık depo',account_or_api_key:'Hesap / API anahtarı',account_may_be_required:'Hesap gerekebilir',twitch_developer_credentials:'Twitch geliştirici erişimi',account_required_for_api:'API için hesap'})[p.access]||p.access)}</p><a href="${esc(p.url)}" class="ghost-link" target="_blank" rel="noopener noreferrer">KAYNAĞI AÇ ↗</a></article>`).join('')}</div></section>`).join('');
}
function renderVisuals(){
 const game=gameById($('artGame').value);const kind=$('localArtKind').value;
 $('localArtControls').classList.toggle('hidden',!game);
 const url=visualUrl(game,kind);
 const preview=$('localArtPreview');preview.style.backgroundImage=url?cssUrl(url):'none';preview.style.backgroundPosition=`${game?.art_theme?.x??50}% ${game?.art_theme?.y??38}%`;
 preview.classList.toggle('transparent-preview',kind==='logo');
 $('artPreviewEmpty').textContent=url?'':'Önce kütüphanenden oyun, ardından kendi görselini seç.';
 const meta=game?.artwork_meta?.[kind];
 $('artProvenance').textContent=meta?`${meta.provider==='user_file'?'Yerel dosya':meta.provider} · ${meta.width} × ${meta.height} · ${new Date(meta.saved_at).toLocaleDateString('tr-TR')}`:game?'Bu kategori için özel görsel seçilmedi.':'';
 $('artSourceLink').classList.toggle('hidden',!meta?.source_url);$('artSourceLink').href=meta?.source_url||'#';
 $('localArtReset').disabled=!game||game[kind+'_url']!=='local';
 $('artTheme').value=game?.art_theme?.preset||'auto';$('artFocusX').value=game?.art_theme?.x??50;$('artFocusY').value=game?.art_theme?.y??38;
 $('artEdition').textContent=game?`${game.name} · ${game.platform.toUpperCase()} · ${game.platform_edition||'Sürüm belirtilmemiş'} · Kimlik: ${game.title_id||'CSV kaydı'}`:'';
 if(game)applyAtmosphere(game);
 loadVisualSources();
}
function initVisuals(){
 document.body.classList.toggle('low-memory',Number(navigator.deviceMemory||8)<=4);
 document.querySelectorAll('.platform-tabs [data-platform]').forEach(b=>b.onclick=()=>switchPlatform(b.dataset.platform));
 $('artGame').addEventListener('change',()=>{$('artConfirm').checked=false;$('artChoices').innerHTML='';renderVisuals()});
 $('localArtKind').onchange=renderVisuals;
 $('sgdbMatches').addEventListener('change',()=>{$('artConfirm').checked=false});
 $('localArtChoose').onclick=()=>$('localArtFile').click();
 $('localArtFile').onchange=async()=>{
  const file=$('localArtFile').files?.[0],g=gameById($('artGame').value),kind=$('localArtKind').value;if(!file||!g)return;
  if(file.size>8000000){toast('Görsel en fazla 8 MB olabilir.',true);return}
  const reader=new FileReader();reader.onerror=()=>toast('Dosya okunamadı.',true);
  reader.onload=async()=>{const r=await run(()=>api('/api/art/upload',{game_id:g.id,kind:kind,image:String(reader.result).split(',')[1]}));if(r){toast(r.message);await reload()}};
  reader.readAsDataURL(file);$('localArtFile').value='';
 };
 $('localArtReset').onclick=async()=>{const g=gameById($('artGame').value);if(!g)return;const r=await run(()=>api('/api/art/reset',{game_id:g.id,kind:$('localArtKind').value}));if(r){toast(r.message);await reload()}};
 const updateFocus=()=>{$('localArtPreview').style.backgroundPosition=`${$('artFocusX').value}% ${$('artFocusY').value}%`};
 $('artFocusX').oninput=updateFocus;$('artFocusY').oninput=updateFocus;
 $('saveArtTheme').onclick=async()=>{const g=gameById($('artGame').value);if(!g)return;const r=await run(()=>api('/api/art/theme',{game_id:g.id,theme:$('artTheme').value,x:Number($('artFocusX').value),y:Number($('artFocusY').value)}));if(r){toast(r.message);await reload()}};
}
