/* Optional developer validation: Playwright + Chromium; no production dependency.
   Start work/audit/serve_audit.py (temporary synthetic data only) before running. */
const {chromium}=require('playwright'),fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
 const urls=JSON.parse(fs.readFileSync(process.env.ATLAS_AUDIT_URLS||'work/audit/fixture-urls.json','utf8'));
 const browser=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1440,height:900},timezoneId:'Europe/Istanbul'});
 await context.route('https://**',route=>route.abort());const page=await context.newPage(),errors=[],metrics={};
 page.on('pageerror',e=>errors.push(e.message));
 for(const size of ['15000','40000']){
  const response=page.waitForResponse(r=>r.url().endsWith('/api/data'));await page.goto(urls[size]);const data=await response;const payloadBytes=Number(await data.headerValue('content-length'));
  await page.waitForFunction(()=>typeof AtlasUltimate==='object'&&document.querySelector('#sourceStatus').textContent.length>0);
  const measure=await page.evaluate(()=>{const start=performance.now();AtlasUltimate.open();document.querySelector('#au-content').getBoundingClientRect();return performance.now()-start});
  const library=await page.evaluate(()=>{const start=performance.now();document.querySelector('[data-au-view="library"]').click();document.querySelector('#au-content').getBoundingClientRect();return {ms:performance.now()-start,cards:document.querySelectorAll('#au-content .au-game-card').length}});
  assert.equal(library.cards,60);await page.click('[data-au-library-page="1"]');assert.equal(await page.locator('#au-content .au-game-card').count(),60);
  metrics[size]={hub_script_layout_ms:+measure.toFixed(2),library_script_layout_ms:+library.ms.toFixed(2),cards:library.cards,payload_bytes:payloadBytes};
  // Replacing arrays must invalidate V5's cached game/achievement counts.
  await page.evaluate(()=>{DATA.library.games=DATA.library.games.slice(0,2);const ids=new Set(DATA.library.games.map(g=>g.id));DATA.library.achievements=DATA.library.achievements.filter(a=>ids.has(a.game_id));AtlasUltimate.refresh()});
  assert.equal(await page.locator('#au-content .au-game-card').count(),2);
 }
 await page.goto(urls['80']);await page.waitForFunction(()=>document.querySelector('#sourceStatus').textContent.length>0);
 await page.evaluate(()=>{navigate('achievements');document.querySelector('#achGame').value='audit-game-1';renderAchievements()});
 await page.click('#achievementList [data-ach="audit-ach-1"]');assert.equal(await page.locator('.inline-achievement').count(),1);assert.equal(await page.locator('#achievementDrawer').evaluate(e=>e.open),false);
 await page.click('[data-inline-reveal]');assert.equal(await page.evaluate(()=>window.pwned),undefined);
 await page.evaluate(()=>switchPlatform('xbox'));await page.click('.au-trigger');await page.click('[data-au-view="library"]');assert.equal(await page.locator('#au-content .au-game-card').count(),4,'V5 all scope must not inherit Classic Xbox scope');
 await page.click('#au-content [data-au-game="audit-game-1"]');assert.equal(await page.locator('#au-content .au-ach-row').first().textContent().then(t=>t.includes(' G')),false);
 await page.click('#au-content [data-ach="audit-ach-1"]');assert.equal(await page.locator('#au-content .inline-achievement').count(),1);
 for(const [w,h]of [[1920,1080],[1440,900],[980,640],[390,844]]){
  await page.setViewportSize({width:w,height:h});for(const view of ['hub','library','game','quests','hall','timeline','artwork']){
   await page.click(`[data-au-view="${view}"]`);assert.equal(await page.evaluate(()=>document.querySelector('#au-root').scrollWidth>innerWidth+1),false,view+' overflow '+w);
   if(w===1440||w===390)await page.screenshot({path:`work/audit/${view}-${w}.png`});
  }
 }
 await page.setViewportSize({width:1440,height:900});await page.click('[data-au-action="console"]');
 await page.evaluate(()=>{window.auditPad={connected:true,axes:[0,0],buttons:Array.from({length:16},()=>({pressed:false}))};Object.defineProperty(navigator,'getGamepads',{value:()=>window.auditPad?[window.auditPad]:[]})});
 const first=await page.locator('#au-console-title').textContent();await page.evaluate(()=>auditPad.buttons[15].pressed=true);await page.waitForTimeout(70);await page.evaluate(()=>auditPad.buttons[15].pressed=false);assert.notEqual(await page.locator('#au-console-title').textContent(),first);
 await page.waitForTimeout(60);await page.evaluate(()=>auditPad.axes[0]=-1);await page.waitForTimeout(70);await page.evaluate(()=>auditPad.axes[0]=0);assert.equal(await page.locator('#au-console-title').textContent(),first);
 for(let i=0;i<12;i++){await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.querySelector('#au-console').contains(document.activeElement)),true)}
 await page.evaluate(()=>window.auditPad=null);await page.waitForTimeout(70);assert.ok((await page.locator('#au-pad-status').textContent()).includes('KLAVYE'));await page.keyboard.press('Escape');assert.equal(await page.locator('#au-console').evaluate(e=>e.open),false);
 await page.click('[data-au-action="console"]');await page.evaluate(()=>{auditPad={connected:true,axes:[0,0],buttons:Array.from({length:16},(_,i)=>({pressed:i===0}))}});await page.waitForTimeout(80);assert.equal(await page.locator('#au-console').evaluate(e=>e.open),false);
 await page.evaluate(()=>auditPad.buttons[0].pressed=false);await page.click('[data-au-action="console"]');await page.evaluate(()=>auditPad.buttons[1].pressed=true);await page.waitForTimeout(80);assert.equal(await page.locator('#au-console').evaluate(e=>e.open),false);
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.evaluate(()=>{const el=document.createElement('div');el.id='audit-art';document.body.append(el);window.auditArt=new AtlasArtTransition(el,u=>u.startsWith('/art/'));auditArt.show('/art/hero/audit-game-0/file',true)});
 await page.waitForFunction(()=>auditArt.current.length>0);const good=await page.evaluate(()=>auditArt.current);
 await page.evaluate(()=>auditArt.show('/art/hero/audit-missing/file',true));await page.waitForFunction(()=>document.querySelector('#audit-art').dataset.artState==='error');assert.equal(await page.evaluate(()=>auditArt.current),good);assert.equal(await page.evaluate(()=>!!auditArt.fade),false);
 assert.equal(await page.evaluate(()=>window.pwned),undefined);assert.deepEqual(errors,[]);
 const result={metrics,viewports:['1920x1080','1440x900','980x640','390x844'],checks:['inline details','spoiler reveal','platform separation','cache invalidation','pagination','simulated gamepad axes/d-pad/A/B','focus trap','disconnect fallback','reduced motion','failed artwork retains prior image','escaped XSS fixture'],page_errors:errors};
 fs.writeFileSync('work/audit/browser-results.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
