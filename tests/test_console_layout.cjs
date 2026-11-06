const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  for(const [width,height] of [[1920,1080],[1440,900],[980,640],[390,844]]){
   for(const hasCover of [false,true]){
   const p=await b.newPage({viewport:{width,height}});
   await p.route('https://**',r=>r.abort());
   await p.goto(JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['80']);
   await p.waitForFunction(()=>window.uiLoaded&&window.AtlasGameRoute);
   // Other suites deliberately persist platform, edition and selected-game state.
   // Select both real fixture cases explicitly instead of assuming the default.
   await p.evaluate(hasCover=>{ACTIVE_PLATFORM='all';ACTIVE_DEVICE='all';$('catalogueFilter').value='game';selectedGame=hasCover?'audit-game-1':'audit-game-0';navigate('games')},hasCover);
   await p.locator('#atlasConsoleButton').click();
   await p.waitForFunction(()=>document.querySelector('#atlasConsole').open);
   const result=await p.evaluate(()=>{
    const d=document.querySelector('#atlasConsole'),foot=d.querySelector('.atlas-console-foot'),hero=d.querySelector('.atlas-console-hero'),rail=d.querySelector('.atlas-console-rail');
    // The decorative blurred background intentionally extends outside the dialog.
    const horizontal=[...d.children].filter(x=>!x.classList.contains('atlas-console-artwork')).some(x=>{const r=x.getBoundingClientRect();return r.left < -2 || r.right > innerWidth+2});
    return {horizontal,overlap:hero.getBoundingClientRect().bottom>rail.getBoundingClientRect().top+2,footer:foot.getBoundingClientRect().top>=rail.getBoundingClientRect().bottom-2,focus:d.contains(document.activeElement),coverHidden:document.querySelector('#atlasConsoleCover').hidden};
   });
   assert.equal(result.horizontal,false,`${width}: horizontal overflow`);
   assert.equal(result.overlap,false,`${width}: hero overlaps cards`);
   assert.equal(result.footer,true,`${width}: footer overlaps rail`);
   assert.equal(result.focus,true,'Console receives focus');assert.equal(result.coverHidden,!hasCover,'Selected fixture cover state');
   if(hasCover)await p.waitForFunction(()=>{const img=document.querySelector('#atlasConsoleCover');return !img.hidden&&img.complete&&img.naturalWidth>0});
   await p.keyboard.press('Escape');await p.waitForFunction(()=>!document.querySelector('#atlasConsole').open);
   await p.close();
   }
  }
  console.log('Console layout: four viewports × explicit cover/no-cover selection, image decode, no control overlap, focus and Escape passed (synthetic)');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
