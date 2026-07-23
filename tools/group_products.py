"""Group Excel catalog by site brands; dedupe weight variants; emit JSON + pages."""
from __future__ import annotations

import html as html_lib
import json
import re
from collections import defaultdict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "R i D A .xlsx"
OUT = ROOT / "assets" / "data" / "brand-products.json"
BRANDS_DIR = ROOT / "brands"

SITE_BRANDS = [
    ("Oishi", ["oishi"], "oishi.png"),
    ("Nissin", ["nissin"], "nissin.png"),
    ("Jack 'n Jill", ["jack n jill", "jack 'n jill", "jack n' jill", "jack n` jill", "jacknjill"], "jack n jill.png"),
    ("Mr. Gulaman", ["mr. gulaman", "mr gulaman", "mr.gulaman", "gulaman"], "mr gulman.png"),
    ("Bench", ["bench", "baby bench"], "bench.png"),
    ("Nestle", ["nestle", "nestlé", "nescafé", "nescafe"], "nestle.png"),
    ("Del Monte", ["del monte", "delmonte"], "Delmonte.png"),
    ("Purefoods", ["purefoods", "pure foods", "purefood"], "pure food.png"),
    ("Lucky Me!", ["lucky me!", "lucky me", "luckyme"], "luckyme.png"),
    ("Century Tuna", ["century tuna", "century"], "century tuna.png"),
    ("UFC", ["ufc"], "ufc.png"),
    ("Regent", ["regent"], "regent.png"),
    ("Knorr", ["knorr"], "knorr.png"),
    ("Ajinomoto", ["ajinomoto", "ajinmoto"], "Ajinmoto.png"),
    ("Zonrox", ["zonrox"], "Zonrox.png"),
    ("Aqsa", ["aqsa", "royal"], "aqsa.png"),
]

MULTI_SPACE = re.compile(r"\s+")
SIZE_TOKEN = re.compile(
    r"(?:^|[\s\-/(])(?:\d+(?:[.,]\d+)?\s*(?:kg|gms?|grms?|grams?|g|ml|ltrs?|liters?|litres?|ltr|cl|oz)|"
    r"\d+\s*x\s*\d+(?:[.,]\d+)?\s*(?:kg|gms?|g|ml|l)?|\d+(?:[.,]\d+)?\s*(?:pcs?|pc|pack|pk)|x\s*\d+)"
    r"(?=$|[\s\-/,)])",
    re.I,
)
SIZE_DEBRIS = re.compile(r"(?:^|\s)(?:gm|gms|gr|grm|kg|ml|ltr)\b\.?", re.I)
PAREN_EMPTY = re.compile(r"\(\s*[\d.,]*\s*\)")
TRAIL_PUNCT = re.compile(r"[\s\-/|,;:]+$")


