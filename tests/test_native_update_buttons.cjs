// Drives the real installed app's WebView2, not a separate Chromium browser.
const { chromium } = require(process.env.ATLAS_PLAYWRIGHT_MODULE);
const fs = require('node:fs');
(async () => {
  const port = process.argv[2], report = process.argv[3];
  let browser, lastError;
  for (let attempt=0; attempt<60; attempt++) {
    try { browser=await chromium.connectOverCDP(`http://127.0.0.1:${port}`); break; }
    catch (error) { lastError=error; await new Promise(r=>setTimeout(r,500)); }
  }
  if (!browser) throw Error('Native WebView2 debugging endpoint unavailable: '+lastError?.message);
  let page;
  for (let attempt=0; attempt<60; attempt++) {
    page=browser.contexts().flatMap(c=>c.pages()).find(p=>/^http:\/\/127\.0\.0\.1:/.test(p.url()));
    if (page) break;
    await new Promise(r=>setTimeout(r,500));
  }
  if (!page) throw Error('Native application document unavailable');
  await page.waitForFunction(()=>typeof navigate==='function' && document.querySelector('#checkUpdate'));
  await page.evaluate(()=>navigate('updates'));
  await page.locator('#checkUpdate').click();
  await page.locator('#downloadUpdate').waitFor({state:'visible',timeout:90000});
  await page.locator('#downloadUpdate').click();
  await page.locator('#installUpdate').waitFor({state:'visible',timeout:180000});
  const closed = new Promise(resolve=>browser.once('disconnected',resolve));
  await page.locator('#installUpdate').click();
  await Promise.race([closed,new Promise((_,reject)=>setTimeout(()=>reject(Error('Update did not close old native app')),45000))]);
  fs.writeFileSync(report,JSON.stringify({ok:true,checks:['real WebView2 check button','real download button','verified ready state','real install button','old native app closed']},null,2));
  process.exit(0);
})().catch(error=>{console.error(error);process.exit(1);});
