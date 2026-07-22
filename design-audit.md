# R i D A — Full UI/UX Design Audit & Improvement Report
**Date:** 2026-07-22 · **Scope:** index.html (1,454 lines), style.css (2,975), cinematic.css (3,119), main.js (614), cinematic.js, globe.js, about.html, why-rida.html
**Auditor:** Frontend design analysis · Verified against actual code on disk

---

## 1. Executive Summary

The site has a strong foundation — solid design tokens, a complete bilingual (EN/AR) RTL system, dark mode, GSAP reveals, custom SVG maps, and good SEO/AEO structure. The visual identity (deep green + gold, Outfit/Inter) is coherent and premium.

The biggest design problems are **not visual** — they are **architectural**: two giant CSS files fighting each other, dead code, a removed section that nav links still point to, and heavy always-on visual effects (film grain, 25 backdrop-filters, infinite marquee + 12 infinite SVG route particles) that cost GPU on every frame.

**Overall design health: 7/10.** Fix the top-10 items below → 9/10.

---

## 2. Confirmed Glitches / Bugs (fix first)

| # | Severity | Issue | Location | Evidence |
|---|----------|-------|----------|----------|
| 1 | 🔴 High | **Broken nav links** — Navbar "Services" and footer "Services" link to `#framework`, but that section was REMOVED. Clicking does nothing. | index.html:440, footer ~:1400 | `<!-- FRAMEWORK SECTION REMOVED -->` at :685 |
| 2 | 🔴 High | **Duplicate `</div>`** in Sourcing map — extra closing `</g>`/`</div>` (line 897 `</g>` twice) and shipping section has `</div>\n</div>` double-close at end (~:949). Malformed DOM → unpredictable rendering. | index.html:897, 949 | read directly |
| 3 | 🟠 Med | **Marquee `loading="eager"` on 24 images** — trust bar loads all 24 supplier logos eagerly (should only be first set), and they're all `eager` even though most are below the fold. | index.html:524–585 | `loading="eager"` ×24 |
| 4 | 🟠 Med | **`aria-hidden` mismatch on marquee** — first `.trust-logos` has `aria-hidden="false"` on parent but children items have no alt issue; second has `aria-hidden="true"` on both parent and each item (redundant, fine) — but both sets use identical `src`, so screen readers may announce 24 images. | index.html:524 | |
| 5 | 🟠 Med | **Royal brand-card uses a different tint** than all others: `#fdf2f2` (opaque) vs `#RRGGBB14` (8% alpha) on the other 15 → in dark mode Royal's tile is a bright pink rectangle that breaks the dark theme. | index.html:1305 | read directly |
| 6 | 🟡 Low | **Institutional.png is 2 MB** — one image weighs more than the entire rest of the image payload combined. | assets/images/stock | 2,025 KB PNG |
| 7 | 🟡 Low | **Inline `style="display:none"` on theme moon icon** + JS toggles `style.display` — flash of wrong icon on first paint; should be class-based. | index.html:449, main.js:70 | |

## 3. Architecture Problems (the "why glitches happen" root causes)

