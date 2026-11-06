/* Local HTTP/UI archive lifecycle with external browser requests blocked. */
const {chromium}=require('playwright'),fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.ATLAS_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 const p=await browser.newPage({viewport:{width:1440,height:900}});let original;
 try{
  await p.route('https://**',r=>r.abort());
  await p.goto(JSON.parse(fs.readFileSync('work/audit/fixture-urls.json'))['0']);await p.waitForFunction(()=>window.uiLoaded&&window.AtlasGameRoute);
  original=await p.evaluate(async()=>await (await fetch('/api/archive/export',{method:'POST',headers:{'Content-Type':'application/json','X-Atlas-Token':TOKEN},body:'{}'})).text());
  const earned='GameName,AchievementName,AchievementPageURL,Gamerscore,UnlockDate\nOffline Game,First,https://www.trueachievements.com/a456/first-achievement,20,2026-01-01\n';
  const locked='GameName,AchievementName,AchievementPageURL,Gamerscore\nOffline Game,Second,https://www.trueachievements.com/a457/second-achievement,30\n';
  await p.evaluate(async({earned,locked})=>{await api('/api/import',{earned,locked,gamertag:'SyntheticXbox'});await reload();switchPlatform('xbox');await preferenceQueue;navigate('games')},{earned,locked});
  const gid=await p.evaluate(()=>DATA.library.games[0].id);
  await p.evaluate(async({gid,image})=>{await api('/api/art/upload',{game_id:gid,kind:'cover',image});await reload()},{gid,image:fs.readFileSync('assets/atlas-mark.png').toString('base64')});
  await p.locator('#gameGrid [data-gid]').first().click();await p.waitForURL('**/#/game/**');await p.waitForFunction(()=>document.querySelector('#detailHero').dataset.artState==='cover');
  await p.locator('[data-tab="achievements"]').click();assert.match(await p.locator('#universeContent').innerText(),/2026/);assert.match(await p.locator('#universeContent').innerText(),/TrueAchievements CSV/);
  await p.evaluate(async()=>{await api('/api/pin',{id:'ta:457',pinned:true});await api('/api/game/notes',{game_id:selectedGame,notes:'Offline note retained'});await reload()});
  await p.evaluate(()=>{navigate('account');document.getElementById('atlasArchivePanel').open=true});
  const downloading=p.waitForEvent('download');await p.locator('#atlasArchiveExport').click();const download=await downloading;
  const raw=fs.readFileSync(await download.path(),'utf8'),document=JSON.parse(raw);assert.match(raw,/"font_scale"\s*:\s*1\.0/);
  const artUrl=await p.evaluate(gid=>localArt('cover',gid),gid);
  const hash=async()=>crypto.createHash('sha256').update(await (await p.request.get(new URL(artUrl,p.url()).href)).body()).digest('hex');const before=await hash();
  await p.reload();await p.waitForFunction(()=>window.uiLoaded&&DATA.state.pins.includes('ta:457'));
  assert.equal(await p.evaluate(()=>DATA.library.games[0].notes),'Offline note retained');
  await p.evaluate(async()=>{await api('/api/game/notes',{game_id:DATA.library.games[0].id,notes:'changed'});await api('/api/pin',{id:'ta:457',pinned:false});await reload();navigate('account');document.getElementById('atlasArchivePanel').open=true});
  assert.equal(await p.evaluate(()=>DATA.library.games[0].notes),'changed');
  await p.locator('#atlasArchiveFile').setInputFiles({name:'synthetic-backup.json',mimeType:'application/json',buffer:Buffer.from(raw)});
  p.once('dialog',d=>d.accept());const restoring=p.waitForResponse(r=>r.url().endsWith('/api/archive/restore'));
  await p.locator('#atlasArchiveRestore').click();assert.equal((await restoring).status(),200);
  await p.waitForFunction(()=>page==='home'&&DATA.state.pins.includes('ta:457'));
  await p.evaluate(async({earned,locked})=>{await api('/api/import',{earned,locked,gamertag:'SyntheticXbox'});await reload()},{earned,locked});
  assert.equal(await p.evaluate(()=>DATA.library.games[0].notes),'Offline note retained');assert.deepEqual(await p.evaluate(()=>DATA.state.pins),['ta:457']);
  assert.equal(await p.evaluate(()=>DATA.library.achievements.find(a=>a.id==='ta:456').unlock_time),'2026-01-01');assert.equal(await p.evaluate(()=>DATA.library.achievements.length),2);assert.equal(await hash(),before);
  assert.equal(document.data.state.provider_inputs.xbox,'SyntheticXbox');
  console.log('Offline browser: CSV → cached cover/date/source → pin/note → page reload → verified archive restore → repeat import; local media hash unchanged (synthetic, external HTTPS blocked)');
 }finally{
  if(original&&!p.isClosed())await p.evaluate(async raw=>{const r=await fetch('/api/archive/restore',{method:'POST',headers:{'Content-Type':'application/json','X-Atlas-Token':TOKEN,'X-Atlas-Archive-Confirm':'restore'},body:raw});if(!r.ok)throw Error('Synthetic fixture cleanup failed')},original);
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exit(1)});
