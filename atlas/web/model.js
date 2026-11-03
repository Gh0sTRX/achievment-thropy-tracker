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
 date(text){if(typeof text!=='string')return null;
 const s=text.trim().replace(/\s+/g,' ').slice(0,100);
 const local=(y,m,d,h=0,min=0,sec=0)=>{
   const x=new Date(y,m-1,d,h,min,sec);
   return x.getFullYear()===y&&x.getMonth()===m-1&&x.getDate()===d&&x.getHours()===h&&x.getMinutes()===min?x:null;
 };
 const clock=(t)=>{
   if(!t)return [0,0,0];
   const x=t.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?$/i);
   if(!x)return null;
   let h=+x[1],m=+x[2],sec=+(x[3]||0);
   if(x[4]){if(h<1||h>12)return null;h=h%12+(x[4].toUpperCase()==='PM'?12:0);}
   return h<24&&m<60&&sec<60?[h,m,sec]:null;
 };
 const iso=s.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:?\d{2})?))?$/i);
 if(iso){
   const y=+iso[1],m=+iso[2],d=+iso[3],t=iso[4];
   if(!local(y,m,d))return null;
   if(!t)return local(y,m,d);
   const timeParts=t.match(/^(\d{2}):(\d{2})(?::(\d{2}))?/);if(!timeParts||+timeParts[1]>23||+timeParts[2]>59||+(timeParts[3]||0)>59)return null;
   if(/Z|[+-]\d{2}:?\d{2}$/i.test(t)){const x=new Date(iso[1]+'-'+iso[2]+'-'+iso[3]+'T'+t.replace(/([+-]\d{2})(\d{2})$/,'$1:$2'));return Number.isFinite(x.getTime())?x:null;}
   const p=t.match(/^(\d{2}):(\d{2})(?::(\d{2}))?/);return p?local(y,m,d,+p[1],+p[2],+(p[3]||0)):null;
 }
 const months={jan:1,january:1,feb:2,february:2,mar:3,march:3,apr:4,april:4,may:5,jun:6,june:6,jul:7,july:7,aug:8,august:8,sep:9,sept:9,september:9,oct:10,october:10,nov:11,november:11,dec:12,december:12};
 let a=s.match(/^(\d{1,2})\s+([A-Za-z]{3,12})\s+(\d{4})(?:\s+(?:at\s+)?(.+))?$/i);
 if(a){const m=months[a[2].toLowerCase()],t=clock(a[4]);return m&&t?local(+a[3],m,+a[1],...t):null;}
 a=s.match(/^([A-Za-z]{3,12})\s+(\d{1,2}),?\s+(\d{4})(?:\s+(?:at\s+)?(.+))?$/i);
 if(a){const m=months[a[1].toLowerCase()],t=clock(a[4]);return m&&t?local(+a[3],m,+a[2],...t):null;}
 a=s.match(/^(\d{1,4})[/.](\d{1,2})[/.](\d{2,4})(?:\s+(?:at\s+)?(.+))?$/i);
 if(a){
   const t=clock(a[4]);if(!t)return null;
   if(a[1].length===4)return local(+a[1],+a[2],+a[3],...t);
   if(a[3].length!==4)return null;
   if(+a[1]>12&&+a[2]<=12)return local(+a[3],+a[2],+a[1],...t);
   if(+a[2]>12&&+a[1]<=12)return local(+a[3],+a[1],+a[2],...t);
 }
 return null;
},
 timeline(items){return items.filter(a=>a.unlocked&&this.date(a.unlock_time)).sort((a,b)=>this.date(b.unlock_time)-this.date(a.unlock_time))},
 measured(a){const cur=Number(a.progress_current),target=Number(a.progress_target);return a.progress_current!=null&&a.progress_target!=null&&Number.isFinite(cur)&&Number.isFinite(target)&&target>0?{current:cur,target,value:Math.max(0,Math.min(100,100*cur/target))}:null},
 secret(a){return !a.unlocked&&!!(a.is_secret||a.secret||a.hidden)}
};
if(typeof module!=='undefined')module.exports=AtlasModel;
