const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const p=await b.newPage();await p.route('https://**',r=>r.abort());await p.goto(JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['80']);await p.waitForFunction(()=>window.uiLoaded&&window.AtlasGameRoute);
  for(const view of ['vault','universe']){
   await p.evaluate(view=>{if(view==='vault'){navigate('achievements');$('achStatus').value='all';renderAchievements()}else{openGame('audit-game-0');document.querySelector('[data-tab=achievements]').click()}},view);
   const row=p.locator('.page:not(.hidden) .achievement-row').first(),button=row.locator('[data-ach]');const id=await button.getAttribute('data-ach');
   const box=await row.boundingBox(),length=await p.evaluate(()=>history.length);
   await row.click({position:{x:box.width/2,y:box.height-8}});
   assert.equal(await p.locator('.inline-achievement').count(),1,view+' frame click');assert.equal(await p.evaluate(()=>inlineSelection.id),id);assert.equal(await p.evaluate(()=>history.length),length);
   await p.locator('[data-inline-close]').click();
   const wasPinned=await p.evaluate(id=>DATA.state.pins.includes(id),id);await row.locator('[data-pin]').click();await p.waitForFunction(({id,before})=>DATA.state.pins.includes(id)!==before,{id,before:wasPinned});assert.equal(await p.locator('.inline-achievement').count(),0,'pin does not open details');
   await p.locator('.page:not(.hidden) .achievement-row [data-ach]').first().focus();await p.keyboard.press('Enter');assert.equal(await p.locator('.inline-achievement').count(),1,'keyboard activation');await p.locator('[data-inline-close]').click();
  }
  console.log('Full achievement frame: Vault/Universe empty-space click, independent pin, Enter activation, inline and history preservation passed');
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
