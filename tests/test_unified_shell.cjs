'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(root,file),'utf8');
const html = read('atlas/web/index.html');
const native = read('atlas/web/ui/shell.js');
const style = read('atlas/web/ui/shell.css');
assert.equal((html.match(/id="atlasConsole"/g)||[]).length,1, 'one console dialog');
assert.equal((html.match(/id="app"/g)||[]).length,1, 'one native app');
assert.equal((html.match(/class="rail"/g)||[]).length,1, 'one navigation rail');
assert.match(html,/\/ui\/shell\.js/);
assert.match(html,/\/ui\/shell\.css/);
assert.doesNotMatch(html,/src="\/ui\/ultimate\.js"/, 'no second application shell');
assert.doesNotMatch(html,/href="\/ui\/ultimate\.css"/, 'no second theme CSS layer');
assert.match(html,/id="atlasThemeSkin"/);
assert.match(html,/id="timeline"/);
for (const theme of ['cinematic','blades','nxe','xmb']) {
  assert.match(native,new RegExp("'"+theme+"'"));
  assert.ok(style.includes('body[data-skin='+theme+']'), 'native style '+theme);
}
assert.match(native,/visualUrl\(g, 'hero'\)/);
assert.match(native,/showModal\(\)/);
assert.match(native,/openGame\(g\.id\)/);
assert.match(native,/theme_skin:skin/);
assert.match(native,/AtlasModel\.date/);
console.log('Unified native themes: one shell, four skins, real art, console and timeline checks passed');
