#!/usr/bin/env python3
import os
import re
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from django.test import Client

from catalog.models import Brand, Product

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("STATICFILES_DIRS", settings.STATICFILES_DIRS)
print("STATIC_ROOT", settings.STATIC_ROOT)
print("brands", Brand.objects.filter(is_active=True).count())
print("products", Product.objects.filter(is_active=True).count())

c = Client()
checks = [
    "/",
    "/about/",
    "/why-rida/",
    "/brands/",
    "/brands/ajinomoto/",
    "/brands/aqsa/",
    "/static/css/style.css",
    "/static/css/cinematic.css",
    "/static/css/catalog.css",
    "/static/js/main.js",
    "/static/assets/logos/logo_english.png",
    "/static/assets/images/brands/oishi.png",
    "/static/assets/images/stock/hero.jpg",
]
ok = True
for u in checks:
    r = c.get(u)
    flag = "OK" if r.status_code == 200 else "FAIL"
    if r.status_code != 200:
        ok = False
    print(flag, r.status_code, u)

r = c.get("/")
html = r.content.decode("utf-8")
tests = {
    "gsap cdn": "gsap" in html.lower(),
    "google fonts": "fonts.googleapis.com" in html,
    "style.css": "/static/css/style.css" in html,
    "cinematic.css": "/static/css/cinematic.css" in html,
    "catalog.css": "/static/css/catalog.css" in html,
    "main.js": "/static/js/main.js" in html,
    "logo": "/static/assets/logos/logo_english.png" in html,
    "brand links": len(re.findall(r"/brands/[a-z0-9-]+/", html)) >= 10,
    "no template leak": "{% for" not in html and "{% url" not in html,
    "single navbar": html.count('class="navbar"') == 1,
    "single footer": html.count('class="footer"') == 1,
    "id brands": 'id="brands"' in html,
}
for k, v in tests.items():
    print(("OK" if v else "FAIL"), k, v)
    if not v:
        ok = False

r2 = c.get("/brands/ajinomoto/")
h2 = r2.content.decode("utf-8")
print("ajinomoto sidebar", "brand-sidebar" in h2)
print("ajinomoto product cards", h2.count("product-card"))
if "brand-sidebar" not in h2:
    ok = False

print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
