/* ============================================================
   R i D A — Cinematic Interactions Layer (ADDITIVE)
   NOTE: reveal-on-scroll + hero entrance are handled by main.js
   (GSAP). This file only adds effects that main.js does NOT do:
   scroll progress · hero mouse-parallax · magnetic buttons ·
   3D card tilt. Nothing here touches .reveal-* opacity.
   ============================================================ */
(function () {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── 1. Scroll progress bar ──
     rAF-batched: the raw 'scroll' event can fire many times per frame on
     mobile, and writing to style.width on every one of those fights the
     browser's own scroll compositing — a common source of janky-feeling
     scroll on phones. Coalescing to one write per animation frame keeps
     this off the scroll-critical path. */
  const progress = document.getElementById('scrollProgress');
  let progressTicking = false;
  function updateProgress() {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    const scrolled = max > 0 ? h.scrollTop / max : 0;
    if (progress) progress.style.width = (scrolled * 100).toFixed(2) + '%';
    progressTicking = false;
  }
  function requestProgressUpdate() {
    if (progressTicking) return;
    progressTicking = true;
    requestAnimationFrame(updateProgress);
  }
  window.addEventListener('scroll', requestProgressUpdate, { passive: true });
  window.addEventListener('resize', requestProgressUpdate);
  updateProgress();

  /* ── 1.5 World sourcing map: dot-matrix continents ──
     Runs regardless of reduced-motion (it renders content, not motion).
     Rough continent outlines (lon,lat) → equirectangular projection;
     a 3° dot grid is plotted for cells that fall on land. */
  const worldDots = document.getElementById('worldDots');
  if (worldDots) {
    const CONTINENTS = [
      // North America
      [[-168,66],[-152,70],[-130,70],[-110,72],[-90,73],[-75,72],[-68,60],[-55,52],[-60,46],[-70,44],[-75,38],[-80,32],[-81,26],[-90,29],[-97,26],[-104,19],[-97,15],[-88,13],[-83,9],[-79,9],[-85,12],[-95,17],[-106,24],[-114,30],[-120,34],[-124,41],[-124,48],[-132,55],[-146,60],[-160,60]],
      // Greenland
      [[-52,60],[-42,62],[-25,70],[-20,76],[-30,82],[-55,82],[-68,78],[-60,72]],
      // South America
      [[-79,9],[-60,9],[-52,5],[-44,-1],[-35,-6],[-37,-13],[-40,-22],[-48,-26],[-53,-33],[-58,-36],[-63,-42],[-68,-55],[-72,-50],[-75,-40],[-70,-20],[-77,-8],[-81,0]],
      // Africa
      [[-6,35],[3,37],[11,37],[20,32],[32,31],[34,27],[37,21],[43,11],[48,11],[51,10],[45,1],[40,-5],[37,-12],[33,-20],[29,-29],[25,-34],[19,-34],[15,-28],[12,-18],[9,-7],[6,0],[-2,5],[-8,5],[-13,9],[-17,15],[-17,21],[-13,28]],
      // Eurasia (incl. Arabia & India; Persian Gulf indent kept for the UAE hub)
      [[-10,36],[-9,43],[-2,48],[-5,50],[-1,54],[5,58],[10,55],[12,57],[10,60],[18,56],[22,60],[28,60],[31,62],[40,66],[50,68],[68,70],[85,74],[105,77],[130,72],[150,70],[170,67],[179,65],[170,60],[162,56],[158,52],[150,45],[142,42],[135,42],[130,40],[126,36],[122,30],[115,22],[108,16],[105,10],[103,3],[100,3],[98,8],[95,14],[91,21],[88,22],[85,20],[80,14],[77,8],[73,15],[70,22],[66,25],[61,25],[56,27],[52,29],[48,30],[48,28],[51,24.5],[54,24.5],[56,26],[59,23],[57,19],[52,15],[48,13],[43,12],[39,20],[35,28],[32,30],[34,32],[36,36],[30,36],[27,37],[23,36],[19,40],[16,39],[15,41],[12,44],[8,44],[5,43],[0,40],[-2,37]],
      // Australia
      [[114,-22],[122,-17],[131,-12],[137,-12],[142,-11],[145,-15],[147,-19],[153,-26],[152,-33],[146,-39],[140,-38],[134,-35],[129,-32],[124,-33],[115,-34]]
    ];
    const inPoly = (x, y, poly) => {
      let c = false;
      for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
        const xi = poly[i][0], yi = poly[i][1], xj = poly[j][0], yj = poly[j][1];
        if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c;
      }
      return c;
    };
    const NS = 'http://www.w3.org/2000/svg';
    const frag = document.createDocumentFragment();
    for (let lat = -54; lat <= 78; lat += 2) {
      for (let lon = -170; lon <= 180; lon += 2) {
        if (CONTINENTS.some((p) => inPoly(lon, lat, p))) {
          const dot = document.createElementNS(NS, 'circle');
          dot.setAttribute('cx', ((lon + 180) / 360 * 1000).toFixed(1));
          dot.setAttribute('cy', ((90 - lat) / 180 * 500).toFixed(1));
          dot.setAttribute('r', '1.55');
          frag.appendChild(dot);
        }
      }
    }
    worldDots.appendChild(frag);

    /* country card <-> map marker hover sync */
    document.querySelectorAll('.country-card').forEach(function (card) {
      var marker = document.querySelector('.world-marker[data-country="' + card.getAttribute('data-country') + '"]');
      if (!marker) return;
      card.addEventListener('mouseenter', function () { marker.classList.add('is-active'); });
      card.addEventListener('mouseleave', function () { marker.classList.remove('is-active'); });
      card.addEventListener('focus', function () { marker.classList.add('is-active'); });
      card.addEventListener('blur', function () { marker.classList.remove('is-active'); });
    });
  }

  if (reduceMotion) return; // skip motion-heavy effects

  /* ── 2. Hero mouse parallax — DISABLED (flickering on text hover) ── */

  /* ── 3. 3D card tilt on hover ── */
  document.querySelectorAll('.vision-card, .portfolio-card, .segment-card, .pillar-card, .region-card, .stat-card-light, .contact-card').forEach(function (card) {
    card.addEventListener('mousemove', function (e) {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      card.style.transform = 'perspective(800px) rotateY(' + (x * 8).toFixed(2) + 'deg) rotateX(' + (y * -6).toFixed(2) + 'deg) translateY(-8px) scale(1.02)';
    });
    card.addEventListener('mouseleave', function () {
      card.style.transform = '';
    });
  });

  /* ── 4. Magnetic CTA buttons ── */
  document.querySelectorAll('.hero-ctas .btn, .btn-primary, .btn-accent').forEach(function (btn) {
    btn.addEventListener('mousemove', function (e) {
      const rect = btn.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      btn.style.transform = 'translate(' + (x * 8).toFixed(2) + 'px, ' + (y * 6).toFixed(2) + 'px) translateY(-4px) scale(1.04)';
    });
    btn.addEventListener('mouseleave', function () {
      btn.style.transform = '';
    });
  });
})();