def slugify(s: str) -> str:
    s = s.lower().replace("é", "e").replace("'", "").replace("`", "").replace("!", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def normalize_name(name: str) -> str:
    n = str(name).replace("`", "'").replace("\u2019", "'").replace("\u2013", "-")
    return MULTI_SPACE.sub(" ", n).strip()


def strip_sizes(name: str) -> str:
    n = SIZE_TOKEN.sub(" ", name)
    n = PAREN_EMPTY.sub(" ", n)
    n = SIZE_DEBRIS.sub(" ", n)
    n = MULTI_SPACE.sub(" ", n).strip()
    n = TRAIL_PUNCT.sub("", n)
    return MULTI_SPACE.sub(" ", n).strip(" -")


def match_brand(name: str):
    lower = name.lower()
    best = None
    best_len = 0
    for display, kws, logo in SITE_BRANDS:
        for kw in kws:
            if lower.startswith(kw) or re.search(r"(?i)(?:^|[\s\-])" + re.escape(kw) + r"(?:$|[\s\-])", name):
                if len(kw) > best_len:
                    best = (display, kws, logo)
                    best_len = len(kw)
    # Jack N` Jill glued variants
    if best is None and re.match(r"(?i)^jack\s*n", name):
        for display, kws, logo in SITE_BRANDS:
            if display.startswith("Jack"):
                return display, kws, logo
    if best is None and re.match(r"(?i)^mr\.?\s*gulaman", name):
        for display, kws, logo in SITE_BRANDS:
            if "Gulaman" in display:
                return display, kws, logo
    return best


def strip_brand_prefix(name: str, keywords: list, brand: str) -> str:
    lower = name.lower()
    for kw in sorted(keywords, key=len, reverse=True):
        if lower.startswith(kw):
            rest = name[len(kw):].lstrip(" -.:|'")
            return rest if rest else name
    m = re.match(r"(?i)^mr\.?\s*gulaman\s*", name)
    if m:
        rest = name[m.end():].strip(" -")
        return rest or name
    m = re.match(r"(?i)^jack\s*n['`]?\s*jill\s*", name)
    if m:
        rest = name[m.end():].strip(" -")
        return rest or name
    m = re.match(r"(?i)^royal\s+", name)
    if m:
        rest = name[m.end():].strip(" -")
        return rest or name
    m = re.match(r"(?i)^baby\s+bench\s*", name)
    if m and brand == "Bench":
        rest = name[m.end():].strip(" -")
        return ("Baby Bench " + rest).strip() if rest else name
    return name


def clean_display_name(full: str, keywords: list, brand: str) -> str:
    if brand == "Aqsa":
        if full.lower().startswith("royal"):
            return "Aqsa " + full[5:].lstrip(" -")
        return full
    without_size = strip_sizes(full)
    product = strip_brand_prefix(without_size, keywords, brand)
    product = MULTI_SPACE.sub(" ", product).strip(" -")
    return product or without_size or full


def pick_better(a: dict, b: dict) -> dict:
    if b["stock"] != a["stock"]:
        return b if b["stock"] > a["stock"] else a
    if b["price"] != a["price"]:
        return b if b["price"] > a["price"] else a
    return b if len(b["fullName"]) >= len(a["fullName"]) else a


def build_data() -> dict:
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    grouped = {b[0]: {} for b in SITE_BRANDS}
    raw_counts = defaultdict(int)
    unmatched = []

    for r in rows:
        vals = list(r) + [None] * 7
        code, name, unit, sell, cost, gp, stock = vals[:7]
        if not name or not str(name).strip():
            continue
        name = normalize_name(name)
        hit = match_brand(name)
        if not hit:
            unmatched.append(name)
            continue
        brand, kws, logo = hit
        raw_counts[brand] += 1
        try:
            stock_n = int(stock or 0)
        except (TypeError, ValueError):
            stock_n = 0
        try:
            price = float(sell or 0)
        except (TypeError, ValueError):
            price = 0.0

        display = clean_display_name(name, kws, brand)
        if brand == "Aqsa":
            key = name.lower()
        else:
            key = strip_brand_prefix(strip_sizes(name), kws, brand).lower()
            key = MULTI_SPACE.sub(" ", key).strip()

        entry = {
            "code": str(code) if code else "",
            "name": display,
            "fullName": name,
            "unit": str(unit or "PCS"),
            "price": price,
            "stock": stock_n,
        }
        prev = grouped[brand].get(key)
        grouped[brand][key] = entry if prev is None else pick_better(prev, entry)

    brands_out = []
    for display, kws, logo in SITE_BRANDS:
        items = list(grouped[display].values())
        items.sort(key=lambda x: x["name"].lower())
        bid = slugify(display)
        brands_out.append({
            "id": bid,
            "name": display if display != "Nestle" else "Nestlé",
            "logo": f"assets/images/brands/{logo}",
            "page": f"brands/{bid}.html",
            "rawCount": raw_counts[display],
            "productCount": len(items),
            "products": [{
                "code": it["code"],
                "name": it["name"],
                "fullName": it["fullName"],
                "unit": it["unit"],
                "price": it["price"],
            } for it in items],
        })

    return {
        "brands": brands_out,
        "meta": {
            "source": XLSX.name,
            "totalRows": len(rows),
            "unmatchedCount": len(unmatched),
            "unmatchedSample": unmatched[:40],
        },
    }


PAGE_CSS = """
.brand-page{padding-top:calc(var(--nav-h,72px) + 32px);padding-bottom:64px}
.brand-page-hero{display:flex;flex-wrap:wrap;align-items:center;gap:24px 32px;margin-bottom:36px;padding:28px 32px;border-radius:20px;background:var(--surface,#fff);border:1px solid var(--border,rgba(0,0,0,.06));box-shadow:0 8px 28px rgba(10,32,20,.06)}
.brand-page-logo-wrap{width:140px;height:88px;display:flex;align-items:center;justify-content:center;border-radius:14px;background:#f4f7f5;border:1px solid rgba(0,0,0,.04);padding:12px;flex-shrink:0}
.brand-page-logo-wrap img{max-width:100%;max-height:64px;object-fit:contain}
.brand-page-hero-text{flex:1;min-width:200px}
.brand-page-kicker{display:inline-block;font-size:.75rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--green-primary,#1f7a4d);margin-bottom:8px}
.brand-page-title{margin:0 0 8px;font-size:clamp(1.6rem,3vw,2.2rem);font-weight:800;color:var(--text,#0a2014);line-height:1.15}
.brand-page-sub{margin:0;color:var(--text-muted,#5a7264);font-size:1rem;max-width:520px}
.brand-page-count{margin-top:12px;display:inline-flex;align-items:center;gap:8px;font-size:.9rem;font-weight:600;color:var(--green-primary,#1f7a4d);background:rgba(31,122,77,.08);padding:6px 12px;border-radius:999px}
.brand-back{display:inline-flex;align-items:center;gap:8px;margin-bottom:20px;font-size:.92rem;font-weight:600;color:var(--green-primary,#1f7a4d);text-decoration:none}
.brand-back:hover{text-decoration:underline}
.product-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
@media(max-width:900px){.product-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:520px){.product-grid{grid-template-columns:1fr}.brand-page-hero{padding:20px}}
.product-card{background:var(--surface,#fff);border:1px solid var(--border,rgba(0,0,0,.06));border-radius:16px;padding:18px 18px 16px;box-shadow:0 4px 14px rgba(10,32,20,.04);transition:transform .25s ease,box-shadow .25s ease,border-color .25s ease;min-width:0}
.product-card:hover{transform:translateY(-3px);box-shadow:0 12px 28px rgba(10,32,20,.1);border-color:rgba(31,122,77,.22)}
.product-card-name{margin:0 0 8px;font-size:1rem;font-weight:650;line-height:1.35;color:var(--text,#0a2014);word-break:break-word}
.product-card-meta{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;font-size:.82rem;color:var(--text-muted,#5a7264)}
.product-card-code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.78rem;opacity:.85}
.product-card-unit{padding:2px 8px;border-radius:999px;background:rgba(31,122,77,.08);color:var(--green-primary,#1f7a4d);font-weight:600;font-size:.75rem}
.product-empty{grid-column:1/-1;text-align:center;padding:48px 20px;color:var(--text-muted,#5a7264);border:1px dashed var(--border,#ccc);border-radius:16px}
[data-theme="dark"] .brand-page-hero,html.dark .brand-page-hero,body.dark .brand-page-hero,
[data-theme="dark"] .product-card,html.dark .product-card,body.dark .product-card{background:var(--bg-card,#0f2419);border-color:rgba(255,255,255,.06)}
[data-theme="dark"] .brand-page-logo-wrap,html.dark .brand-page-logo-wrap,body.dark .brand-page-logo-wrap{background:rgba(255,255,255,.04);border-color:rgba(255,255,255,.06)}
[data-theme="dark"] .brand-page-title,html.dark .brand-page-title,body.dark .brand-page-title,
[data-theme="dark"] .product-card-name,html.dark .product-card-name,body.dark .product-card-name{color:var(--text,#e8f0ea)}
a.brand-card-link{text-decoration:none;color:inherit;display:flex;flex-direction:column;align-items:center;height:100%}
a.brand-card-link:focus-visible{outline:2px solid var(--green-primary,#1f7a4d);outline-offset:3px;border-radius:16px}
"""


def render_brand_page(brand: dict) -> str:
    esc = html_lib.escape
    products_html = []
    if not brand["products"]:
        products_html.append(
            '<div class="product-empty">Product range listing coming soon. Contact us for the full assortment.</div>'
        )
    else:
        for p in brand["products"]:
            code = esc(p.get("code") or "")
            name = esc(p.get("name") or p.get("fullName") or "")
            unit = esc(p.get("unit") or "PCS")
            code_html = f'<span class="product-card-code">SKU {code}</span>' if code else ""
            products_html.append(
                f'<article class="product-card reveal-up"><h3 class="product-card-name">{name}</h3>'
                f'<div class="product-card-meta"><span class="product-card-unit">{unit}</span>{code_html}</div></article>'
            )

    title = esc(brand["name"])
    count = brand["productCount"]
    logo = esc("../" + brand["logo"])
    bid = esc(brand["id"])
    count_label = f"{count} product" + ("s" if count != 1 else "")
    body_products = "\n        ".join(products_html)

    return f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} Products | R i D A — FMCG Distribution UAE</title>
  <meta name="description" content="Browse {title} products distributed by R i D A across the UAE.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://www.ridame.com/brands/{bid}.html">
  <link rel="icon" href="../favicon.ico?v=4" sizes="any">
  <link rel="manifest" href="../site.webmanifest">
  <meta name="theme-color" content="#0A2014">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600&family=Cairo:wght@700&family=Tajawal:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <link rel="stylesheet" href="../css/cinematic.css">
  <style>{PAGE_CSS}</style>
