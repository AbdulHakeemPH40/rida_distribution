"""Excel → catalog helpers: strip sizes, dedupe variants, match brands."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from django.conf import settings

# Site brands seed (name, keywords, logo relative to static/, slug)
SITE_BRANDS = [
    ("Oishi", ["oishi"], "assets/images/brands/oishi.png", "oishi"),
    ("Nissin", ["nissin"], "assets/images/brands/nissin.png", "nissin"),
    (
        "Jack 'n Jill",
        ["jack n jill", "jack 'n jill", "jack n' jill", "jack n` jill", "jacknjill"],
        "assets/images/brands/jack n jill.png",
        "jack-n-jill",
    ),
    (
        "Mr. Gulaman",
        ["mr. gulaman", "mr gulaman", "mr.gulaman", "gulaman"],
        "assets/images/brands/mr gulman.png",
        "mr-gulaman",
    ),
    ("Bench", ["bench", "baby bench"], "assets/images/brands/bench.png", "bench"),
    ("Nestlé", ["nestle", "nestlé", "nescafé", "nescafe"], "assets/images/brands/nestle.png", "nestle"),
    ("Del Monte", ["del monte", "delmonte"], "assets/images/brands/Delmonte.png", "del-monte"),
    ("Purefoods", ["purefoods", "pure foods", "purefood"], "assets/images/brands/pure food.png", "purefoods"),
    ("Lucky Me!", ["lucky me!", "lucky me", "luckyme"], "assets/images/brands/luckyme.png", "lucky-me"),
    (
        "Century Tuna",
        ["century tuna", "century"],
        "assets/images/brands/century tuna.png",
        "century-tuna",
    ),
    ("UFC", ["ufc"], "assets/images/brands/ufc.png", "ufc"),
    ("Regent", ["regent"], "assets/images/brands/regent.png", "regent"),
    ("Knorr", ["knorr"], "assets/images/brands/knorr.png", "knorr"),
    ("Ajinomoto", ["ajinomoto", "ajinmoto"], "assets/images/brands/Ajinmoto.png", "ajinomoto"),
    ("Zonrox", ["zonrox"], "assets/images/brands/Zonrox.png", "zonrox"),
    # Aqsa placeholder (ex-Royal) — logo can be swapped later
    ("Aqsa", ["aqsa", "royal"], "assets/images/brands/aqsa.png", "aqsa"),
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


def match_brand_seed(name: str):
    lower = name.lower()
    best = None
    best_len = 0
    for display, kws, logo, slug in SITE_BRANDS:
        for kw in kws:
            if lower.startswith(kw) or re.search(
                r"(?i)(?:^|[\s\-])" + re.escape(kw) + r"(?:$|[\s\-])", name
            ):
                if len(kw) > best_len:
                    best = (display, kws, logo, slug)
                    best_len = len(kw)
    if best is None and re.match(r"(?i)^jack\s*n", name):
        for display, kws, logo, slug in SITE_BRANDS:
            if display.startswith("Jack"):
                return display, kws, logo, slug
    if best is None and re.match(r"(?i)^mr\.?\s*gulaman", name):
        for display, kws, logo, slug in SITE_BRANDS:
            if "Gulaman" in display:
                return display, kws, logo, slug
    return best


def strip_brand_prefix(name: str, keywords: list, brand: str) -> str:
    lower = name.lower()
    for kw in sorted(keywords, key=len, reverse=True):
        if lower.startswith(kw):
            rest = name[len(kw) :].lstrip(" -.:|'")
            return rest if rest else name
    m = re.match(r"(?i)^mr\.?\s*gulaman\s*", name)
    if m:
        rest = name[m.end() :].strip(" -")
        return rest or name
    m = re.match(r"(?i)^jack\s*n['`]?\s*jill\s*", name)
    if m:
        rest = name[m.end() :].strip(" -")
        return rest or name
    m = re.match(r"(?i)^royal\s+", name)
    if m:
        rest = name[m.end() :].strip(" -")
        return rest or name
    m = re.match(r"(?i)^baby\s+bench\s*", name)
    if m and brand == "Bench":
        rest = name[m.end() :].strip(" -")
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


def guess_category_name(display_name: str, brand: str) -> str:
    """Lightweight category from leading words of the product title."""
    n = display_name.strip()
    if not n:
        return "General"
    # Take first 1–2 significant tokens
    parts = re.split(r"\s+", n)
    stop = {"and", "with", "in", "the", "of", "for", "&"}
    tokens = [p for p in parts if p.lower() not in stop]
    if not tokens:
        return "General"
    if len(tokens) == 1:
        return tokens[0].title()
    # Prefer first two words for series names (Crispy Fry, Umami Seasoning)
    return f"{tokens[0]} {tokens[1]}".title()


def pick_better(a: dict, b: dict) -> dict:
    if b["stock"] != a["stock"]:
        return b if b["stock"] > a["stock"] else a
    if b["price"] != a["price"]:
        return b if b["price"] > a["price"] else a
    return b if len(b["full_name"]) >= len(a["full_name"]) else a


def parse_excel(path: Path | None = None) -> dict:
    """Return {brands: [{name,slug,logo,keywords,products:[{...}]}]} from Excel."""
    import openpyxl

    xlsx = Path(path or getattr(settings, "CATALOG_XLSX", settings.BASE_DIR / "R i D A .xlsx"))
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))

    grouped: dict[str, dict] = {b[0]: {} for b in SITE_BRANDS}
    meta = {b[0]: {"kws": b[1], "logo": b[2], "slug": b[3]} for b in SITE_BRANDS}
    raw_counts: dict[str, int] = defaultdict(int)
    unmatched: list[str] = []

    for r in rows:
        vals = list(r) + [None] * 7
        code, name, unit, sell, cost, gp, stock = vals[:7]
        if not name or not str(name).strip():
            continue
        name = normalize_name(name)
        hit = match_brand_seed(name)
        if not hit:
            unmatched.append(name)
            continue
        brand, kws, logo, slug = hit
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
            "sku": str(code) if code else "",
            "name": display,
            "full_name": name,
            "unit": str(unit or "PCS"),
            "price": price,
            "stock": stock_n,
            "dedupe_key": key,
            "category": guess_category_name(display, brand),
        }
        prev = grouped[brand].get(key)
        grouped[brand][key] = entry if prev is None else pick_better(prev, entry)

    brands_out = []
    for display, kws, logo, slug in SITE_BRANDS:
        items = list(grouped[display].values())
        items.sort(key=lambda x: x["name"].lower())
        brands_out.append(
            {
                "name": display,
                "slug": slug,
                "logo": logo,
                "keywords": ",".join(kws),
                "raw_count": raw_counts[display],
                "products": items,
            }
        )

    return {
        "brands": brands_out,
        "meta": {
            "source": xlsx.name,
            "total_rows": len(rows),
            "unmatched_count": len(unmatched),
            "unmatched_sample": unmatched[:40],
        },
    }


def sync_catalog_from_data(data: dict, *, clear_products: bool = True) -> dict:
    """Upsert Brand/Category/Product from parse_excel() output."""
    from django.utils.text import slugify

    from .models import Brand, Category, Product

    stats = {"brands": 0, "products": 0, "categories": 0}

    if clear_products:
        Product.objects.all().delete()
        Category.objects.all().delete()

    for i, b in enumerate(data["brands"]):
        brand, _ = Brand.objects.update_or_create(
            slug=b["slug"],
            defaults={
                "name": b["name"],
                "logo": b["logo"],
                "match_keywords": b["keywords"],
                "is_active": True,
                "sort_order": i,
            },
        )
        stats["brands"] += 1

        # Categories from product names
        cat_cache: dict[str, Category] = {}
        for p in b["products"]:
            cat_name = p.get("category") or "General"
            cat_slug = slugify(cat_name) or "general"
            if cat_slug not in cat_cache:
                cat, created = Category.objects.get_or_create(
                    brand=brand,
                    slug=cat_slug,
                    defaults={"name": cat_name, "sort_order": len(cat_cache)},
                )
                cat_cache[cat_slug] = cat
                if created:
                    stats["categories"] += 1
            else:
                cat = cat_cache[cat_slug]

            Product.objects.update_or_create(
                brand=brand,
                dedupe_key=p["dedupe_key"] or p["name"].lower(),
                defaults={
                    "category": cat,
                    "name": p["name"],
                    "full_name": p.get("full_name") or p["name"],
                    "sku": p.get("sku") or "",
                    "unit": p.get("unit") or "PCS",
                    "price": p.get("price") or 0,
                    "stock": p.get("stock") or 0,
                    "is_active": True,
                },
            )
            stats["products"] += 1

    return stats
