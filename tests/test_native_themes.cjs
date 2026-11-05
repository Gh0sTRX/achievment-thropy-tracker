const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{const b=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});const p=await b.newPage();await p.route('https://**',r=>r.abort());await p.goto(JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['80']);await p.waitForFunction(()=>window.uiLoaded&&window.AtlasGameRoute);
 for(const [width,height] of [[1920,1080],[1440,900],[980,640],[390,844]]){
  await p.setViewportSize({width,height});
  for(const skin of ['cinematic','blades','nxe','xmb']){
   const state=await p.evaluate(skin=>{const ids=games().map(g=>g.id);DATA.state.ui.theme_skin=skin;DATA.state.ui.high_contrast=true;render();navigate('games');return {ids,after:games().map(g=>g.id)}},skin);assert.deepEqual(state.ids,state.after);
   await p.locator('#gameGrid [data-gid]').first().click();await p.waitForURL('**/#/game/**');
   await p.locator('[data-tab="overview"]').focus();await p.keyboard.press('ArrowRight');assert.equal(await p.locator('[data-tab="achievements"]').getAttribute('aria-selected'),'true');
   assert.equal(await p.locator('#universeContent').getAttribute('role'),'tabpanel');assert.equal(await p.locator('[data-tab="achievements"]').evaluate(n=>n===document.activeElement),true);
   await p.keyboard.press('Escape');await p.waitForURL('**/#games');await p.waitForTimeout(300);
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   if(width===390)assert.ok(await p.locator('.rail').evaluate(n=>n.inert&&n.getBoundingClientRect().right<=1),'mobile sidebar hidden for '+skin);
  }
 }
 console.log('Native themes: 16 viewport/theme combinations, contrast, unchanged identities, tabs, focus and hidden mobile menu passed');await b.close()})().catch(e=>{console.error(e);process.exit(1)});
