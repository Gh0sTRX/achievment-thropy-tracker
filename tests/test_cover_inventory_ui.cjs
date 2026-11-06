const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const p=await browser.newPage({viewport:{width:1100,height:720}});
  await p.route('https://**',r=>r.abort());
  const calls=[];
  await p.route('**/api/art/cover_inventory',async r=>{
   const input=r.request().postDataJSON();calls.push(input);
   const offset=input.offset||0;
   const rows=Array.from({length:offset?6:20},(_,i)=>({
    game_id:'audit-game-'+(offset+i),name:'Audit Game '+(offset+i),
    platform:['xbox','psn','pc'][(offset+i)%3],
    edition:'360',title_id:'',state:'missing_source',
    reason:'Bu kategori için kullanılabilir kaynak yok.',
    action:'Görsel seç.',provider:'',source_available:false,code:null
   }));
   await r.fulfill({json:{total_games:27,covered:1,missing:26,with_source:3,needs_matching:23,
    offset,limit:20,has_more:!offset,items:rows}});
  });
  let coversRequest=null;
  await p.route('**/api/media/download',async r=>{
   coversRequest=r.request().postDataJSON();
   await r.fulfill({json:{message:'Kapak kaynakları için işlem başlatıldı.'}});
  });
  const fixture=JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['80'];
  await p.goto(fixture);
  await p.waitForFunction(()=>window.uiLoaded&&window.AtlasGameRoute);
  // Start on PSN to verify that the all-library queue can open an Xbox game.
  await p.evaluate(()=>{ACTIVE_PLATFORM='psn';ACTIVE_DEVICE='all';navigate('artwork')});
  await p.locator('#scanCoverLibrary').click();
  await p.waitForFunction(()=>document.querySelectorAll('#coverInventoryList [data-cover-select]').length===20);
  assert.match(await p.locator('#coverInventoryStatus').innerText(),/27 oyun\/sürüm/);
  assert.match(await p.locator('#coverInventoryPage').innerText(),/1 \/ 2/);
  await p.locator('#coverInventoryNext').click();
  await p.waitForFunction(()=>document.querySelectorAll('#coverInventoryList [data-cover-select]').length===6);
  assert.match(await p.locator('#coverInventoryPage').innerText(),/2 \/ 2/);
  await p.locator('#coverInventoryPrev').click();
  await p.locator('[data-cover-select="audit-game-0"]').click();
  assert.equal(await p.locator('#artGame').inputValue(),'audit-game-0');
  assert.equal(await p.evaluate(()=>ACTIVE_PLATFORM),'all');
  assert.equal(await p.locator('#localArtKind').inputValue(),'cover');
  assert.equal(await p.locator('#artwork details.panel').first().evaluate(el=>el.open),true);
  await p.locator('#recoverCoverLibrary').click();
  await p.waitForFunction(()=>document.querySelector('#coverInventoryStatus')?.textContent.includes('27 oyun'));
  assert.equal(coversRequest.covers_only,true);
  assert.deepEqual(calls.map(x=>x.offset),[0,20,0]);
  console.log('Game Universe: full cross-platform cover inventory, 20+6 paging, per-game edition review and cover-only download request passed');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