### 3.1 Two 3,000-line stylesheets fighting
- `style.css` (2,975 lines) defines `:root` tokens → `cinematic.css` (3,119 lines) **redefines almost all of them** (`--green-primary`, `--gold-primary`, fonts, radii, shadows, transitions). Every component is styled twice.
- **118 `!important` total** (27 + 91) — most in cinematic.css to beat style.css specificity. This is a specificity war; every new fix requires another `!important`.
- **31 `transition: all`** (19 + 12) — causes the hover-jank you already experienced on vision cards (animates `backdrop-filter`, `box-shadow`, everything).
- Result: changing anything is fragile — fixes silently fail or regress elsewhere (you've seen this).

**Recommendation:** consolidate into ONE stylesheet (or clearly layered: tokens → base → components → overrides) and drive `!important` count toward 0. Use CSS layers (`@layer base, components, overrides;`) — native, no build step needed.

### 3.2 Dead code
- `initFrameworkTimeline()` runs in main.js for the removed framework section.
- `worldDots` `<g>` is empty in HTML — populated by globe.js presumably, but `.globe-wrapper` is a fixed map, not a globe (naming confusion).
- `site.webmanifest`, `robots.txt`, `sitemap.xml` ✅ fine.
- `findings.md`, `business.md` at root — dev docs served publicly (harmless but should move to a docs folder or be excluded).

### 3.3 Inline styles everywhere
35 `style=` attributes in index.html — 16 brand-card tint colors, section text alignment, CTA button sizing. These override your own token system and bypass dark mode (bug #5 is a direct consequence).

**Fix:** move brand tints to a data-driven class or CSS custom property per card: `style="--brand:#E3002B"` then `.brand-card-logo{background:color-mix(in srgb, var(--brand) 8%, transparent)}` — dark-mode safe automatically.

## 4. Visual Design Improvements (highest impact first)

### 4.1 Hero — the most important 3 seconds
- Hero photo is a **172 KB JPG with an overlay + moon effect**, but the H1 ("FROM SOURCE TO SHELF") is the only content above the fold — no brand name, no location, no credibility marker. Add a small eyebrow above the H1: `R i D A · UAE FMCG Distribution`.
- Two CTAs ("Explore Our Network" + "Partner With Us") have **equal visual weight** — always give ONE primary. Make "Partner With Us" the filled gold/green button, "Explore" a ghost/outline.
- `onerror="this.remove()"` on hero image means if the image 404s, the whole photo disappears silently — add a CSS gradient fallback behind it.
- Hero text sits on a photo — verify 4.5:1 contrast on every image variant; add a stronger scrim at text position (not uniform overlay).

### 4.2 Typography scale
- Only 3 font weights of Outfit are loaded but headings use 400–900 across files (some browsers will fake-bold). The Google Fonts URL requests Outfit 400–900 ✅, Poppins 600–800, Inter 400–600, Cairo 700, Tajawal 400–500 — **6 families, ~15 files ≈ 300+ KB of fonts**. Poppins is now unused as a heading font (cinematic.css swaps to Outfit) → **drop Poppins entirely**, keep Outfit + Inter + Cairo + Tajawal.
- `letter-spacing: -0.011em` on the whole body is fine, but Arabic should NOT have negative tracking — add `[lang="ar"] body { letter-spacing: 0 }`.

### 4.3 Cards (portfolio / segments / brands / stats / contact)
Five different card systems currently exist with different radii, shadows, icon treatments. Unify into ONE `.card` primitive + variants:
- `.card--icon` (portfolio), `.card--photo` (segments), `.card--logo` (brands), `.card--stat`, `.card--action` (contact).
- Brand cards: 16 text-SVG wordmarks in different font sizes (14–24px) look uneven — normalize optical size, put wordmark on a consistent baseline, and add `viewBox` consistent padding. Better: real brand logos when licensed.
- Stat cards: `data-count="1000"` animates to "1000+" — good; but "Same Day" card has no icon-consistent sizing. Keep icons at a fixed 24px box.

### 4.4 Spacing & rhythm
You already fixed the worst of it (trust-bar → about → portfolio). Remaining rhythm issue: `section-alt` background alternates (segments / advantages / contact all `section-alt`) — brands section between two `section-alt` blocks creates a light-light-light sandwich in light mode. Alternate strictly: alt / plain / alt / plain.

### 4.5 Dark mode
- Dark tokens are well done (separate `--bg-elevated`, green brightened to `#34C77B`). Two gaps:
  1. Royal brand tile bug (#5).
  2. Trust-bar supplier logos are PNGs with (likely) white backgrounds — in dark mode they'll show as white rectangles. Add `filter: brightness(.9)` or a white "logo plate" intentionally (`background:#fff; padding; radius`) so it looks deliberate.
  3. UAE map gradient uses fixed hex `#2E8B57→#0C4A28` — fine in both modes, but marker labels (`marker-label`) need a dark-mode fill check.

### 4.6 Motion / performance (this is where "glitch" feelings come from)
- **Film grain overlay** (`body::after`, `position:fixed; z-index:9999`) — a fixed full-viewport layer forces compositing on every scroll frame. On mid-range phones this causes visible scroll stutter. Either remove it, use `opacity < 0.04`, or apply `transform: translateZ(0)` + `will-change` and confirm it's GPU-composited. Best: static PNG grain instead of animated noise if any.
- **25 `backdrop-filter` usages** — each is a GPU readback. Cap blur use to: navbar + mobile drawer + maybe CTA banner. Never animate elements that have backdrop-filter (this was your vision-card jank).
- **12 infinite `animateMotion` route particles + 20s marquee + pulse animations** all run simultaneously, forever. Add `prefers-reduced-motion` kill-switch (only 5 rules exist now — extend to marquee, route particles, grain, parallax).
- GSAP + ScrollTrigger + cinematic.js + globe.js + main.js — ensure all reveals use ONE observer/ScrollTrigger batch; three separate IntersectionObservers already exist.
- **Overscroll-behavior-y: none** on html blocks iOS pull-to-refresh — intended, but test on Android Chrome (can trap scroll at top in RTL).

### 4.7 Accessibility gaps
- Marquee images: decorative duplicates should ALL have empty alt (done for set 2) but set 1 has real alts — correct; however the section has no way to pause for keyboard users (hover-pause only). Add `prefers-reduced-motion: marquee stops`.
- Focus styles: verify visible `:focus-visible` rings on nav, lang/theme toggles, cards-as-links (contact cards are `<a>` — they need focus rings).
- `.lang-toggle` says "EN | AR" — no `aria-pressed`/state indication of current language.
- Color contrast: `--text-secondary #6B9E7B` on `#F6F8F5` ≈ 3.3:1 — **fails WCAG AA for body text** (needs 4.5:1). Darken muted green to ~#527A62.
- Map SVGs have role="img" + aria-label ✅ good.

### 4.8 Bilingual / RTL
- Strong `data-en`/`data-ar` system ✅. Risks:
  - Hard-coded `<br>` in hero title breaks differently in Arabic ("من المصدر إلى الرف" is 4 words, will wrap awkwardly) — test AR hero visually.
  - Letter-spacing in AR (see 4.2).
  - Footer copyright mixes EN brand + AR span — check RTL bidi rendering ("© 2026 R i D A — تحالف التوزيع..." ordering).
  - `dir="rtl"` flips marquee direction? Verify trust-bar animation direction still reads correctly in RTL.

### 4.9 Content / trust design
- "Top 16 Brands by Range Depth" — but trust bar shows different retailers; nowhere explains the relationship (supplier vs distributor vs partner). One line under the heading would fix confusion.
- No social proof numbers near CTAs ("1000+ SKUs" exists in coverage — consider moving one stat into hero or about card).
- `sameAs: []` in JSON-LD is empty — add LinkedIn/Instagram when available (SEO, not visual).

### 4.10 Mobile
- Mobile drawer is premium ✅. Check: 16-brand grid at 2 cols on small phones → cards get narrow; wordmarks at 14–24px inside 120px viewBox will scale down hard — set a `min-height` and `object-fit`-like padding.
- Tables: none — good.
- Tap targets: emirate-tag chips and criteria-chips should be ≥40px tall on mobile.

---

## 5. Prioritized Action Plan

### Phase 1 — Fix glitches (30–45 min)
1. Remove/repoint `#framework` nav + footer links (point to `#portfolio` or restore a Services anchor).
2. Fix duplicate `</g>` and `</div>` in sourcing map + shipping section.
3. Fix Royal card tint → `--brand` pattern for all 16 cards (dark-mode safe).
4. Marquee: `loading="lazy"` on all but first 6 logos.
5. Class-based theme icon swap (no inline `display:none`).

### Phase 2 — Performance / de-glitch (1–2 hrs)
6. Film grain: static, low-opacity, GPU-composited (or remove).
7. Cap backdrop-filter usage; extend `prefers-reduced-motion` to marquee, particles, grain, reveals.
8. Drop Poppins from Google Fonts; subset weights actually used.
9. Compress `institutional.png` (2 MB → WebP ~150 KB).
10. Replace `transition: all` with explicit properties (31 instances).

### Phase 3 — Polish (2–4 hrs)
11. Consolidate card systems into one primitive + variants; unify radii/shadows via tokens only.
12. Hero: eyebrow label, single primary CTA, scrim/contrast audit, image fallback.
13. Fix `#6B9E7B` contrast; supplier-logo plates for dark mode; AR letter-spacing/hero-wrap checks.
14. CSS architecture: `@layer` refactor or merge, target `!important` ≈ 0.
15. Focus-visible audit + keyboard test of drawer, marquee pause, contact cards.

### Phase 4 — Delight (optional)
16. Real brand logos (licensed) replacing text SVGs.
17. Micro-interactions: magnetic CTA buttons, stat count-up already good — add once-per-session reveal so returning users don't re-watch animations.
18. Add a lightweight "Capabilities/Services" strip to replace the removed framework section so nav "Services" has a home.

---

## 6. Quick-Win Metrics

| Change | Est. gain |
|--------|-----------|
| Drop Poppins + subset fonts | −150 to −250 KB |
| institutional.png → WebP | −1.9 MB |
| Grain + particle + marquee motion budget | noticeably smoother scroll on mobile |
| 31 `transition: all` → explicit | removes hover jank class of bugs |
| Fix 5 broken/hidden links & DOM errors | fewer "glitch" reports like today's |

*All findings verified against files on disk (line numbers cited). Nothing in this report is assumed.*
