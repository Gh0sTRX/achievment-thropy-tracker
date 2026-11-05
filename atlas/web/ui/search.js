/* Native universal search. An index is rebuilt only when data or spoiler policy changes. */
(() => {
 'use strict';
 let indexedGames=null,indexedItems=null,reveal=null,index=[],matches=[],active=0,returnFocus=null,timer;
 const dialog=()=>document.getElementById('atlasSearch');
 const input=()=>document.getElementById('atlasSearchQuery');
 function rebuild(){
  const gs=DATA.library.games||[],as=DATA.library.achievements||[],show=Boolean(document.getElementById('showSecrets')?.checked);
  if(gs===indexedGames&&as===indexedItems&&show===reveal)return;
  indexedGames=gs;indexedItems=as;reveal=show;const games=new Map(gs.map(g=>[g.id,g]));
  const labels=g=>[g.name,g.platform,g.platform==='psn'?'PlayStation PSN':g.platform==='xbox'?'Xbox':'PC Steam',deviceLabel(g),g.platform_edition,g.title_id].join(' ');
  index=gs.map(g=>({kind:'game',id:g.id,game:g,title:g.name,text:norm(labels(g))}));
  for(const a of as){const g=games.get(a.game_id);if(!g)continue;const title=AtlasModel.secret(a)&&!show?'Gizli başarım':a.name;
   index.push({kind:'achievement',id:a.id,game:g,item:a,title,text:norm([labels(g),title,a.dlc,AtlasModel.secret(a)&&!show?'':a.provider_id].join(' '))});
  }
 }
 function draw(){
  rebuild();const tokens=input().value.trim().split(/\s+/).map(norm).filter(Boolean),pins=new Set(DATA.state.pins||[]);
  const pinQuery=tokens.includes(norm('sabitlenen'));const terms=tokens.filter(t=>t!==norm('sabitlenen'));
  matches=index.filter(r=>(!pinQuery||pins.has(r.id))&&terms.every(t=>r.text.includes(t)));active=0;
  document.getElementById('atlasSearchCount').textContent=matches.length+' sonuç · en fazla 40 gösterilir';
  document.getElementById('atlasSearchResults').innerHTML=matches.slice(0,40).map((r,i)=>{
   const url=visualUrl(r.game,'cover');return `<button type="button" role="option" id="atlasSearchOption${i}" data-search-result="${i}" aria-selected="${i===0}">${url?`<img src="${esc(url)}" alt="" loading="lazy">`:''}<span><strong>${esc(r.title)}</strong><small>${esc(r.kind==='game'?'Oyun':r.game.name)} · ${esc(deviceLabel(r.game))}${r.item?.dlc?' · '+esc(r.item.dlc):''}${pins.has(r.id)?' · Sabitlenen':''}</small></span></button>`;
  }).join('');select(0);
 }
 function select(next){const nodes=[...document.querySelectorAll('[data-search-result]')];if(!nodes.length){input().removeAttribute('aria-activedescendant');return}active=(next+nodes.length)%nodes.length;nodes.forEach((n,i)=>n.setAttribute('aria-selected',String(i===active)));input().setAttribute('aria-activedescendant',nodes[active].id);nodes[active].scrollIntoView({block:'nearest',behavior:'instant'})}
 function choose(i){const row=matches[i];if(!row)return;returnFocus=null;dialog().close();if(row.kind==='game')openGame(row.game.id);else window.AtlasGameRoute.showAchievement(row.id)}
 function open(query=''){returnFocus=document.activeElement;input().value=query;if(!dialog().open)dialog().showModal();draw();input().focus()}
 function init(){
  const d=dialog();if(!d)return;
  document.getElementById('atlasSearchClose').onclick=()=>d.close();d.addEventListener('close',()=>returnFocus?.isConnected&&returnFocus.focus({preventScroll:true}));
  input().addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(draw,100)});
  input().addEventListener('keydown',e=>{if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();select(active+(e.key==='ArrowDown'?1:-1))}else if(e.key==='Enter'){e.preventDefault();choose(active)}});
  d.addEventListener('click',e=>{const b=e.target.closest('[data-search-result]');if(b)choose(Number(b.dataset.searchResult))});
  document.addEventListener('keydown',e=>{const typing=/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)||e.target.isContentEditable;
   if((e.key.toLowerCase()==='k'&&(e.ctrlKey||e.metaKey))||(e.key==='/'&&!typing)){e.preventDefault();e.stopImmediatePropagation();open()}
  },true);
  document.getElementById('globalSearchForm').onsubmit=e=>{e.preventDefault();open(document.getElementById('globalSearch').value)};
  window.AtlasSearch={open,rebuild};
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
