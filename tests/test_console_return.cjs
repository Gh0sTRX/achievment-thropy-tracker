const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const p=await b.newPage();await p.route('https://**',r=>r.abort());
  await p.goto(JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['80']);await p.waitForFunction(()=>window.uiLoaded&&window.AtlasConsole);
  await p.evaluate(()=>{ACTIVE_PLATFORM='all';ACTIVE_DEVICE='all';$('catalogueFilter').value='game';navigate('games');selectedGame='audit-game-1';AtlasConsole.open();window.testPad={connected:true,axes:[0,0],buttons:Array.from({length:16},()=>({pressed:false}))};Object.defineProperty(navigator,'getGamepads',{value:()=>{window.padReads=(window.padReads||0)+1;return [testPad]},configurable:true});window.dispatchEvent(new Event('gamepadconnected'))});
  async function press(n){let reads=await p.evaluate(n=>{testPad.buttons[n].pressed=true;return window.padReads||0},n);await p.waitForFunction(n=>padReads>=n+2,reads);reads=await p.evaluate(n=>{testPad.buttons[n].pressed=false;return padReads},n);await p.waitForFunction(n=>padReads>=n+2,reads)}
  const before=await p.locator('#atlasConsoleTitle').innerText();await press(15);assert.notEqual(await p.locator('#atlasConsoleTitle').innerText(),before);
  await p.evaluate(()=>testPad.axes[0]=-1);await p.waitForFunction(before=>document.querySelector('#atlasConsoleTitle').textContent===before,before);const neutral=await p.evaluate(()=>{testPad.axes[0]=0;return padReads});await p.waitForFunction(n=>padReads>=n+2,neutral);
  const title=await p.locator('#atlasConsoleTitle').innerText();await press(0);await p.waitForFunction(()=>page==='universe');
  await press(5);await press(4);assert.equal(await p.locator('[data-tab=overview]').getAttribute('aria-selected'),'true');await press(5);assert.equal(await p.locator('[data-tab=achievements]').getAttribute('aria-selected'),'true');
  const target=p.locator('#universeContent .achievement-row [data-ach]').first();const aid=await target.getAttribute('data-ach');await target.focus();const pinned=await p.evaluate(id=>DATA.state.pins.includes(id),aid);await press(2);await p.waitForFunction(({id,before})=>DATA.state.pins.includes(id)!==before,{id:aid,before:pinned});
  await press(3);await p.waitForFunction(()=>$('atlasSearch').open);await press(1);await p.waitForFunction(()=>!$('atlasSearch').open);
  await press(1);await p.waitForFunction(()=>AtlasConsole.isOpen(),null,{timeout:3000});
  assert.equal(await p.locator('#atlasConsoleTitle').innerText(),title);
  await p.waitForFunction(()=>document.activeElement?.matches('#atlasConsoleRail .selected'));
  await p.keyboard.press('Escape');await p.waitForFunction(()=>!AtlasConsole.isOpen());
  console.log('Console return: simulated D-pad/analog/A/B/X/Y/RB, pin, selected game/focus restore and Escape passed; no physical controller acceptance');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
