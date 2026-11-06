const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const p=await b.newPage();await p.route('https://**',r=>r.abort());
  await p.goto(JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['80']);
  await p.waitForFunction(()=>window.uiLoaded&&window.AtlasGameRoute);
  const result=await p.evaluate(async()=>{
   ACTIVE_PLATFORM='all';ACTIVE_DEVICE='all';$('catalogueFilter').value='game';
   const a=DATA.library.achievements.find(a=>!a.unlocked&&!a.flag);
   await api('/api/pin',{id:a.id,pinned:true});await reload();navigate('home');
   return {choices:nextMoveChoices(),id:a.id,html:$('recommendations').textContent,cards:$('recommendations').querySelectorAll('.suggest').length};
  });
  assert.ok(result.choices.length<=3);assert.ok(result.choices.some(r=>r.achievement_id===result.id));
  assert.equal(result.cards,result.choices.length);assert.match(result.html,/Kaynak:/);assert.match(result.html,/doğrulanmadı/);
  await p.evaluate(()=>{switchPlatform('psn');navigate('home')});
  assert.equal(await p.evaluate(()=>nextMoveChoices().every(r=>gameById(r.game_id).platform==='psn')),true);
  console.log('Next Move: pinned choice, max three cards, source/unknown labels and platform isolation passed (synthetic)');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
