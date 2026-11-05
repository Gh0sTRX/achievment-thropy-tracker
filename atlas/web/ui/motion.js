/* Native v0.15 motion: one app shell, no overlay and no synthetic game assets. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let activeMotion = [];
  const getSkin = () => document.body.dataset.skin || 'cinematic';
  const reduced = () => Boolean(
    document.body.classList.contains('reduced-motion') ||
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  );
  function cancel() {
    for (const animation of activeMotion) {
      try { animation.cancel(); } catch (_) {}
    }
    activeMotion = [];
  }
  function enterFrames(skin) {
    if (skin === 'blades') return [{opacity:0, transform:'translateX(-14px)'}, {opacity:1, transform:'translateX(0)'}];
    if (skin === 'nxe') return [{opacity:0, transform:'translateY(8px) scale(.985)'}, {opacity:1, transform:'translateY(0) scale(1)'}];
    if (skin === 'xmb') return [{opacity:0, transform:'translateY(16px)'}, {opacity:1, transform:'translateY(0)'}];
    return [{opacity:0, transform:'translateY(12px)'}, {opacity:1, transform:'translateY(0)'}];
  }
  function play(element, frames, duration, delay=0) {
    if (!element || typeof element.animate !== 'function') return;
    const animation = element.animate(frames, {
      duration, delay, easing:'cubic-bezier(.2,.72,.22,1)', fill:'both'
    });
    activeMotion.push(animation);
    // 'fill' must not retain a transform after this transition ends.
    animation.addEventListener?.('finish', () => animation.cancel(), {once:true});
    return animation;
  }
  function animatePage(target) {
    cancel();
    if (reduced()) return;
    const section = $(target);
    if (!section || section.classList.contains('hidden')) return;
    play(section, enterFrames(getSkin()), 270);
    const nodes = section.querySelectorAll(
      ':scope > .section-head, :scope > .stat-grid, :scope > .panel, ' +
      ':scope > .featured, :scope > .quest-board, :scope > .atlas-welcome'
    );
    [...nodes].slice(0, 5).forEach((node, index) => {
      play(node, [{opacity:0,transform:'translateY(7px)'},{opacity:1,transform:'translateY(0)'}],
        210, 24 + index * 28);
    });
  }
  function animateSelection() {
    cancel();
    if (reduced()) return;
    const section = document.querySelector('.page:not(.hidden)');
    if (!section) return;
    const nodes = section.querySelectorAll(
      '.game-card, .suggest, .achievement-row, .atlas-timeline-bin, .inline-achievement'
    );
    [...nodes].slice(0, 10).forEach((node, index) => {
      play(node, [{opacity:.2,transform:'translateY(6px)'},{opacity:1,transform:'translateY(0)'}],
        200, Math.min(index * 20, 120));
    });
  }
  function init() {
    window.addEventListener('atlas:navigate',event=>{const {destination,previous}=event.detail;if(destination!==previous)animatePage(destination)});
    document.body.addEventListener('click', e => {
      const t = e.target.closest('[data-platform], [data-layout], [data-atlas-range], [data-gid]');
      if (!t || reduced()) return;
      // Prior handlers finish native rendering before we examine the new DOM.
      queueMicrotask(() => {
        if (!t.matches('[data-gid]')) animateSelection();
      });
    });
    document.body.addEventListener('change', e => {
      if (e.target.matches('#achStatus, #achGame, #achSort, #gameSort')) {
        queueMicrotask(animateSelection);
      }
    });
    // Theme updates do not change platform data; CSS handles the visual identity.
    window.AtlasMotion = {enabled: () => !reduced()};
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, {once:true});
  } else init();
})();
