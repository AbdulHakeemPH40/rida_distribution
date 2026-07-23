"""One-shot: convert static HTML into Django templates."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "templates"
TPL.mkdir(exist_ok=True)
(TPL / "core").mkdir(exist_ok=True)
(TPL / "catalog").mkdir(exist_ok=True)
(TPL / "includes").mkdir(exist_ok=True)


def staticify(html: str) -> str:
    """Rewrite asset paths to {% static %}."""
    # href/src to local assets
    def repl_attr(m):
        attr, quote, path = m.group(1), m.group(2), m.group(3)
        if path.startswith(("http://", "https://", "//", "mailto:", "tel:", "#", "{%")):
            return m.group(0)
        # strip leading ./
        path = path.lstrip("./")
        # query strings stay outside static
        if "?" in path:
            file, qs = path.split("?", 1)
            return f'{attr}={quote}{{% static \'{file}\' %}}?{qs}{quote}'
        return f"{attr}={quote}{{% static '{path}' %}}{quote}"

    html = re.sub(
        r'\b(href|src|data-logo-en|data-logo-ar)=(["\'])(?!https?:|//|mailto:|tel:|#|{%)([^"\']+)\2',
        repl_attr,
        html,
    )
    return html


BASE = r'''{% load static %}
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}{{ SITE_NAME }} | {{ SITE_TAGLINE }} — FMCG Import & Distribution UAE{% endblock %}</title>
  <meta name="description" content="{% block meta_description %}R i D A — Reliable Innovative Distribution Alliance. UAE trusted FMCG import and distribution company.{% endblock %}">
  <meta name="robots" content="index, follow">
  <link rel="icon" href="{% static 'assets/logos/favicon.ico' %}" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="{% static 'assets/logos/favicon-32x32.png' %}">
  <link rel="apple-touch-icon" sizes="180x180" href="{% static 'assets/logos/apple-touch-icon.png' %}">
  <link rel="manifest" href="{% static 'site.webmanifest' %}">
  <meta name="theme-color" content="#0A2014">
  <link rel="canonical" href="{% block canonical %}{{ SITE_DOMAIN }}{{ request.path }}{% endblock %}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&family=Cairo:wght@700&family=Tajawal:wght@400;500&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
  <link rel="stylesheet" href="{% static 'css/style.css' %}">
  <link rel="stylesheet" href="{% static 'css/cinematic.css' %}">
  <link rel="stylesheet" href="{% static 'css/catalog.css' %}">
  {% block extra_head %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
  <div class="scroll-progress" id="scrollProgress"></div>

  <nav class="navbar" id="navbar">
    <div class="navbar-inner">
      <a href="{% url 'core:home' %}" class="navbar-logo-link">
        <img src="{% static 'assets/logos/logo_english.png' %}" data-logo-en="{% static 'assets/logos/logo_english.png' %}" data-logo-ar="{% static 'assets/logos/logo_2_arabic.png' %}" alt="R i D A Logo" class="navbar-logo">
      </a>
      <div class="navbar-links" id="navLinks">
        <a href="{% url 'core:about' %}" data-en="About" data-ar="من نحن">About</a>
        <a href="{% url 'core:home' %}#brands" data-en="Brands" data-ar="العلامات التجارية">Brands</a>
        <a href="{% url 'core:home' %}#coverage" data-en="Coverage" data-ar="التغطية">Coverage</a>
        <a href="{% url 'core:home' %}#contact" data-en="Contact" data-ar="اتصل بنا">Contact</a>
      </div>
      <div class="navbar-actions">
        <button class="lang-toggle" id="langToggle" aria-label="Toggle language">EN | AR</button>
        <button class="theme-toggle" id="themeToggle" aria-label="Toggle dark mode">
          <svg class="icon-sun" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
          <svg class="icon-moon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>
        <div class="hamburger" id="hamburger"><span></span><span></span><span></span></div>
      </div>
    </div>
  </nav>

  <div class="mobile-drawer" id="mobileDrawer" aria-hidden="true">
    <div class="mobile-drawer-head">
      <img src="{% static 'assets/logos/logo_english.png' %}" data-logo-en="{% static 'assets/logos/logo_english.png' %}" data-logo-ar="{% static 'assets/logos/logo_2_arabic.png' %}" alt="R i D A" class="mobile-drawer-logo">
      <button type="button" class="mobile-drawer-close" id="drawerClose" aria-label="Close menu">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <nav class="mobile-drawer-nav" aria-label="Mobile">
      <a href="{% url 'core:about' %}" data-en="About" data-ar="من نحن">About</a>
      <a href="{% url 'core:home' %}#brands" data-en="Brands" data-ar="العلامات التجارية">Brands</a>
      <a href="{% url 'core:home' %}#coverage" data-en="Coverage" data-ar="التغطية">Coverage</a>
      <a href="{% url 'core:home' %}#contact" data-en="Contact" data-ar="اتصل بنا">Contact</a>
    </nav>
    <div class="mobile-drawer-foot">
      <a href="{% url 'core:home' %}#contact" class="mobile-drawer-cta" data-en="Get in Touch" data-ar="تواصل معنا">Get in Touch</a>
    </div>
  </div>
  <div class="overlay" id="overlay"></div>

  {% block content %}{% endblock %}

  <footer class="footer">
    <div class="footer-watermark" aria-hidden="true">R i D A</div>
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <img id="footerLogo" src="{% static 'assets/logos/logo_english.png' %}" data-logo-en="{% static 'assets/logos/logo_english.png' %}" data-logo-ar="{% static 'assets/logos/logo_2_arabic.png' %}" alt="R i D A Logo" class="footer-logo" width="228" height="106">
          <p class="footer-tagline" data-en="Reliable Innovative Distribution Alliance — UAE's trusted FMCG distribution partner." data-ar="ريدا — شريك التوزيع الموثوق في الإمارات للسلع الاستهلاكية سريعة الحركة.">Reliable Innovative Distribution Alliance — UAE's trusted FMCG distribution partner.</p>
        </div>
        <div class="footer-col">
          <h4 class="footer-heading" data-en="Quick Links" data-ar="روابط سريعة">Quick Links</h4>
          <div class="footer-links">
            <a href="{% url 'core:about' %}" data-en="About Us" data-ar="من نحن">About Us</a>
            <a href="{% url 'core:home' %}#brands" data-en="Brands" data-ar="العلامات التجارية">Brands</a>
            <a href="{% url 'core:home' %}#contact" data-en="Contact" data-ar="اتصل بنا">Contact</a>
          </div>
        </div>
        <div class="footer-col">
          <h4 class="footer-heading" data-en="Contact Info" data-ar="معلومات الاتصال">Contact Info</h4>
          <div class="footer-links">
            <a href="tel:{{ SITE_PHONE }}">{{ SITE_PHONE_DISPLAY }}</a>
            <a href="mailto:{{ SITE_EMAIL }}">{{ SITE_EMAIL }}</a>
            <a href="https://api.whatsapp.com/send?phone={{ SITE_WHATSAPP }}&text=Hello%20R%20i%20D%20A" target="_blank" rel="noopener noreferrer" data-en="WhatsApp Chat" data-ar="محادثة واتساب">WhatsApp Chat</a>
            <a href="https://www.google.com/maps/search/?api=1&query=Dragon+Mart+2+Dubai+UAE" target="_blank" rel="noopener noreferrer">Dragon Mart 2, Dubai, U.A.E.</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p class="footer-copyright">&copy; 2026 R i D A —
          <span data-en="Reliable Innovative Distribution Alliance. All rights reserved." data-ar="ريدا — تحالف التوزيع المبتكر الموثوق. جميع الحقوق محفوظة.">Reliable Innovative Distribution Alliance. All rights reserved.</span>
        </p>
      </div>
    </div>
  </footer>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js" defer></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js" defer></script>
  <script src="{% static 'js/main.js' %}" defer></script>
  <script src="{% static 'js/cinematic.js' %}" defer></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
'''

(TPL / "base.html").write_text(BASE, encoding="utf-8")
print("wrote base.html")

# --- HOME: body content from index.html between body tags, strip nav/footer ---
index = (ROOT / "index.html").read_text(encoding="utf-8")
# extract body
body_m = re.search(r"<body[^>]*>(.*)</body>", index, re.S | re.I)
body = body_m.group(1) if body_m else index

# remove scroll progress, nav, mobile drawer, overlay (in base)
body = re.sub(r'<!-- Scroll progress bar -->\s*<div class="scroll-progress"[^>]*>.*?</div>', "", body, count=1, flags=re.S)
body = re.sub(r"<!-- ═+ NAVBAR ═+ -->\s*<nav class=\"navbar\".*?</nav>", "", body, count=1, flags=re.S)
body = re.sub(r"<!-- Mobile Drawer -->\s*<div class=\"mobile-drawer\".*?<div class=\"overlay\" id=\"overlay\"></div>", "", body, count=1, flags=re.S)
# footer
body = re.sub(r"<!-- ═+ FOOTER ═+ -->\s*<footer class=\"footer\">.*?</footer>", "", body, count=1, flags=re.S)
# scripts at end
body = re.sub(r"<!-- GSAP.*", "", body, flags=re.S)
body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.S)
body = re.sub(r'<script[^>]+src="[^"]+"[^>]*>\s*</script>', "", body)

body = staticify(body)

# Replace brand grid with dynamic loop
brand_grid_pattern = re.compile(
    r'(<div class="brands-grid stagger-cards">).*?(</div>\s*</div>\s*</section>)',
    re.S,
)
brand_loop = r'''\1
        {% for brand in brands %}
        <a href="{% url 'catalog:brand_detail' brand.slug %}" class="brand-card brand-card-link reveal-up" aria-label="View {{ brand.name }} products">
          <div class="brand-card-logo">
            {% if brand.logo %}
            <img src="{% static brand.logo %}" alt="{{ brand.name }}" loading="lazy" width="120" height="60">
            {% else %}
            <span class="brand-card-placeholder">{{ brand.name|truncatechars:12 }}</span>
            {% endif %}
          </div>
          <p class="brand-card-name">{{ brand.name }}</p>
        </a>
        {% empty %}
        <p class="product-empty">Brand catalog loading soon.</p>
        {% endfor %}
      \2'''
body2, n = brand_grid_pattern.subn(brand_loop, body, count=1)
if n == 0:
    print("WARNING: brands grid not replaced")
else:
    body = body2
    print("brands grid -> dynamic")

# fix about / why links
body = body.replace('href="{% static \'about.html\' %}"', 'href="{% url \'core:about\' %}"')
body = body.replace('href="{% static \'why-rida.html\' %}"', 'href="{% url \'core:why_rida\' %}"')
body = body.replace("href=\"about.html\"", 'href="{% url \'core:about\' %}"')
body = body.replace("href=\"why-rida.html\"", 'href="{% url \'core:why_rida\' %}"')
# staticify may have broken some # anchors — restore
body = re.sub(r"href=\"\{% static '#([^']+)' %\}\"", r'href="#\1"', body)

home = "{% extends 'base.html' %}\n{% load static %}\n{% block extra_js %}\n<script src=\"{% static 'js/globe.js' %}\" defer></script>\n{% endblock %}\n{% block content %}\n" + body.strip() + "\n{% endblock %}\n"
(TPL / "core" / "home.html").write_text(home, encoding="utf-8")
print("wrote core/home.html", len(home))

# --- ABOUT ---
about_src = ROOT / "about.html"
if about_src.exists():
    a = about_src.read_text(encoding="utf-8")
    am = re.search(r"<body[^>]*>(.*)</body>", a, re.S | re.I)
    ab = am.group(1) if am else a
    ab = re.sub(r'<div class="scroll-progress"[^>]*>.*?</div>', "", ab, count=1, flags=re.S)
    ab = re.sub(r"<nav class=\"navbar\".*?</nav>", "", ab, count=1, flags=re.S)
    ab = re.sub(r"<div class=\"mobile-drawer\".*?<div class=\"overlay\"[^>]*></div>", "", ab, count=1, flags=re.S)
    ab = re.sub(r"<footer class=\"footer\">.*?</footer>", "", ab, count=1, flags=re.S)
    ab = re.sub(r"<script[^>]*>.*?</script>", "", ab, flags=re.S)
    ab = re.sub(r'<script[^>]+src="[^"]+"[^>]*>\s*</script>', "", ab)
    ab = staticify(ab)
    ab = ab.replace("href=\"index.html\"", 'href="{% url \'core:home\' %}"')
    ab = ab.replace("href=\"index.html#", 'href="{% url \'core:home\' %}#')
    ab = re.sub(r"href=\"\{% static 'index\.html' %\}\"", 'href="{% url \'core:home\' %}"', ab)
    ab = re.sub(r"href=\"\{% static 'index\.html#([^']+)' %\}\"", r'href="{% url \'core:home\' %}#\1"', ab)
    about_tpl = "{% extends 'base.html' %}\n{% load static %}\n{% block title %}About Us | {{ SITE_NAME }}{% endblock %}\n{% block content %}\n" + ab.strip() + "\n{% endblock %}\n"
    (TPL / "core" / "about.html").write_text(about_tpl, encoding="utf-8")
    print("wrote core/about.html")
else:
    (TPL / "core" / "about.html").write_text(
        "{% extends 'base.html' %}\n{% block title %}About | {{ SITE_NAME }}{% endblock %}\n{% block content %}<main class='container' style='padding:120px 0'><h1>About R i D A</h1></main>{% endblock %}\n",
        encoding="utf-8",
    )

# why-rida
why_src = ROOT / "why-rida.html"
if why_src.exists():
    w = why_src.read_text(encoding="utf-8")
    wm = re.search(r"<body[^>]*>(.*)</body>", w, re.S | re.I)
    wb = wm.group(1) if wm else w
    wb = re.sub(r'<div class="scroll-progress"[^>]*>.*?</div>', "", wb, count=1, flags=re.S)
    wb = re.sub(r"<nav class=\"navbar\".*?</nav>", "", wb, count=1, flags=re.S)
    wb = re.sub(r"<div class=\"mobile-drawer\".*?<div class=\"overlay\"[^>]*></div>", "", wb, count=1, flags=re.S)
    wb = re.sub(r"<footer class=\"footer\">.*?</footer>", "", wb, count=1, flags=re.S)
    wb = re.sub(r"<script[^>]*>.*?</script>", "", wb, flags=re.S)
    wb = re.sub(r'<script[^>]+src="[^"]+"[^>]*>\s*</script>', "", wb)
    wb = staticify(wb)
    wb = re.sub(r"href=\"\{% static 'index\.html' %\}\"", 'href="{% url \'core:home\' %}"', wb)
    wb = re.sub(r"href=\"\{% static 'index\.html#([^']+)' %\}\"", r'href="{% url \'core:home\' %}#\1"', wb)
    wb = wb.replace("href=\"index.html\"", 'href="{% url \'core:home\' %}"')
    why_tpl = "{% extends 'base.html' %}\n{% load static %}\n{% block title %}Why R i D A | {{ SITE_NAME }}{% endblock %}\n{% block content %}\n" + wb.strip() + "\n{% endblock %}\n"
    (TPL / "core" / "why_rida.html").write_text(why_tpl, encoding="utf-8")
    print("wrote core/why_rida.html")
else:
    (TPL / "core" / "why_rida.html").write_text(
        "{% extends 'base.html' %}\n{% block content %}<main class='container' style='padding:120px 0'><h1>Why R i D A</h1></main>{% endblock %}\n",
        encoding="utf-8",
    )

# Brand detail — ecommerce layout
brand_detail = r'''{% extends 'base.html' %}
{% load static %}
{% block title %}{{ brand.name }} Products | {{ SITE_NAME }}{% endblock %}
{% block meta_description %}Browse {{ brand.name }} products distributed by R i D A across the UAE.{% endblock %}
{% block body_class %}page-brand-detail{% endblock %}
{% block content %}
<main class="brand-shop">
  <div class="container brand-shop-inner">
    <a class="brand-back" href="{% url 'core:home' %}#brands">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
      <span data-en="All Brands" data-ar="كل العلامات">All Brands</span>
    </a>

    <header class="brand-shop-hero">
      <div class="brand-shop-logo">
        {% if brand.logo %}
        <img src="{% static brand.logo %}" alt="{{ brand.name }}" width="140" height="70" loading="eager">
        {% endif %}
      </div>
      <div class="brand-shop-hero-text">
        <span class="brand-page-kicker" data-en="Brand Range" data-ar="تشكيلة العلامة">Brand Range</span>
        <h1 class="brand-shop-title">{{ brand.name }}</h1>
        <p class="brand-shop-sub" data-en="Products distributed by R i D A across the UAE. Size variants are grouped — names show without gram weights." data-ar="منتجات توزعها ريدا في الإمارات. تم تجميع أحجام المنتج المتشابهة.">
          Products distributed by R i D A across the UAE. Size variants are grouped — names show without gram weights.
        </p>
        <div class="brand-page-count">{{ total_count }} product{{ total_count|pluralize }}</div>
      </div>
    </header>

    <div class="brand-shop-layout">
      {# LEFT SIDEBAR #}
      <aside class="brand-sidebar" aria-label="Categories">
        <div class="brand-sidebar-card">
          <h2 class="brand-sidebar-heading" data-en="Categories" data-ar="الفئات">Categories</h2>
          <nav class="brand-cat-nav">
            <a href="{% url 'catalog:brand_detail' brand.slug %}"
               class="brand-cat-link{% if not active_category %} is-active{% endif %}">
              <span data-en="All products" data-ar="كل المنتجات">All products</span>
              <span class="brand-cat-count">{{ total_count }}</span>
            </a>
            {% for cat in categories %}
            <a href="?category={{ cat.slug }}{% if search_q %}&q={{ search_q|urlencode }}{% endif %}"
               class="brand-cat-link{% if active_category.slug == cat.slug %} is-active{% endif %}">
              <span>{{ cat.name }}</span>
              <span class="brand-cat-count">{{ cat.n }}</span>
            </a>
            {% endfor %}
          </nav>
        </div>

        <div class="brand-sidebar-card brand-sidebar-brands">
          <h2 class="brand-sidebar-heading" data-en="Other brands" data-ar="علامات أخرى">Other brands</h2>
          <nav class="brand-cat-nav brand-cat-nav-compact">
            {% for b in all_brands %}
            <a href="{% url 'catalog:brand_detail' b.slug %}"
               class="brand-cat-link{% if b.slug == brand.slug %} is-active{% endif %}">{{ b.name }}</a>
            {% endfor %}
          </nav>
        </div>
      </aside>

      {# MAIN GRID #}
      <section class="brand-shop-main">
        <form class="brand-shop-toolbar" method="get" action="">
          {% if active_category %}
          <input type="hidden" name="category" value="{{ active_category.slug }}">
          {% endif %}
          <div class="brand-search">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3-3"/></svg>
            <input type="search" name="q" value="{{ search_q }}" placeholder="Search products…" aria-label="Search products">
          </div>
          <p class="brand-shop-showing">
            Showing <strong>{{ product_count }}</strong>
            {% if active_category %}in {{ active_category.name }}{% endif %}
          </p>
        </form>

        <div class="product-grid stagger-cards">
          {% for p in products %}
          <article class="product-card reveal-up">
            <div class="product-card-thumb" aria-hidden="true">
              <span class="product-card-initial">{{ p.name|first|upper }}</span>
            </div>
            <h3 class="product-card-name">{{ p.name }}</h3>
            <div class="product-card-meta">
              {% if p.category %}<span class="product-card-cat">{{ p.category.name }}</span>{% endif %}
              <span class="product-card-unit">{{ p.unit }}</span>
            </div>
          </article>
          {% empty %}
          <div class="product-empty">
            {% if brand.slug == 'aqsa' %}
            Aqsa product range coming soon — placeholder brand for now.
            {% else %}
            No products match this filter. Try another category or clear search.
            {% endif %}
          </div>
          {% endfor %}
        </div>

        <div class="brand-shop-cta">
          <a href="{% url 'core:home' %}#contact" class="btn btn-primary" data-en="Enquire about this brand" data-ar="استفسر عن هذه العلامة">Enquire about this brand</a>
        </div>
      </section>
    </div>
  </div>
</main>
{% endblock %}
'''
(TPL / "catalog" / "brand_detail.html").write_text(brand_detail, encoding="utf-8")
print("wrote catalog/brand_detail.html")

brand_list = r'''{% extends 'base.html' %}
{% load static %}
{% block title %}Brands | {{ SITE_NAME }}{% endblock %}
{% block content %}
<main class="brand-shop">
  <div class="container" style="padding-top:120px;padding-bottom:64px">
    <h1 class="brand-shop-title">All Brands</h1>
    <div class="brands-grid stagger-cards" style="margin-top:32px">
      {% for brand in brands %}
      <a href="{% url 'catalog:brand_detail' brand.slug %}" class="brand-card brand-card-link">
        <div class="brand-card-logo">
          {% if brand.logo %}<img src="{% static brand.logo %}" alt="{{ brand.name }}" loading="lazy" width="120" height="60">{% endif %}
        </div>
        <p class="brand-card-name">{{ brand.name }}</p>
        <p class="brand-card-count">{{ brand.n_products }} products</p>
      </a>
      {% endfor %}
    </div>
  </div>
</main>
{% endblock %}
'''
(TPL / "catalog" / "brand_list.html").write_text(brand_list, encoding="utf-8")
print("wrote catalog/brand_list.html")

# catalog CSS
css = r'''
/* ===== Brand shop (ecommerce layout) ===== */
.brand-shop {
  padding-top: calc(var(--nav-h, 72px) + 28px);
  padding-bottom: 72px;
  min-height: 70vh;
}
.brand-shop-inner { max-width: 1200px; }
.brand-back {
  display: inline-flex; align-items: center; gap: 8px;
  margin-bottom: 18px; font-size: .92rem; font-weight: 600;
  color: var(--green-primary, #1f7a4d); text-decoration: none;
}
.brand-back:hover { text-decoration: underline; }

.brand-shop-hero {
  display: flex; flex-wrap: wrap; align-items: center; gap: 24px 32px;
  margin-bottom: 28px; padding: 24px 28px; border-radius: 20px;
  background: var(--surface, #fff);
  border: 1px solid var(--border, rgba(0,0,0,.06));
  box-shadow: 0 8px 28px rgba(10,32,20,.06);
}
.brand-shop-logo {
  width: 140px; height: 88px; display: flex; align-items: center; justify-content: center;
  border-radius: 14px; background: #f4f7f5; border: 1px solid rgba(0,0,0,.04); padding: 12px; flex-shrink: 0;
}
.brand-shop-logo img { max-width: 100%; max-height: 64px; object-fit: contain; }
.brand-shop-title {
  margin: 0 0 8px; font-size: clamp(1.6rem, 3vw, 2.2rem); font-weight: 800;
  color: var(--text, #0a2014); line-height: 1.15;
}
.brand-shop-sub { margin: 0; color: var(--text-muted, #5a7264); font-size: 1rem; max-width: 560px; }
.brand-page-kicker {
  display: inline-block; font-size: .75rem; font-weight: 600; letter-spacing: .12em;
  text-transform: uppercase; color: var(--green-primary, #1f7a4d); margin-bottom: 8px;
}
.brand-page-count {
  margin-top: 12px; display: inline-flex; align-items: center; gap: 8px;
  font-size: .9rem; font-weight: 600; color: var(--green-primary, #1f7a4d);
  background: rgba(31,122,77,.08); padding: 6px 12px; border-radius: 999px;
}

.brand-shop-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}
@media (max-width: 900px) {
  .brand-shop-layout { grid-template-columns: 1fr; }
  .brand-sidebar-brands { display: none; }
}

.brand-sidebar { position: sticky; top: calc(var(--nav-h, 72px) + 16px); }
.brand-sidebar-card {
  background: var(--surface, #fff);
  border: 1px solid var(--border, rgba(0,0,0,.06));
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 14px;
  box-shadow: 0 4px 14px rgba(10,32,20,.04);
}
.brand-sidebar-heading {
  margin: 0 0 12px; font-size: .78rem; font-weight: 700;
  letter-spacing: .08em; text-transform: uppercase; color: var(--text-muted, #5a7264);
}
.brand-cat-nav { display: flex; flex-direction: column; gap: 4px; }
.brand-cat-link {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 10px 12px; border-radius: 10px; text-decoration: none;
  color: var(--text, #0a2014); font-size: .92rem; font-weight: 500;
  transition: background .15s ease, color .15s ease;
}
.brand-cat-link:hover { background: rgba(31,122,77,.08); }
.brand-cat-link.is-active {
  background: rgba(31,122,77,.14);
  color: var(--green-primary, #1f7a4d);
  font-weight: 700;
}
.brand-cat-count {
  font-size: .75rem; font-weight: 700; color: var(--text-muted, #5a7264);
  background: rgba(0,0,0,.04); padding: 2px 8px; border-radius: 999px;
}
.brand-cat-link.is-active .brand-cat-count {
  background: rgba(31,122,77,.18); color: var(--green-primary, #1f7a4d);
}
.brand-cat-nav-compact .brand-cat-link { padding: 8px 10px; font-size: .86rem; }

.brand-shop-toolbar {
  display: flex; flex-wrap: wrap; align-items: center; gap: 14px 20px;
  margin-bottom: 18px;
}
.brand-search {
  flex: 1; min-width: 200px; display: flex; align-items: center; gap: 10px;
  background: var(--surface, #fff); border: 1px solid var(--border, rgba(0,0,0,.08));
  border-radius: 12px; padding: 10px 14px;
}
.brand-search input {
  border: 0; outline: 0; background: transparent; width: 100%;
  font: inherit; color: var(--text, #0a2014);
}
.brand-shop-showing { margin: 0; font-size: .9rem; color: var(--text-muted, #5a7264); }

.product-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
@media (max-width: 900px) { .product-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .product-grid { grid-template-columns: 1fr; } }

.product-card {
  background: var(--surface, #fff);
  border: 1px solid var(--border, rgba(0,0,0,.06));
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 14px rgba(10,32,20,.04);
  transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
  min-width: 0;
  display: flex; flex-direction: column; gap: 10px;
}
.product-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(10,32,20,.1);
  border-color: rgba(31,122,77,.22);
}
.product-card-thumb {
  height: 88px; border-radius: 12px;
  background: linear-gradient(145deg, rgba(31,122,77,.1), rgba(31,122,77,.02));
  display: flex; align-items: center; justify-content: center;
}
.product-card-initial {
  width: 48px; height: 48px; border-radius: 12px;
  display: grid; place-items: center;
  font-weight: 800; font-size: 1.2rem;
  color: var(--green-primary, #1f7a4d);
  background: rgba(255,255,255,.7);
  border: 1px solid rgba(31,122,77,.12);
}
.product-card-name {
  margin: 0; font-size: .98rem; font-weight: 650; line-height: 1.35;
  color: var(--text, #0a2014); word-break: break-word;
}
.product-card-meta {
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  font-size: .78rem; color: var(--text-muted, #5a7264); margin-top: auto;
}
.product-card-unit, .product-card-cat {
  padding: 2px 8px; border-radius: 999px;
  background: rgba(31,122,77,.08); color: var(--green-primary, #1f7a4d);
  font-weight: 600; font-size: .72rem;
}
.product-card-cat { background: rgba(0,0,0,.04); color: var(--text-muted, #5a7264); }
.product-empty {
  grid-column: 1 / -1; text-align: center; padding: 48px 20px;
  color: var(--text-muted, #5a7264);
  border: 1px dashed var(--border, #ccc); border-radius: 16px;
}
.brand-shop-cta { margin-top: 36px; text-align: center; }

a.brand-card-link { text-decoration: none; color: inherit; display: flex; flex-direction: column; align-items: center; height: 100%; }
.brand-card-count { font-size: .8rem; color: var(--text-muted, #5a7264); margin: 4px 0 0; }

[data-theme="dark"] .brand-shop-hero,
[data-theme="dark"] .brand-sidebar-card,
[data-theme="dark"] .product-card,
[data-theme="dark"] .brand-search,
html.dark .brand-shop-hero,
html.dark .brand-sidebar-card,
html.dark .product-card,
html.dark .brand-search {
  background: var(--bg-card, #0f2419);
  border-color: rgba(255,255,255,.06);
}
[data-theme="dark"] .brand-shop-logo,
html.dark .brand-shop-logo { background: rgba(255,255,255,.04); }
[data-theme="dark"] .brand-shop-title,
[data-theme="dark"] .product-card-name,
html.dark .brand-shop-title,
html.dark .product-card-name { color: var(--text, #e8f0ea); }
'''
css_path = ROOT / "css" / "catalog.css"
css_path.write_text(css, encoding="utf-8")
print("wrote css/catalog.css")

# favicon + webmanifest into static-friendly places: also copy site.webmanifest note
# Ensure static/site.webmanifest via assets path - add empty static keep
(ROOT / "static" / ".gitkeep").write_text("", encoding="utf-8")
# Copy site.webmanifest and favicon into static root aliases if needed
import shutil
for name in ("site.webmanifest", "favicon.ico", "robots.txt"):
    src = ROOT / name
    if src.exists():
        # serve via staticfiles_dirs assets won't cover root files — put in static/
        shutil.copy2(src, ROOT / "static" / name)
        print("copied", name, "-> static/")

print("DONE")
