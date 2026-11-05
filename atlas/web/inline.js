'use strict';
let inlineSelection=null;
function detailMarkup(a,revealed=false){
 const secret=AtlasModel.secret(a)&&!$('showSecrets').checked&&!revealed,pin=(DATA.state.pins||[]).includes(a.id),measured=AtlasModel.measured(a),source=safeLink(a.source_url);
 return `<div class="inline-title"><span class="eyebrow">${esc(sourceLabel(a))}</span><button class="secondary" data-inline-close aria-label="Başarım ayrıntısını kapat">✕</button></div><div class="inline-body">${secret?'<span class="ach-icon missing-art">?</span>':imgIcon(a)}<div><h3 id="inline-achievement-title">${esc(secret?'Gizli başarım':a.name)}</h3><p>${esc(a.game_name)} · ${esc(deviceLabel((DATA.library.games||[]).find(g=>g.id===a.game_id)||{}))}</p>${tier(a)} <span class="status-tag">${a.unlocked?'KAZANILDI':'KİLİTLİ'}</span>${secret?'<p>Bu başarım hikâye ayrıntısı içerebilir.</p><button class="secondary" data-inline-reveal>GİZLİ AYRINTILARI GÖSTER</button>':`<p>${esc(a.description||'Sağlayıcı açıklama bildirmedi.')}</p>${measured?`<p>Sağlayıcının bildirdiği ilerleme: ${fmt(measured.current)} / ${fmt(measured.target)}</p><progress max="100" value="${measured.value}" aria-label="Gerçek API ilerlemesi"></progress>`:''}${unlockMarkup(a)}${a.unlock_time_raw?`<details><summary>Kaynak tarih değeri</summary><p>${esc(a.unlock_time_raw)}</p></details>`:''}${a.rarity_source&&a.rarity_percent!=null?`<p>${esc(a.rarity_source)} · %${esc(a.rarity_percent)}</p>`:''}${a.flag?'<p>Kaynak erişim riski işaretlemiş; canlı sunucu durumu doğrulanmadı.</p>':''}${guideMarkup(a)}${communityLinks(a)}`}</div></div><div class="detail-buttons"><button class="secondary" data-pin="${esc(a.id)}" aria-pressed="${pin}">${pin?'★ HEDEFİ KALDIR':'☆ HEDEFE SABİTLE'}</button>${source?`<a class="ghost-link" href="${esc(source)}" target="_blank" rel="noopener noreferrer">KAYNAĞI AÇ ↗</a>`:''}</div>`;
}
function closeInline(){const el=document.querySelector('.inline-achievement');if(el){const trigger=inlineSelection?.trigger;trigger?.setAttribute('aria-expanded','false');el.remove();if(trigger?.isConnected)trigger.focus({preventScroll:true})}inlineSelection=null;}
function expandInline(id,anchor){
 const a=(DATA.library.achievements||[]).find(a=>a.id===id);if(!a)return;
 let trigger=anchor||document.activeElement;
 let host=trigger?.closest?.('.achievement-row,.suggest,.timeline li');
 if(!host){navigate('achievements');$('achStatus').value='all';$('achGame').value=a.game_id;$('achSearch').value='';achPage=Math.floor(achForGame(a.game_id).findIndex(x=>x.id===id)/SIZE);renderAchievements();trigger=[...$('achievementList').querySelectorAll('[data-ach]')].find(b=>b.dataset.ach===id);host=trigger?.closest('.achievement-row')}
 if(!host)return;
 if(inlineSelection?.id===id&&document.querySelector('.inline-achievement')?.previousElementSibling===host){closeInline();return}
 closeInline();inlineSelection={id,trigger,revealed:false};
 const panel=document.createElement('section');panel.className='inline-achievement';panel.setAttribute('role','region');panel.setAttribute('aria-labelledby','inline-achievement-title');panel.innerHTML=detailMarkup(a);host.insertAdjacentElement('afterend',panel);trigger?.setAttribute('aria-expanded','true');
 if(!matchMedia('(prefers-reduced-motion:reduce)').matches&&!DATA.state.ui?.reduced_motion)panel.animate([{opacity:0,transform:'translateY(-8px)',maxHeight:'0px'},{opacity:1,transform:'translateY(0)',maxHeight:panel.scrollHeight+'px'}],{duration:220,easing:'ease-out'});
}
jumpAch=id=>expandInline(id);
document.addEventListener('click',e=>{if(e.target.closest('[data-inline-close]')){closeInline();return}if(e.target.closest('[data-inline-reveal]')&&inlineSelection){const a=(DATA.library.achievements||[]).find(a=>a.id===inlineSelection.id);inlineSelection.revealed=true;document.querySelector('.inline-achievement').innerHTML=detailMarkup(a,true)}});
let inlineBeforeRender=null;
window.addEventListener('atlas:before-render',()=>{inlineBeforeRender=inlineSelection;inlineSelection=null});
window.addEventListener('atlas:render',()=>{const old=inlineBeforeRender;inlineBeforeRender=null;if(old){const trigger=[...document.querySelectorAll('.page:not(.hidden) [data-ach]')].find(b=>b.dataset.ach===old.id&&b.getClientRects().length);if(trigger)expandInline(old.id,trigger)}});


function renderTransfers(){
 const jobs=DATA.status||{},active=[['public_job','Profil'],['media_job','Görseller'],['guide_job','Rehberler'],['job','Xbox'],['art_job','İkonlar']].filter(([key])=>jobs[key]?.running);
 $('transferDock').classList.toggle('hidden',!active.length);$('transferText').textContent=active.map(([key,name])=>`${name}: ${jobs[key].stopping?'durduruluyor…':`${jobs[key].done||0}/${jobs[key].total||'?'}`}`).join(' · ');
 $('stopProfile').classList.toggle('hidden',!jobs.public_job?.running&&!jobs.job?.running);$('stopMedia').classList.toggle('hidden',!jobs.media_job?.running&&!jobs.art_job?.running);
}
document.addEventListener('click',async e=>{const button=e.target.closest('[data-stop]');if(!button)return;button.disabled=true;try{const r=await api('/api/downloads/stop',{kind:button.dataset.stop});toast(r.message)}catch(e){toast(e.message,true)}finally{button.disabled=false}});



function liftFeedback(){for(const id of ['transferDock','notification']){const el=$(id);if(el)document.body.appendChild(el)}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',liftFeedback,{once:true});else liftFeedback();
