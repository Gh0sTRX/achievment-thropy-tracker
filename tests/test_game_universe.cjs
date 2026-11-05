/* Native route integration, synthetic data only. Start audit_fixture_server.py. */
const {chromium}=require('playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const urls=JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'));
 const browser=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 const results=[];
 for(const [width,height] of [[1920,1080],[1440,900],[980,640],[390,844]]){
  const context=await browser.newContext({viewport:{width,height},reducedMotion:'reduce'});
  await context.route('https://**',r=>r.abort());const p=await context.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.goto(urls['80']);await p.waitForFunction(()=>typeof DATA!=='undefined'&&DATA?.library?.games?.length>0);
  await p.evaluate(()=>navigate('games'));
  const card=p.locator('#gameGrid [data-gid]').first();const gid=await card.getAttribute('data-gid');await card.focus();await card.click();
  await p.waitForURL('**/#/game/**');assert.equal(await p.locator('#universe').isVisible(),true);assert.equal(await p.locator('#games').isVisible(),false);
  assert.equal(await p.locator('#detailName').evaluate(n=>n===document.activeElement),true);
  for(const tab of ['achievements','goals','artwork','timeline','dlc','notes']){await p.locator(`[data-tab="${tab}"]`).click();assert.ok(await p.locator('#universeContent').innerHTML())}
  await p.locator('#gameNotes').fill('unsaved local draft');await p.evaluate(()=>render());assert.equal(await p.locator('#gameNotes').inputValue(),'unsaved local draft');
  await p.keyboard.press('Escape');await p.waitForURL('**/#games');await p.waitForFunction(()=>document.activeElement?.matches('#gameGrid [data-gid]')); 
  await p.goForward();await p.waitForURL('**/#/game/**');assert.equal(await p.locator('#universe').isVisible(),true);
  await p.reload();await p.waitForFunction(()=>document.querySelector('#universe:not(.hidden)'));
  assert.equal(await p.evaluate(()=>window.pwned),undefined);assert.deepEqual(errors,[]);
  assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  results.push({width,height,gid,checks:'route, back/forward, deep link, focus, tabs, unsaved draft, escaped fixture, no horizontal overflow'});await context.close();
 }
 console.log(JSON.stringify(results));fs.writeFileSync('work/audit/game-universe-results.json',JSON.stringify(results,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