</head>
<body>
  <div class="scroll-progress" id="scrollProgress"></div>
  <nav class="navbar" id="navbar">
    <div class="navbar-inner">
      <a href="../index.html" class="navbar-logo-link">
        <img src="../assets/logos/logo_english.png" data-logo-en="../assets/logos/logo_english.png" data-logo-ar="../assets/logos/logo_2_arabic.png" alt="R i D A Logo" class="navbar-logo">
      </a>
      <div class="navbar-links" id="navLinks">
        <a href="../about.html" data-en="About" data-ar="من نحن">About</a>
        <a href="../index.html#brands" data-en="Brands" data-ar="العلامات التجارية">Brands</a>
        <a href="../index.html#coverage" data-en="Coverage" data-ar="التغطية">Coverage</a>
        <a href="../index.html#contact" data-en="Contact" data-ar="اتصل بنا">Contact</a>
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
      <img src="../assets/logos/logo_english.png" data-logo-en="../assets/logos/logo_english.png" data-logo-ar="../assets/logos/logo_2_arabic.png" alt="R i D A" class="mobile-drawer-logo">
      <button type="button" class="mobile-drawer-close" id="drawerClose" aria-label="Close menu">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <nav class="mobile-drawer-nav" aria-label="Mobile">
      <a href="../about.html" data-en="About" data-ar="من نحن">About</a>
      <a href="../index.html#brands" data-en="Brands" data-ar="العلامات التجارية">Brands</a>
      <a href="../index.html#coverage" data-en="Coverage" data-ar="التغطية">Coverage</a>
      <a href="../index.html#contact" data-en="Contact" data-ar="اتصل بنا">Contact</a>
    </nav>
    <div class="mobile-drawer-foot">
      <a href="../index.html#contact" class="mobile-drawer-cta" data-en="Get in Touch" data-ar="تواصل معنا">Get in Touch</a>
    </div>
  </div>
  <div class="overlay" id="overlay"></div>
  <main class="brand-page">
    <div class="container">
      <a class="brand-back" href="../index.html#brands">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        <span data-en="All Brands" data-ar="كل العلامات">All Brands</span>
      </a>
      <header class="brand-page-hero">
        <div class="brand-page-logo-wrap">
          <img src="{logo}" alt="{title}" width="120" height="60" loading="eager">
        </div>
        <div class="brand-page-hero-text">
          <span class="brand-page-kicker" data-en="Brand Range" data-ar="تشكيلة العلامة">Brand Range</span>
          <h1 class="brand-page-title">{title}</h1>
          <p class="brand-page-sub" data-en="Products distributed by R i D A across the UAE. Similar size variants are grouped into one product." data-ar="منتجات توزعها ريدا في الإمارات. تم تجميع أحجام المنتج المتشابهة.">
            Products distributed by R i D A across the UAE. Similar size variants are grouped into one product.
          </p>
          <div class="brand-page-count">{count_label}</div>
        </div>
      </header>
      <div class="product-grid stagger-cards">
        {body_products}
      </div>
      <div style="margin-top:40px;text-align:center">
        <a href="../index.html#contact" class="btn btn-primary" data-en="Enquire about this brand" data-ar="استفسر عن هذه العلامة">Enquire about this brand</a>
      </div>
    </div>
  </main>
  <footer class="footer" style="margin-top:64px">
    <div class="container">
      <div class="footer-bottom" style="border-top:none;padding-top:0">
        <p class="footer-copyright">&copy; 2026 R i D A —
          <span data-en="Reliable Innovative Distribution Alliance. All rights reserved." data-ar="ريدا — تحالف التوزيع المبتكر الموثوق. جميع الحقوق محفوظة.">Reliable Innovative Distribution Alliance. All rights reserved.</span>
        </p>
      </div>
    </div>
  </footer>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js" defer></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js" defer></script>
  <script src="../js/main.js" defer></script>
  <script src="../js/cinematic.js" defer></script>
</body>
</html>
"""


def write_pages(data: dict) -> None:
    BRANDS_DIR.mkdir(parents=True, exist_ok=True)
    for brand in data["brands"]:
        path = BRANDS_DIR / f"{brand['id']}.html"
        path.write_text(render_brand_page(brand), encoding="utf-8")
        print(f"  page {path.name} ({brand['productCount']} products)")


def main() -> None:
    data = build_data()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Total rows: {data['meta']['totalRows']}")
    print(f"Unmatched: {data['meta']['unmatchedCount']}")
    print("--- per brand (raw -> unique) ---")
    for b in data["brands"]:
        print(f"  {b['name']:16s}  raw={b['rawCount']:4d}  unique={b['productCount']:4d}")
    print("--- writing brand pages ---")
    write_pages(data)
    print("sample products:")
    for b in data["brands"]:
        print(f"  [{b['name']}]")
        for p in b["products"][:5]:
            print(f"    - {p['name']}")


if __name__ == "__main__":
    main()
