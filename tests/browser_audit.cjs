/* Native shell audit; start tests/audit_fixture_server.py. All records are synthetic. */
const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const urls=JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'));
 const browser=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1440,height:900},timezoneId:'Europe/Istanbul'});
 await context.route('https://**',r=>r.abort());const p=await context.newPage(),errors=[],metrics={};p.on('pageerror',e=>errors.push(e.message));
 for(const size of ['5000','15000','40000']){
  const response=p.waitForResponse(r=>r.url().endsWith('/api/data'));await p.goto(urls[size]);const data=await response;await p.waitForFunction(()=>window.uiLoaded&&window.AtlasSearch);
  metrics[size]=await p.evaluate(()=>{
   const timed=fn=>{const start=performance.now();fn();document.querySelector('.page:not(.hidden)').getBoundingClientRect();return +(performance.now()-start).toFixed(2)};
   const home=timed(()=>render()),library=timed(()=>navigate('games')),warm=timed(()=>renderGames());
   const search=timed(()=>AtlasSearch.open('ps3')),results=document.querySelectorAll('[data-search-result]').length;document.querySelector('#atlasSearch').close();
   return {hub_script_layout_ms:home,library_script_layout_ms:library,warm_library_ms:warm,first_search_ms:search,result_nodes:results,game_nodes:document.querySelectorAll('#gameGrid [data-gid]').length};
  });metrics[size].payload_bytes=Number(await data.headerValue('content-length'));assert.ok(metrics[size].game_nodes<=80);assert.ok(metrics[size].result_nodes<=40);
  // Replacing arrays plus a revision must invalidate cached scope and progress.
  const invalidation=await p.evaluate(()=>{const original=DATA.library;DATA.library={...original,games:original.games.slice(0,2),achievements:original.achievements.filter(a=>original.games.slice(0,2).some(g=>g.id===a.game_id))};libraryRevision++;render();return {games:games().length,items:achievements().length,cards:document.querySelectorAll('#gameGrid [data-gid]').length}});assert.equal(invalidation.games,2);assert.equal(invalidation.cards,2);assert.ok(invalidation.items>0);
 }
 await p.goto(urls['80']);await p.waitForFunction(()=>window.uiLoaded&&window.AtlasConsole);
 // Actual Gamepad API polling, with a simulated standard controller.
 await p.evaluate(()=>{window.testPad={connected:true,axes:[0,0],buttons:Array.from({length:16},()=>({pressed:false}))};Object.defineProperty(navigator,'getGamepads',{value:()=>{window.padReads=(window.padReads||0)+1;return [window.testPad]},configurable:true});window.dispatchEvent(new Event('gamepadconnected'));navigate('games');document.querySelector('#gameGrid [data-gid]').focus()});
 async function press(n){const down=await p.evaluate(n=>{window.testPad.buttons[n].pressed=true;return window.padReads||0},n);await p.waitForFunction(reads=>window.padReads>=reads+2,down);const up=await p.evaluate(n=>{window.testPad.buttons[n].pressed=false;return window.padReads},n);await p.waitForFunction(reads=>window.padReads>=reads+2,up)}
 await press(0);await p.waitForURL('**/#/game/**');await press(5);assert.equal(await p.locator('[data-tab="achievements"]').getAttribute('aria-selected'),'true');
 const pinTarget=await p.locator('#universeContent [data-ach]').first().getAttribute('data-ach');const wasPinned=await p.evaluate(id=>DATA.state.pins.includes(id),pinTarget);await p.locator('#universeContent [data-ach]').first().focus();await press(2);await p.waitForFunction(({id,before})=>DATA.state.pins.includes(id)!==before,{id:pinTarget,before:wasPinned});
 await press(3);assert.equal(await p.locator('#atlasSearch').isVisible(),true);await press(1);assert.equal(await p.locator('#atlasSearch').isVisible(),false);
 await press(1);await p.waitForURL('**/#games');await p.evaluate(()=>{window.testPad.connected=false});
 for(const [width,height] of [[1920,1080],[1440,900],[980,640],[390,844]]){await p.setViewportSize({width,height});await p.evaluate(()=>navigate('home'));await p.waitForTimeout(300);assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await p.screenshot({path:`work/audit/native-${width}x${height}.png`,fullPage:false})}
 await p.emulateMedia({reducedMotion:'reduce'});assert.equal(await p.evaluate(()=>AtlasMotion.enabled()),false);
 assert.equal(await p.evaluate(()=>window.pwned),undefined);assert.deepEqual(errors,[]);
 const result={synthetic:true,metrics,page_errors:errors,gamepad:'standard API simulated; A route, RB tab, X pin, Y search, B search close/back; no physical device',resolutions:[1920,1440,980,390]};fs.writeFileSync('work/audit/browser-results.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
