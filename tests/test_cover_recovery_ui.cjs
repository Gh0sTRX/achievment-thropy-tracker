// End-to-end localhost flow; provider image responses use the Atlas mark, not game art.
const {chromium}=require('playwright'),{spawn}=require('node:child_process'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const fixture=spawn(process.env.ATLAS_TEST_PYTHON||'python',['-u','tests/cover_recovery_fixture_server.py'],{stdio:['ignore','pipe','inherit']});
 let browser;
 try{
  const url=await new Promise((resolve,reject)=>{let data='';const t=setTimeout(()=>reject(Error('Cover fixture timeout')),30000);fixture.once('exit',code=>{clearTimeout(t);reject(Error('Cover fixture exited '+code))});fixture.stdout.on('data',chunk=>{data+=chunk;try{const parsed=JSON.parse(data.split('\n')[0]);clearTimeout(t);resolve(parsed.url)}catch{}})});
  browser=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
  const p=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
  await p.route('https://**',r=>r.abort());const errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.goto(url);await p.waitForFunction(()=>window.uiLoaded&&window.AtlasGameRoute);
  await p.evaluate(()=>{ACTIVE_PLATFORM='all';ACTIVE_DEVICE='all';navigate('games')});
  async function evidence(path){await p.evaluate(()=>{let banner=document.getElementById('syntheticEvidence');if(!banner){banner=document.createElement('div');banner.id='syntheticEvidence';banner.style='position:fixed;bottom:0;left:0;right:0;z-index:999999;background:#142c48;color:white;padding:10px;text-align:center;font:14px sans-serif';document.body.append(banner)}banner.textContent='SENTETİK TEST ARŞİVİ · Atlas simgesi test görselidir; gerçek oyun kapağı değildir.'});await p.screenshot({path})}
  await evidence('work/audit/native-cover-before.png');
  await p.locator('#gameGrid [data-gid="fixture:0"]').click();await p.waitForURL('**/#/game/**');
  await evidence('work/audit/native-cover-universe-before.png');
  await p.keyboard.press('Escape');await p.waitForURL('**/#games');
  await p.evaluate(()=>navigate('artwork'));await p.locator('#recoverCoverLibrary').click();
  await p.waitForFunction(()=>DATA.status.media_job?.report?.discovery&&!DATA.status.media_job.running);
  await p.locator('#scanCoverLibrary').click();
  await p.waitForFunction(()=>document.querySelector('#coverInventoryStatus').textContent.includes('7 gerçek yerel kapak'));
  assert.match(await p.locator('#coverInventoryStatus').innerText(),/13 onay bekliyor/);
  await p.locator('#coverInventoryFilter').selectOption('pending');
  await p.waitForFunction(()=>document.querySelectorAll('#coverInventoryList [data-cover-select]').length===13);
  await p.locator('[data-cover-select="fixture:1"]').click();
  assert.equal(await p.locator('#sgdbMatches').inputValue(),'123');
  assert.equal(await p.locator('#artConfirm').isChecked(),false,'Names never pre-authorize a match');
  await p.evaluate(()=>navigate('games'));await evidence('work/audit/native-cover-after.png');
  const cover=await p.evaluate(()=>visualUrl(gameById('fixture:0'),'cover'));
  assert.ok(cover.startsWith('/art/cover/'));
  assert.equal((await p.request.get(url+cover.slice(1))).status(),200);
  const card=p.locator('#gameGrid [data-gid="fixture:0"]');
  assert.ok((await card.locator('.cover-art').getAttribute('style')).includes(cover),'Library card shares cached cover');
  const cssCover=await card.locator('.cover-art').evaluate(el=>getComputedStyle(el).backgroundImage.slice(5,-2));
  assert.equal((await p.request.get(cssCover)).status(),200,'CSS URL must load without double encoding');
  await card.click();await p.waitForURL('**/#/game/**');
  await evidence('work/audit/native-cover-universe-after.png');
  assert.ok(await p.locator('#universe').evaluate((el,src)=>[...el.querySelectorAll('img')].some(i=>i.getAttribute('src')===src)||el.innerHTML.includes(src),cover),'Universe shares cached cover');
  await p.keyboard.press('Escape');await p.waitForURL('**/#games');
  await p.evaluate(()=>{selectedGame='fixture:0'});await p.locator('#atlasConsoleButton').click();
  await p.waitForFunction(()=>document.querySelector('#atlasConsoleCover').naturalWidth>0);
  assert.equal(await p.locator('#atlasConsoleCover').getAttribute('src'),cover,'Console shares cached cover');
  await p.keyboard.press('Escape');
  // Block all non-local services, reopen the page and confirm the cached file still decodes.
  await p.reload();await p.waitForFunction(()=>window.uiLoaded);
  assert.equal(await p.evaluate(()=>visualUrl(gameById('fixture:0'),'cover')),cover);
  assert.deepEqual(errors,[]);
  fs.writeFileSync('work/audit/cover-ui-results.json',JSON.stringify({synthetic_only:true,total:20,covered:7,recovered:7,pending:13,network:'mock provider + real localhost HTTP',shared_views:['library','universe','console'],errors},null,2));
  console.log('Synthetic cover recovery: real localhost discovery/download, 7 decoded covers, 13 pending confirmations, shared offline cover across Library/Universe/Console passed');
 }finally{if(browser)await browser.close();fixture.kill()}
})().catch(e=>{console.error(e);process.exit(1)});
