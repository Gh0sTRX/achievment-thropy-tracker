/* Reuse the Windows smoke interaction against an empty local archive. */
const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const p=await browser.newPage({viewport:{width:1280,height:860}}),errors=[];
  p.on('pageerror',e=>errors.push(e.message));await p.route('https://**',r=>r.abort());
  await p.goto(JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['0']);
  await p.waitForFunction(()=>window.uiLoaded&&window.AtlasSearch);
  assert.equal(await p.evaluate(()=>DATA.library.games.length),0);
  for(const action of ["navigate('artwork')","switchPlatform('pc')","switchPlatform('psn');navigate('account')","navigate('updates')","navigate('account')","navigate('quests')","navigate('hall')","navigate('profile')"])await p.evaluate(action);
  // Exact synthetic UI scenario executed by the Windows WebView2 smoke test.
  const source=fs.readFileSync('atlas/desktop.py','utf8');
  const script=source.split('if not window.evaluate_js("""')[1]?.split('"""):')[0];
  assert.ok(script,'Native smoke scenario must remain available');
  assert.equal(await p.evaluate(script),true);
  await p.waitForFunction(()=>page==='games'&&document.activeElement?.matches('#gameGrid [data-gid]'));
  const before=await p.evaluate(()=>({id:document.activeElement.dataset.gid,hash:location.hash,length:history.length}));
  await p.evaluate(async()=>{await preferenceQueue;await reload()});
  assert.equal(await p.evaluate(()=>document.activeElement.dataset.gid),before.id,'Refresh must retain card focus');
  assert.equal(await p.evaluate(()=>location.hash),before.hash);
  assert.equal(await p.evaluate(()=>history.length),before.length);
  assert.deepEqual(errors,[]);
  console.log('Native history: exact programmatic inline/search/back scenario, no extra route and stable focus after asynchronous refresh passed (synthetic Chromium)');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
