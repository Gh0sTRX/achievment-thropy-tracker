'use strict';
// Pure projections. Provider identities are never inferred from names or artwork.
const AtlasModel={
 scope(library,platform='all',device='all'){
  const games=(library.games||[]).filter(g=>(platform==='all'||g.platform===platform)&&(device==='all'||(g.devices||[]).includes(device)));
  const ids=new Set(games.map(g=>g.id));return {games,achievements:(library.achievements||[]).filter(a=>ids.has(a.game_id))};
 },
 index(items){const groups=new Map();for(const a of items){if(!groups.has(a.game_id))groups.set(a.game_id,[]);groups.get(a.game_id).push(a)}return groups},
 progress(items=[]){const earned=items.filter(a=>a.unlocked),sum=a=>a.reduce((s,x)=>s+(Number(x.points)||0),0);return {total:items.length,earned:earned.length,totalG:sum(items),earnedG:sum(earned),left:items.length-earned.length,remainingG:sum(items)-sum(earned),ratio:items.length?100*earned.length/items.length:0,blocked:items.filter(a=>a.flag&&!a.unlocked).length}},
 metrics(items){const got=items.filter(a=>a.unlocked);return {earned:got.length,total:items.length,xboxScore:got.filter(a=>a.platform==='xbox').reduce((s,a)=>s+(Number(a.points)||0),0),psn:got.filter(a=>a.platform==='psn').length}},
 completion(game,items,completeExport){const p=this.progress(items);return {allRecorded:p.total>0&&p.earned===p.total,verified:p.total>0&&p.earned===p.total&&(game.complete_export===true||completeExport===true),platinum:items.some(a=>a.platform==='psn'&&a.trophy_type==='platinum'&&a.unlocked)}},
 date(text){
  if(typeof text!=='string'||!/^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:?\d{2})?)?$/.test(text))return null;
  const [y,m,d]=text.slice(0,10).split('-').map(Number);const day=new Date(y,m-1,d);
  if(day.getFullYear()!==y||day.getMonth()!==m-1||day.getDate()!==d)return null;
  const date=text.length===10?day:new Date(text);return Number.isFinite(date.getTime())?date:null;
 },
 timeline(items){return items.filter(a=>a.unlocked&&this.date(a.unlock_time)).sort((a,b)=>this.date(b.unlock_time)-this.date(a.unlock_time))},
 measured(a){const cur=Number(a.progress_current),target=Number(a.progress_target);return a.progress_current!=null&&a.progress_target!=null&&Number.isFinite(cur)&&Number.isFinite(target)&&target>0?{current:cur,target,value:Math.max(0,Math.min(100,100*cur/target))}:null},
 secret(a){return !a.unlocked&&!!(a.is_secret||a.secret||a.hidden)}
};
if(typeof module!=='undefined')module.exports=AtlasModel;
