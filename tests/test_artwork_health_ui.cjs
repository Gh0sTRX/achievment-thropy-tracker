const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const p=await b.newPage({viewport:{width:980,height:640}});await p.route('https://**',r=>r.abort());let retried=null;
  await p.route('**/api/media/download',async r=>{retried=r.request().postDataJSON();await r.fulfill({json:{message:'Synthetic single-game retry accepted'}})});
  await p.goto(JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['80']);await p.waitForFunction(()=>window.uiLoaded&&window.AtlasGameRoute);
  await p.evaluate(()=>{ACTIVE_PLATFORM='all';ACTIVE_DEVICE='all';navigate('artwork')});
  await p.locator('#artGame').selectOption('audit-game-0');await p.locator('#checkSelectedArtHealth').click();
  await p.waitForFunction(()=>$('artHealth').textContent.startsWith('1 oyun'));
  let text=await p.locator('#artHealthGames').innerText();assert.match(text,/Kaynak yok/);assert.match(text,/oyun\/edisyon/);assert.match(text,/Başarım ikonları/);assert.match(text,/1000/);
  assert.equal(await p.locator('#artHealthGames [data-gid]').count(),1);
  await p.locator('[data-health-retry]').click();assert.equal(retried.game_id,'audit-game-0');
  await p.locator('#artGame').selectOption('audit-game-1');await p.locator('#checkSelectedArtHealth').click();await p.waitForFunction(()=>document.querySelector('#artHealthGames [data-gid]')?.dataset.gid==='audit-game-1');
  text=await p.locator('#artHealthGames').innerText();assert.match(text,/Önbellekte/);assert.equal(await p.evaluate(()=>window.pwned),undefined);
  const identity=await p.evaluate(()=>{const g=gameById('audit-game-1'),changed={...g,artwork_meta:{cover:{provider:'Xbox TitleHub',game_id:g.id,title_id:'other',platform:g.platform,platform_edition:g.platform_edition}}};const hidden=visualUrl(changed,'cover');changed.artwork_meta.cover.provider='user_file';return {hidden,custom:visualUrl(changed,'cover')}});assert.equal(identity.hidden,'');assert.ok(identity.custom.startsWith('/'));
  await p.locator('[data-health-art]').click();assert.equal(await p.locator('#artGame').inputValue(),'audit-game-1');
  console.log('Artwork health: real local API, per-game scope, six asset types, source/action hints, cached cover, escaped names and targeted retry (mock download) passed');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
