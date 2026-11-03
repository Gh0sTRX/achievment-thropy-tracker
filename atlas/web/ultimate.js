'use strict';
let preferenceQueue=Promise.resolve();
function savePreferences(values){
 preferenceQueue=preferenceQueue.then(async()=>{const prior={...DATA.state.ui};DATA.state.ui={...prior,...values};applyPreferences();try{await api('/api/preferences',values)}catch(e){DATA.state.ui=prior;applyPreferences();render();toast(e.message,true)}});return preferenceQueue;
}
function applyPreferences(){const ui=DATA.state.ui||{};document.body.classList.toggle('reduced-motion',!!ui.reduced_motion);document.body.classList.toggle('dense-mode',!!ui.dense_mode);document.body.classList.toggle('high-contrast',!!ui.high_contrast);document.documentElement.style.setProperty('--font-scale',ui.font_scale||1);document.documentElement.style.setProperty('--hero-overlay',ui.hero_contrast??.68)}
start();
