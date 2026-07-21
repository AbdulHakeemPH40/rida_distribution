/**
 * R i D A — Global Sourcing Map  (Self-Contained Edition)
 * ──────────────────────────────────────────────────────
 * Renders a flat world map with:
 *   • Embedded simplified continent SVG paths (NO external dependency needed)
 *   • Optional d3 enhancement if CDN loads successfully
 *   • UAE hub marker (gold, pulsing)
 *   • Sourcing markets highlighted
 *   • Animated dashed gold routes (UAE ↔ each country)
 *   • Traveling particles along each route
 *   • Hover sync with .country-card list
 *
 * This version ALWAYS renders — even offline — using built-in map data.
 */
(function () {
  'use strict';

  var container = document.getElementById('globe3d');
  if (!container) return;

  /* ── Configuration ─────────────────────────────────────── */
  var HUB = { name: 'UAE', lat: 24.0, lon: 54.0 };
  var SPOKES = [
    { name: 'India',       lat: 22.0,  lon: 78.5  },
    { name: 'Sri Lanka',   lat: 7.9,   lon: 80.8  },
    { name: 'Thailand',    lat: 15.5,  lon: 101.0 },
    { name: 'Vietnam',     lat: 16.0,  lon: 107.5 },
    { name: 'Philippines', lat: 13.0,  lon: 122.0 },
    { name: 'China',       lat: 35.0,  lon: 105.0 },
    { name: 'Korea',       lat: 36.5,  lon: 127.8 },
    { name: 'Nigeria',     lat: 9.0,   lon: 8.0   },
    { name: 'Congo',       lat: -2.0,  lon: 23.0  },
    { name: 'Uganda',      lat: 1.0,   lon: 32.0  },
    { name: 'Kenya',       lat: 0.5,   lon: 38.0  },
    { name: 'Zambia',      lat: -13.0, lon: 28.0  }
  ];

  var GOLD  = '#F5C542';
  var GREEN = '#3DD489';
  var activeCountry = null;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Embedded simplified world map (equirectangular SVG paths) ──
   * These are hand-simplified continent outlines in a 1000×500 viewBox
   * using equirectangular projection (lon: -180→0, 180→1000; lat: 90→0, -90→500).
   * Compact enough to embed, detailed enough to look professional.
   */
  var MAP_W = 1000, MAP_H = 500;

  var CONTINENTS = [
    /* North America */
    'M 80 80 L 120 60 L 180 55 L 230 70 L 270 90 L 290 110 L 280 130 L 250 140 L 230 160 L 210 180 L 190 195 L 160 200 L 140 210 L 120 220 L 100 210 L 85 190 L 75 160 L 70 130 L 75 100 Z',
    /* Central America strip */
    'M 200 200 L 220 210 L 240 225 L 250 240 L 245 250 L 230 245 L 215 235 L 205 220 Z',
    /* South America */
    'M 260 240 L 290 235 L 320 245 L 340 260 L 350 290 L 345 330 L 330 370 L 310 400 L 290 420 L 275 415 L 265 390 L 260 360 L 255 320 L 258 280 L 260 250 Z',
    /* Greenland */
    'M 340 40 L 380 35 L 410 50 L 415 80 L 400 100 L 370 95 L 350 75 Z',
    /* Europe */
    'M 460 90 L 490 80 L 520 75 L 545 85 L 560 100 L 555 120 L 540 130 L 520 135 L 500 130 L 480 125 L 465 115 Z',
    /* UK */
    'M 445 95 L 455 90 L 458 105 L 450 115 L 442 110 Z',
    /* Scandinavia */
    'M 490 55 L 510 50 L 525 60 L 520 75 L 505 80 L 495 75 L 488 65 Z',
    /* Africa */
    'M 480 140 L 520 135 L 555 140 L 580 155 L 595 180 L 600 215 L 595 250 L 580 285 L 560 310 L 540 320 L 520 315 L 500 300 L 485 275 L 475 245 L 470 210 L 472 175 Z',
    /* Madagascar */
    'M 590 275 L 598 270 L 600 290 L 593 300 L 588 290 Z',
    /* Middle East / Arabian Peninsula */
    'M 560 130 L 590 125 L 610 135 L 615 155 L 605 170 L 585 175 L 565 165 L 555 150 Z',
    /* Asia (main) */
    'M 560 90 L 600 80 L 650 75 L 700 80 L 750 85 L 800 90 L 830 100 L 850 120 L 845 140 L 820 150 L 790 155 L 760 150 L 730 145 L 700 140 L 670 135 L 640 130 L 610 125 L 580 115 L 565 100 Z',
    /* India */
    'M 640 150 L 660 145 L 675 155 L 680 175 L 670 195 L 655 200 L 645 185 L 638 165 Z',
    /* Southeast Asia / Indochina */
    'M 700 155 L 725 150 L 740 160 L 745 180 L 735 195 L 720 200 L 705 190 L 698 175 Z',
    /* Indonesia / Philippines islands */
    'M 740 200 L 760 195 L 775 205 L 785 215 L 780 225 L 765 220 L 750 215 L 742 210 Z',
    'M 790 210 L 810 205 L 825 215 L 820 230 L 800 225 L 788 220 Z',
    /* Japan */
    'M 845 125 L 855 120 L 862 135 L 855 150 L 848 145 L 843 135 Z',
    /* Australia */
    'M 800 280 L 840 275 L 875 280 L 895 295 L 900 315 L 885 330 L 855 335 L 825 330 L 800 320 L 790 300 Z',
    /* New Zealand */
    'M 920 335 L 930 330 L 935 345 L 928 355 L 920 350 Z'
  ];

  /* ── DOM: create SVG ────────────────────────────────────── */
  var svgNS = 'http://www.w3.org/2000/svg';
  var svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('class', 'globe-svg');
  svg.setAttribute('viewBox', '0 0 ' + MAP_W + ' ' + MAP_H);
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  container.appendChild(svg);

  /* ── Layers ─────────────────────────────────────────────── */
  var defs = document.createElementNS(svgNS, 'defs');
  var oceanLayer = document.createElementNS(svgNS, 'g');
  var gridLayer = document.createElementNS(svgNS, 'g');
  var landLayer = document.createElementNS(svgNS, 'g');
  var highlightLayer = document.createElementNS(svgNS, 'g');
  var routeLayer = document.createElementNS(svgNS, 'g');
  var markerLayer = document.createElementNS(svgNS, 'g');
  var labelLayer = document.createElementNS(svgNS, 'g');

  [defs, oceanLayer, gridLayer, landLayer, highlightLayer,
   routeLayer, markerLayer, labelLayer].forEach(function (l) {
    svg.appendChild(l);
  });

  /* ── Filters & gradients ───────────────────────────────── */
  defs.innerHTML =
    '<filter id="goldGlow" x="-200%" y="-200%" width="500%" height="500%">' +
      '<feGaussianBlur stdDeviation="4" result="b"/>' +
      '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>' +
    '</filter>' +
    '<filter id="greenGlow" x="-200%" y="-200%" width="500%" height="500%">' +
      '<feGaussianBlur stdDeviation="3" result="b"/>' +
      '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>' +
    '</filter>' +
    '<radialGradient id="oceanGrad" cx="50%" cy="45%" r="75%">' +
      '<stop offset="0%" stop-color="#0d2e1d"/>' +
      '<stop offset="55%" stop-color="#0a2014"/>' +
      '<stop offset="100%" stop-color="#06140c"/>' +
    '</radialGradient>' +
    '<radialGradient id="hubPulse" cx="50%" cy="50%" r="50%">' +
      '<stop offset="0%" stop-color="#F5C542" stop-opacity="0.5"/>' +
      '<stop offset="100%" stop-color="#F5C542" stop-opacity="0"/>' +
    '</radialGradient>';

  /* ── Equirectangular projection (lon, lat) → (x, y) ────── */
  function project(lon, lat) {
    var x = (lon + 180) / 360 * MAP_W;
    var y = (90 - lat) / 180 * MAP_H;
    return [x, y];
  }

  /* ── Draw ocean background ──────────────────────────────── */
  function drawOcean() {
    oceanLayer.innerHTML = '';
    var rect = document.createElementNS(svgNS, 'rect');
    rect.setAttribute('x', 0);
    rect.setAttribute('y', 0);
    rect.setAttribute('width', MAP_W);
    rect.setAttribute('height', MAP_H);
    rect.setAttribute('fill', 'url(#oceanGrad)');
    oceanLayer.appendChild(rect);
  }

  /* ── Draw graticule grid ────────────────────────────────── */
  function drawGrid() {
    gridLayer.innerHTML = '';
    /* Meridians (vertical lines) every 30° */
    for (var lon = -180; lon <= 180; lon += 30) {
      var x = (lon + 180) / 360 * MAP_W;
      var line = document.createElementNS(svgNS, 'line');
      line.setAttribute('x1', x);
      line.setAttribute('y1', 0);
      line.setAttribute('x2', x);
      line.setAttribute('y2', MAP_H);
      line.setAttribute('stroke', 'rgba(61,212,137,0.05)');
      line.setAttribute('stroke-width', '0.5');
      gridLayer.appendChild(line);
    }
    /* Parallels (horizontal lines) every 30° */
    for (var lat = -90; lat <= 90; lat += 30) {
      var y = (90 - lat) / 180 * MAP_H;
      var line = document.createElementNS(svgNS, 'line');
      line.setAttribute('x1', 0);
      line.setAttribute('y1', y);
      line.setAttribute('x2', MAP_W);
      line.setAttribute('y2', y);
      line.setAttribute('stroke', 'rgba(61,212,137,0.05)');
      line.setAttribute('stroke-width', '0.5');
      gridLayer.appendChild(line);
    }
  }

  /* ── Draw land (continents) ─────────────────────────────── */
  function drawLand() {
    landLayer.innerHTML = '';
    highlightLayer.innerHTML = '';

    CONTINENTS.forEach(function (d) {
      var path = document.createElementNS(svgNS, 'path');
      path.setAttribute('d', d);
      path.setAttribute('class', 'map-country');
      path.setAttribute('fill', 'rgba(61,212,137,0.13)');
      path.setAttribute('stroke', 'rgba(61,212,137,0.28)');
      path.setAttribute('stroke-width', '0.8');
      path.setAttribute('stroke-linejoin', 'round');
      landLayer.appendChild(path);
    });
  }

  /* ── Draw routes (UAE → each spoke) ────────────────────── */
  var routePaths = [];
  var routeParticles = [];

  function drawRoutes() {
    routeLayer.innerHTML = '';
    routePaths = [];
    routeParticles = [];

    var hub = project(HUB.lon, HUB.lat);

    SPOKES.forEach(function (s, i) {
      var pt = project(s.lon, s.lat);

      /* Build a curved path (quadratic bezier with midpoint offset) */
      var mx = (hub[0] + pt[0]) / 2;
      var my = (hub[1] + pt[1]) / 2;
      /* Offset midpoint upward for arc effect */
      var dx = pt[0] - hub[0];
      var dy = pt[1] - hub[1];
      var dist = Math.sqrt(dx * dx + dy * dy);
      var offset = dist * 0.2;
      /* Perpendicular direction */
      var perpX = -dy / (dist || 1);
      var perpY = dx / (dist || 1);
      var cpx = mx + perpX * offset;
      var cpy = my + perpY * offset;

      var dStr = 'M' + hub[0] + ',' + hub[1] + ' Q' + cpx + ',' + cpy + ' ' + pt[0] + ',' + pt[1];

      var routePath = document.createElementNS(svgNS, 'path');
      routePath.setAttribute('d', dStr);
      routePath.setAttribute('class', 'map-route');
      routePath.setAttribute('fill', 'none');
      routePath.setAttribute('stroke', 'rgba(245,197,66,0.45)');
      routePath.setAttribute('stroke-width', '1.5');
      routePath.setAttribute('stroke-dasharray', '6 5');
      routePath.setAttribute('stroke-linecap', 'round');
      routePath.setAttribute('data-country', s.name);
      routeLayer.appendChild(routePath);

      /* Sample points along the curve for particle animation */
      var pts = [];
      var steps = 80;
      for (var k = 0; k <= steps; k++) {
        var t = k / steps;
        var oneMinusT = 1 - t;
        var px = oneMinusT * oneMinusT * hub[0] + 2 * oneMinusT * t * cpx + t * t * pt[0];
        var py = oneMinusT * oneMinusT * hub[1] + 2 * oneMinusT * t * cpy + t * t * pt[1];
        pts.push([px, py]);
      }

      routePaths.push({ path: routePath, points: pts, name: s.name, index: i });

      /* Traveling particle */
      var particle = document.createElementNS(svgNS, 'circle');
      particle.setAttribute('r', '3');
      particle.setAttribute('fill', GOLD);
      particle.setAttribute('filter', 'url(#goldGlow)');
      particle.setAttribute('class', 'map-particle');
      particle.setAttribute('data-country', s.name);
      routeLayer.appendChild(particle);
      routeParticles.push({ circle: particle, points: pts, offset: i * 0.2, name: s.name });
    });
  }

  /* ── Draw markers (hub + spokes) ───────────────────────── */
  var hubPulse = null;

  function drawMarkers() {
    markerLayer.innerHTML = '';
    labelLayer.innerHTML = '';

    /* Hub */
    var hub = project(HUB.lon, HUB.lat);

    hubPulse = document.createElementNS(svgNS, 'circle');
    hubPulse.setAttribute('cx', hub[0]);
    hubPulse.setAttribute('cy', hub[1]);
    hubPulse.setAttribute('r', '30');
    hubPulse.setAttribute('fill', 'url(#hubPulse)');
    hubPulse.setAttribute('class', 'map-hub-pulse');
    markerLayer.appendChild(hubPulse);

    var hubCore = document.createElementNS(svgNS, 'circle');
    hubCore.setAttribute('cx', hub[0]);
    hubCore.setAttribute('cy', hub[1]);
    hubCore.setAttribute('r', '5');
    hubCore.setAttribute('fill', GOLD);
    hubCore.setAttribute('filter', 'url(#goldGlow)');
    hubCore.setAttribute('class', 'map-hub-core');
    markerLayer.appendChild(hubCore);

    drawLabel(hub[0], hub[1], 'UAE • HQ', true);

    /* Spokes */
    SPOKES.forEach(function (s) {
      var pt = project(s.lon, s.lat);

      var ring = document.createElementNS(svgNS, 'circle');
      ring.setAttribute('cx', pt[0]);
      ring.setAttribute('cy', pt[1]);
      ring.setAttribute('r', '12');
      ring.setAttribute('fill', 'rgba(61,212,137,0.12)');
      ring.setAttribute('class', 'map-spoke-ring');
      ring.setAttribute('data-country', s.name);
      markerLayer.appendChild(ring);

      var dot = document.createElementNS(svgNS, 'circle');
      dot.setAttribute('cx', pt[0]);
      dot.setAttribute('cy', pt[1]);
      dot.setAttribute('r', '4');
      dot.setAttribute('fill', GREEN);
      dot.setAttribute('filter', 'url(#greenGlow)');
      dot.setAttribute('class', 'map-spoke-dot');
      dot.setAttribute('data-country', s.name);
      markerLayer.appendChild(dot);

      drawLabel(pt[0], pt[1], s.name, false, s.name);
    });
  }

  /* ── Draw a label (pill badge) ─────────────────────────── */
  function drawLabel(x, y, text, isHub, dataCountry) {
    var padding = 8;
    var fontSize = isHub ? 13 : 11;
    var approxW = text.length * (fontSize * 0.58) + padding * 2;
    var h = 22;
    var bx = x - approxW / 2;
    var by = y - h - 12;
    if (bx < 4) bx = 4;
    if (bx + approxW > MAP_W - 4) bx = MAP_W - 4 - approxW;
    if (by < 4) by = y + 12;

    var rect = document.createElementNS(svgNS, 'rect');
    rect.setAttribute('x', bx);
    rect.setAttribute('y', by);
    rect.setAttribute('width', approxW);
    rect.setAttribute('height', h);
    rect.setAttribute('rx', '11');
    rect.setAttribute('class', 'map-label' + (isHub ? ' map-label-hub' : ''));
    rect.setAttribute('fill', isHub ? 'rgba(245,197,66,0.18)' : 'rgba(7,20,13,0.85)');
    rect.setAttribute('stroke', isHub ? 'rgba(245,197,66,0.8)' : 'rgba(61,212,137,0.4)');
    rect.setAttribute('stroke-width', '1');
    if (dataCountry) rect.setAttribute('data-country', dataCountry);
    labelLayer.appendChild(rect);

    var t = document.createElementNS(svgNS, 'text');
    t.setAttribute('x', bx + approxW / 2);
    t.setAttribute('y', by + h / 2 + 4);
    t.setAttribute('text-anchor', 'middle');
    t.setAttribute('font-size', fontSize);
    t.setAttribute('font-family', 'Inter, system-ui, sans-serif');
    t.setAttribute('font-weight', '600');
    t.setAttribute('fill', isHub ? GOLD : '#EAF3EC');
    if (dataCountry) t.setAttribute('data-country', dataCountry);
    t.textContent = text;
    labelLayer.appendChild(t);
  }

  /* ── Full render ───────────────────────────────────────── */
  function render() {
    drawOcean();
    drawGrid();
    drawLand();
    drawRoutes();
    drawMarkers();
  }

  /* ── Animation loop ────────────────────────────────────── */
  var t0 = performance.now();
  var running = true;

  function animate(now) {
    if (!running) return;
    var t = (now - t0) / 1000;

    if (!reduceMotion) {
      /* Animate route dashes */
      var dashOffset = -t * 25;
      routePaths.forEach(function (r) {
        var hot = activeCountry === r.name;
        r.path.style.strokeDashoffset = dashOffset;
        r.path.setAttribute('stroke', hot ? GOLD : 'rgba(245,197,66,0.45)');
        r.path.setAttribute('stroke-width', hot ? '2.5' : '1.5');
      });

      /* Animate particles along routes */
      routeParticles.forEach(function (p) {
        var prog = ((t * 0.25) + p.offset) % 1;
        var idx = Math.floor(prog * (p.points.length - 1));
        var frac = prog * (p.points.length - 1) - idx;
        var a = p.points[idx];
        var b = p.points[Math.min(idx + 1, p.points.length - 1)];
        var px = a[0] + (b[0] - a[0]) * frac;
        var py = a[1] + (b[1] - a[1]) * frac;
        p.circle.setAttribute('cx', px);
        p.circle.setAttribute('cy', py);
        var hot = activeCountry === p.name;
        p.circle.setAttribute('r', hot ? '4.5' : '3');
        p.circle.setAttribute('opacity', hot ? '1' : '0.85');
      });

      /* Hub pulse */
      if (hubPulse) {
        var pulse = Math.sin(t * 1.8) * 0.5 + 0.5;
        hubPulse.setAttribute('r', 25 + pulse * 12);
        hubPulse.setAttribute('opacity', 0.4 - pulse * 0.3);
      }

      /* Spoke ring pulse */
      var rings = markerLayer.querySelectorAll('.map-spoke-ring');
      rings.forEach(function (ring, i) {
        var p = Math.sin(t * 2 + i * 0.8) * 0.5 + 0.5;
        ring.setAttribute('r', 10 + p * 5);
        ring.setAttribute('opacity', 0.15 + p * 0.1);
      });
    }

    requestAnimationFrame(animate);
  }

  /* ── Card hover sync ───────────────────────────────────── */
  document.querySelectorAll('.country-card').forEach(function (card) {
    var name = card.getAttribute('data-country');
    card.addEventListener('mouseenter', function () { activeCountry = name; });
    card.addEventListener('mouseleave', function () { activeCountry = null; });
    card.addEventListener('focus', function () { activeCountry = name; });
    card.addEventListener('blur', function () { activeCountry = null; });
  });

  /* ── Pause when off-screen ─────────────────────────────── */
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var was = running;
        running = e.isInterIntersecting;
        if (running && !was) { t0 = performance.now(); requestAnimationFrame(animate); }
      });
    }, { threshold: 0.05 }).observe(container);
  }

  /* ── INIT — render immediately (no external deps!) ─────── */
  render();
  requestAnimationFrame(animate);

  console.log('R i D A map: rendered successfully (self-contained mode)');

})();
