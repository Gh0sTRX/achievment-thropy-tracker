'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const html = read('atlas/web/index.html');
const foundation = read('atlas/web/ui/foundation.js');
const server = read('atlas/server.py');
const style = read('atlas/web/ui/foundation.css');
const nav = html.match(/<nav class="nav" aria-label="Ana gezinme">([\s\S]*?)<\/nav>/);
assert.ok(nav, 'native primary navigation');
const primary = nav[1].split('<details')[0];
assert.deepEqual([...primary.matchAll(/data-page="([^"]+)"/g)].map(m => m[1]), [
  'home','games','quests','hall','profile'
], 'five primary screens');
const secondary = nav[1].split('<details')[1];
for (const name of ['achievements','timeline','artwork','account','updates']) {
  assert.match(secondary, new RegExp('data-page="'+name+'"'), 'secondary route: '+name);
  assert.match(html, new RegExp('id="'+name+'"'), 'page remains reachable: '+name);
}
assert.match(html, /id="atlasMoreNav"/);
assert.equal((html.match(/id="atlasWelcome"/g) || []).length, 1);
for (const kind of ['xbox','psn','csv']) {
  assert.match(html, new RegExp('data-atlas-onboard="'+kind+'"'));
}
assert.match(html, /id="atlasCsvImport"/);
assert.match(html, /id="atlasSourceSummary"/);
assert.match(html, /id="atlasUpdateBlockers"/);
assert.match(html, /id="atlasStopForUpdate" data-stop="all"/);
assert.match(html, /\/ui\/foundation\.js/);
assert.match(html, /\/ui\/foundation\.css/);
assert.doesNotMatch(html, /src="\/ui\/ultimate\.js"/);
assert.match(foundation, /drawWelcome/);
assert.match(foundation, /atlas-empty-library/);
assert.match(style, /body\.atlas-empty-library #home/);
assert.match(foundation, /drawUpdateBlockers/);
assert.match(foundation, /UPDATE_BLOCKERS/);
assert.match(foundation, /textContent/);
assert.match(foundation, /renderUpdates = function foundationRenderUpdates/);
assert.match(server, /def update_blockers\(self\)/);
assert.match(style, /atlas-welcome-options/);
for (const id of ['atlasArchivePanel', 'atlasArchiveExport', 'atlasArchiveFile', 'atlasArchiveRestore', 'atlasArchiveStatus']) {
  assert.match(html, new RegExp('id="' + id + '"'), 'local archive control: ' + id);
}
assert.match(foundation, /api\/archive\/export/);
assert.match(foundation, /api\/archive\/restore/);
assert.match(foundation, /confirm\(/, 'explicit destructive restore confirmation');
assert.match(server, /'\/api\/archive\/restore'/);
assert.match(server, /X-Atlas-Token/, 'all archive writes are authenticated');
console.log('Foundation: navigation, onboarding, blockers and guarded archive controls passed');
