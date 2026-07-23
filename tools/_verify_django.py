import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import Client
from catalog.models import Brand, Product

c = Client()
urls = ["/", "/about/", "/brands/", "/brands/ajinomoto/", "/brands/aqsa/", "/brands/oishi/"]
print("Brands:", Brand.objects.count(), "Products:", Product.objects.count())
for b in Brand.objects.all()[:5]:
    print(" ", b.slug, b.products.count())

ok = True
for url in urls:
    r = c.get(url)
    print(url, r.status_code, "bytes", len(r.content))
    if r.status_code != 200:
        ok = False
        print(r.content[:300])
    else:
        body = r.content.decode("utf-8", errors="replace")
        if url == "/brands/ajinomoto/":
            print("  has sidebar", "brand-sidebar" in body)
            print("  has product-grid", "product-grid" in body)
            print("  sample name check", "Crispy" in body or "Umami" in body or "Ginisa" in body)
        if url == "/":
            print("  dynamic brands", "/brands/ajinomoto/" in body or "ajinomoto" in body)

print("PASS" if ok else "FAIL")
