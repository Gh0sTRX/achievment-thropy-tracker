const assert=require('node:assert/strict');
class Element{
 constructor(){this.childNodes=[];this.dataset={};this.style={};this.classList={add:()=>{}}}
 replaceChildren(...items){this.childNodes=items}append(...items){this.childNodes.push(...items)}after(x){this.sibling=x}cloneNode(){return new Element()}removeAttribute(){}remove(){this.removed=true}
}
let requests=[];
global.Image=class{constructor(){this.alt=''}setAttribute(){}set src(x){this.value=x;if(x)requests.push(this)}get src(){return this.value}};
global.requestAnimationFrame=f=>f();const Transition=require('../atlas/web/art_transition.js');
const el=new Element(),t=new Transition(el,u=>u.startsWith('/art/'));
t.show('/art/a',true);const a=requests.at(-1);a.onload();assert.equal(t.current,'/art/a');
t.show('/art/b',true);requests.at(-1).onerror();assert.equal(t.current,'/art/a');assert.equal(el.childNodes[0],a);
const count=requests.length;t.show('/art/b',true);assert.equal(requests.length,count,'Failed URLs have retry cooldown');
t.show('/art/c',true);const stale=requests.at(-1),staleLoad=stale.onload;t.show('/art/d',true);staleLoad();assert.equal(t.current,'/art/a','Stale callback cannot commit');requests.at(-1).onload();assert.equal(t.current,'/art/d');
t.show('/art/a',true);assert.equal(requests.length,count+2,'Cached image reused without request');assert.equal(t.current,'/art/a');assert.ok(t.cache.size<=2);
t.show('/art/e',false);requests.at(-1).onload();assert.ok(t.fade);t.clearFade();
t.show('https://evil.example/img');assert.equal(t.current,'');assert.equal(el.childNodes.length,0);
t.show('/art/f');t.cancel();assert.equal(t.pending,null);console.log('Artwork: stale loads, failure fallback, bounded cache, no duplicate fetch, reduced-motion and URL guard passed');
