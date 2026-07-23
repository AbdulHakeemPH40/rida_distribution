# R i D A — Django site

Full Django conversion of the R i D A FMCG distribution website.

## Stack

- **Django 5.x** + SQLite
- Apps: `core` (home / about / why-rida), `catalog` (brands + products)
- Shared layout: `templates/base.html` (nav, footer, SEO, CDNs)
- Static assets: everything under `static/` (`css/`, `js/`, `assets/`)

## Quick start

```powershell
cd C:\Users\Hakeem1\OneDrive\Desktop\Rida
pip install -r requirements.txt
python manage.py migrate
python manage.py import_catalog
python manage.py runserver
```

| URL | Page |
|-----|------|
| http://127.0.0.1:8000/ | Homepage (dynamic brand grid) |
| http://127.0.0.1:8000/about/ | About |
| http://127.0.0.1:8000/why-rida/ | Why R i D A |
| http://127.0.0.1:8000/brands/ | Brand list |
| http://127.0.0.1:8000/brands/ajinomoto/ | Brand shop (sidebar + products) |
| http://127.0.0.1:8000/admin/ | Django admin |

## Project layout

```
Rida/
├── manage.py
├── config/                 # settings, urls, wsgi
├── core/                   # home, about, why-rida views
├── catalog/                # Brand / Category / Product + import_catalog
├── templates/
│   ├── base.html           # CDNs, fonts, GSAP, nav, footer
│   ├── core/
│   │   ├── home.html       # index content (extends base)
│   │   ├── about.html
│   │   └── why_rida.html
│   └── catalog/
│       ├── brand_list.html
│       └── brand_detail.html   # ecommerce sidebar shop
├── static/                 # CANONICAL front-end assets
│   ├── css/                # style.css, cinematic.css, catalog.css
│   ├── js/                 # main.js, cinematic.js, globe.js
│   └── assets/             # logos, brand images, stock, supplier
├── media/                  # user uploads (if any)
├── _legacy_static/         # old root HTML archived (not served)
├── css/ js/ assets/        # original copies (optional; static/ is live)
└── R i D A .xlsx           # catalog source
```

## How templates are wired

1. **`base.html`** — full `<head>` from the old site:
   - Google Fonts, GSAP (cdnjs), SEO/OG/Twitter, JSON-LD
   - `{% static %}` for CSS/JS/logos
   - Shared navbar + mobile drawer + footer
   - `{% block content %}` / `{% block extra_head %}` / `{% block extra_js %}`

2. **Page templates** extend base and only fill content:
   - `templates/core/home.html` ← former `index.html` body
   - `templates/core/about.html` ← former `about.html` body
   - `templates/core/why_rida.html` ← former `why-rida.html` body
   - `templates/catalog/brand_detail.html` ← ecommerce brand page

3. **Brand grid on home** loops DB brands:
   ```django
   {% for brand in brands %}
     <a href="{% url 'catalog:brand_detail' brand.slug %}">...</a>
   {% endfor %}
   ```

## Catalog import

```powershell
python manage.py import_catalog
```

- Reads `R i D A .xlsx`
- Matches rows to the 16 site brands
- Strips gram/ml from display names
- Dedupes size variants
- Builds sidebar categories
- **Aqsa** stays a placeholder until you provide the real logo/items

## Notes

- Live UI is **only** Django (`templates/` + `static/`).
- Old `index.html` / `about.html` / `why-rida.html` / `brands/*.html` live in `_legacy_static/` for reference — not served.
- Create admin user: `python manage.py createsuperuser`
- Production collect: `python manage.py collectstatic`
