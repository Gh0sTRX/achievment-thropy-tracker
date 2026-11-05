/* Native transfer protocol: real HTTP, synthetic fixture only. */
const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 const p=await b.newPage({viewport:{width:1440,height:900}}),errors=[];p.on('pageerror',e=>errors.push(e.message));await p.route('https://**',r=>r.abort());
 await p.goto(JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['80']);await p.waitForFunction(()=>window.uiLoaded&&window.AtlasGameRoute);
 const initial=await p.evaluate(()=>{window.transferGames=DATA.library.games;window.transferItems=DATA.library.achievements;return {id:DATA.library.achievements[0].id,pinned:DATA.state.pins.includes(DATA.library.achievements[0].id),game:DATA.library.games[0].id,note:'Transfer '+Date.now()}});
 let response=p.waitForResponse(r=>r.url().endsWith('/api/data'));
 await p.evaluate(async ({id,pinned})=>{await api('/api/pin',{id,pinned:!pinned});await reload()},initial);
 let body=await (await response).json();assert.equal(body.library_unchanged,true);assert.equal(body.library.library,null);
 assert.equal(await p.evaluate(()=>DATA.library.games===window.transferGames&&DATA.library.achievements===window.transferItems),true);
 assert.equal(await p.evaluate(id=>DATA.state.pins.includes(id),initial.id),!initial.pinned);
 response=p.waitForResponse(r=>r.url().endsWith('/api/data'));
 await p.evaluate(async ({game,note})=>{await api('/api/game/notes',{game_id:game,notes:note});await reload()},initial);
 body=await (await response).json();assert.equal(body.library_unchanged,false);assert.equal(await p.evaluate(()=>DATA.library.games===window.transferGames),false);
 assert.equal(await p.evaluate(id=>DATA.library.games.find(g=>g.id===id).notes,initial.game),initial.note);
 await p.evaluate(()=>navigate('artwork'));await p.locator('#checkArtHealth').click();await p.waitForFunction(()=>document.querySelector('#artHealth').textContent.includes('4 oyun'));
 // A slow old response must not overwrite a later refresh.
 const base=await p.evaluate(async()=>await (await fetch('/api/data',{cache:'no-store'})).json());let held,resolveFirst;const firstSeen=new Promise(r=>resolveFirst=r);let requests=0;
 await p.route('**/api/data',route=>{requests++;if(requests===1){held=route;resolveFirst();return}const next=JSON.parse(JSON.stringify(base));next.library.state.log=['latest-response'];return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(next)})});
 await p.evaluate(()=>{window.slowTransfer=reload()});await firstSeen;
 await p.evaluate(async()=>await reload());const old=JSON.parse(JSON.stringify(base));old.library.state.log=['stale-response'];await held.fulfill({status:200,contentType:'application/json',body:JSON.stringify(old)});await p.evaluate(()=>window.slowTransfer);
 assert.deepEqual(await p.evaluate(()=>DATA.state.log),['latest-response']);assert.deepEqual(errors,[]);
 console.log('Native transfer: gzip browser decode, partial pin refresh preserves array identity, notes invalidate, artwork health POST and stale reload ordering passed');await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
