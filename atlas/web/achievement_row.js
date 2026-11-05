'use strict';
// Vault and Universe share the same provider-backed row and inline expansion.
function unlockMarkup(a){
 if(!a.unlocked)return '<p class="unlock-date">Henüz kazanılmadı.</p>';
 const date=AtlasModel.date(a.unlock_time);
 if(!date)return '<p class="unlock-date">Kazanılma tarihi kaynakta yok</p>';
 const dateOnly=/^\d{4}-\d{2}-\d{2}$/.test(a.unlock_time);
 return `<p class="unlock-date"><time datetime="${esc(a.unlock_time)}">${esc(date.toLocaleString('tr-TR',dateOnly?{dateStyle:'medium'}:{dateStyle:'medium',timeStyle:'short'}))}</time>${dateOnly?' · Saat kaynakta yok':' · Yerel saat'}</p>`;
}
function achievementRow(a){
 const secret=AtlasModel.secret(a)&&!$('showSecrets').checked,pin=(DATA.state.pins||[]).includes(a.id),measured=AtlasModel.measured(a);
 return `<article class="achievement-row ${a.unlocked?'earned':''}">${secret?'<span class="ach-icon missing-art" aria-label="Gizli başarım">?</span>':imgIcon(a)}<div class="ach-copy"><h3><button class="ach-open" data-ach="${esc(a.id)}" aria-expanded="false">${esc(achTitle(a))}</button></h3><small>${esc(a.game_name)} · ${esc(deviceLabel(gameById(a.game_id)||{}))} · ${esc(a.dlc||'Temel oyun')} · ${a.unlocked?'Kazanılmış':'Kilitli'}</small><p>${esc(secret?'Hikâye ayrıntıları gizlendi.':a.description||(a.source==='trueachievements_csv'?'CSV açıklama veya ikon içermez. Doğrulanmış sağlayıcıyla zenginleştirilebilir.':'Kaynak açıklama sağlamadı.'))}</p>${unlockMarkup(a)}${!secret&&measured?`<p>Ölçülen ilerleme: ${fmt(measured.current)} / ${fmt(measured.target)}</p>`:''}<small>Veri kaynağı: ${esc(sourceLabel(a))}${a.flag?' · Kaynak erişim bayrağı':''}</small></div><b class="ach-score">${tier(a)}</b><button class="star" data-pin="${esc(a.id)}" aria-label="${pin?'Hedefi kaldır':'Hedefe sabitle'}" aria-pressed="${pin}">${pin?'★':'☆'}</button></article>`;
}
const gameHeroLoads=new Map();let gameHeroSerial=0;
function decodedArt(url){if(!gameHeroLoads.has(url)){const pending=new Promise(resolve=>{const img=new Image();img.onload=()=>resolve(true);img.onerror=()=>resolve(false);img.src=url});gameHeroLoads.set(url,pending);while(gameHeroLoads.size>16)gameHeroLoads.delete(gameHeroLoads.keys().next().value)}return gameHeroLoads.get(url)}
async function applyGameHero(g){
 const serial=++gameHeroSerial,el=$('detailHero');el.style.backgroundImage='none';el.dataset.artState='empty';
 for(const kind of ['hero','banner','screenshot','cover']){const url=visualUrl(g,kind);if(!url)continue;if(!await decodedArt(url))continue;if(serial!==gameHeroSerial)return;el.style=visualStyle(g,kind);el.dataset.artState=kind==='cover'?'cover':'ready';$('detailHint').textContent=kind==='cover'?'Arka plan mevcut kapaktan uyarlanmıştır.':g.plan||'Sağlayıcı görseli';return}
 if(serial===gameHeroSerial)$('detailHint').textContent='Bu oyun için doğrulanmış görsel kaynağı yok. Görseller sekmesinden eşleşmeyi onaylayabilir veya kendi dosyanı seçebilirsin.';
}
document.addEventListener('click',async e=>{if(e.target.closest('[data-universe-art]')){const gid=selectedGame;navigate('artwork');$('artGame').value=gid;renderVisuals();$('artGame').focus()}if(e.target.closest('[data-universe-media]')){const r=await run(()=>api('/api/media/download',{game_id:selectedGame}));if(r)toast(r.message)}});
