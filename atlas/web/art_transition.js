'use strict';
// Two-entry decoded image cache plus one pending load; stale requests never replace the selected game's art.
class AtlasArtTransition {
 constructor(element,accept){this.element=element;this.accept=accept;this.serial=0;this.current='';this.requested='';this.pending=null;this.fade=null;this.timer=null;this.cache=new Map();this.failed=new Map()}
 cancel(){this.serial++;if(this.pending){this.pending.onload=null;this.pending.onerror=null;this.pending.src='';this.pending=null}this.requested=''}
 show(url,noMotion=false){
  if(url&&!this.accept(url))url='';
  if(!url){this.cancel();this.clearFade();this.element.replaceChildren();this.element.style.backgroundImage='none';this.element.dataset.artState='empty';this.current='';return}
  if(url===this.current||url===this.requested)return;
  if((this.failed.get(url)||0)>Date.now())return;
  this.cancel();const serial=this.serial;this.requested=url;this.element.dataset.artState='loading';
  const apply=img=>{
   if(serial!==this.serial)return;
   this.pending=null;this.requested='';this.clearFade();
   if(this.element.childNodes.length&&!noMotion){
    const old=this.element.cloneNode(false);old.removeAttribute('id');old.classList.add('au-ambient-fading');
    old.append(...this.element.childNodes);this.element.after(old);this.fade=old;
    requestAnimationFrame(()=>old.classList.add('au-fade-out'));this.timer=setTimeout(()=>this.clearFade(),570);
   }
   this.element.replaceChildren(img);this.element.style.backgroundImage='none';this.current=url;this.element.dataset.artState='ready';
   this.cache.delete(url);this.cache.set(url,img);
   while(this.cache.size>2)this.cache.delete(this.cache.keys().next().value);
  };
  if(this.cache.has(url)){apply(this.cache.get(url));return}
  const img=new Image();img.alt='';img.setAttribute('aria-hidden','true');img.className='au-art-layer';this.pending=img;
  img.onload=()=>{img.onload=null;img.onerror=null;apply(img)};
  img.onerror=()=>{if(serial!==this.serial)return;this.pending=null;this.requested='';this.failed.set(url,Date.now()+60000);while(this.failed.size>16)this.failed.delete(this.failed.keys().next().value);this.element.dataset.artState='error'};
  img.src=url;
 }
 clearFade(){clearTimeout(this.timer);this.fade?.remove();this.fade=null;this.timer=null}
}
if(typeof module!=='undefined')module.exports=AtlasArtTransition;
