#!/usr/bin/env python3
"""
Fully migrate the static R i D A site into Django:
  1. Copy css/, js/, assets/, favicon, robots, manifest into static/
  2. Build templates/base.html from index.html head+nav+footer (CDN, SEO, GSAP)
  3. Build home/about/why_rida content templates that extend base
  4. Rewrite asset paths -> {% static %} and internal links -> {% url %}
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
TEMPLATES = ROOT / "templates"


def copy_static_tree() -> None:
    """Move all front-end assets under static/ for Django staticfiles."""
    STATIC.mkdir(exist_ok=True)

    pairs = [
        (ROOT / "css", STATIC / "css"),
        (ROOT / "js", STATIC / "js"),
        (ROOT / "assets", STATIC / "assets"),
    ]
    for src, dst in pairs:
        if not src.exists():
            print(f"  skip missing {src}")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"  copied {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    for name in ("favicon.ico", "robots.txt", "site.webmanifest", "sitemap.xml"):
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, STATIC / name)
            print(f"  copied {name}")

    # logos also live under assets/logos — ensure favicons at static root aliases
    logos = STATIC / "assets" / "logos"
    if logos.exists():
        for fav in ("favicon.ico", "favicon-32x32.png", "favicon-16x16.png", "apple-touch-icon.png"):
            src = logos / fav
            if src.exists() and fav == "favicon.ico":
                shutil.copy2(src, STATIC / "favicon.ico")


def rewrite_static_paths(html: str) -> str:
    """Convert relative asset paths to Django {% static %} tags."""

    def static_tag(path: str) -> str:
        path = path.lstrip("./").split("?")[0]
        return "{% static '" + path + "' %}"

    # href / src / content attributes pointing at local assets
    patterns = [
        # href="css/..." src="js/..." src="assets/..." href="assets/..." href="favicon..."
        (
            r'(?P<attr>href|src|data-logo-en|data-logo-ar|content)=([\'"])(?P<path>(?:\.?/)?(?:css|js|assets|favicon\.ico|robots\.txt|site\.webmanifest|sitemap\.xml)[^\'"]*)\2',
            lambda m: f"{m.group('attr')}=\"{static_tag(m.group('path'))}\"",
        ),
        # url(assets/...) or url(css/...) inside inline style
        (
            r'url\(([\'"]?)(?P<path>(?:\.?/)?(?:css|js|assets)/[^\'"\)]+)\1\)',
            lambda m: "url('" + static_tag(m.group("path")) + "')",
        ),
        # preload as=image href=
        (
            r'(rel=["\']preload["\'][^>]*href=)([\'"])(?P<path>(?:\.?/)?(?:css|js|assets)/[^\'"]+)\2',
            lambda m: m.group(1) + '"' + static_tag(m.group("path")) + '"',
        ),
    ]

    out = html
    for pat, repl in patterns:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)

    # Fix double-wrapped static if any
    out = out.replace("{% static '{% static '", "{% static '")
    out = out.replace("' %} %}'", "' %}")

    return out


def rewrite_urls(html: str) -> str:
    """Map legacy .html links to Django URL names."""
    replacements = [
        (r'href=(["\'])index\.html\1', r'href="{% url \'core:home\' %}"'),
        (r'href=(["\'])about\.html\1', r'href="{% url \'core:about\' %}"'),
        (r'href=(["\'])why-rida\.html\1', r'href="{% url \'core:why_rida\' %}"'),
        (r'href=(["\'])/\1', r'href="{% url \'core:home\' %}"'),
        # brand pages: brands/foo.html -> catalog brand_detail
        (
            r'href=(["\'])brands/([a-z0-9-]+)\.html\1',
            r'href="{% url \'catalog:brand_detail\' slug=\'\2\' %}"',
        ),
        # hash-only section links that used index.html#x
        (r'href=(["\'])index\.html(#[^\'"]+)\1', r'href="{% url \'core:home\' %}\2"'),
        # bare #brands etc stay as-is for home; on other pages prefix home
    ]
    out = html
    for pat, repl in replacements:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)

    # Logo home links that are href="" or href="#" on logo — leave
    # Common pattern: href="index.html#contact"
    out = re.sub(
        r'href=(["\'])(?:\.?/)?index\.html(#[a-z0-9-]+)\1',
        r'href="{% url \'core:home\' %}\2"',
        out,
        flags=re.IGNORECASE,
    )
    return out


def extract_between(html: str, start_pat: str, end_pat: str) -> tuple[str, int, int]:
    sm = re.search(start_pat, html, flags=re.I | re.S)
    if not sm:
        raise ValueError(f"start not found: {start_pat[:60]}")
    em = re.search(end_pat, html[sm.end() :], flags=re.I | re.S)
    if not em:
        raise ValueError(f"end not found after {start_pat[:40]}")
    start = sm.start()
    end = sm.end() + em.end()
    return html[start:end], start, end


def split_index(html: str) -> dict[str, str]:
    """Split index.html into head_inner, nav_block, main_content, footer, scripts."""
    # <head>...</head>
    head_m = re.search(r"<head[^>]*>(.*?)</head>", html, flags=re.I | re.S)
    if not head_m:
        raise ValueError("no head")
    head_inner = head_m.group(1)

    body_m = re.search(r"<body[^>]*>(.*?)</body>", html, flags=re.I | re.S)
    if not body_m:
        raise ValueError("no body")
    body = body_m.group(1)

    # Footer
    foot_m = re.search(r"(<footer\b.*?</footer>)", body, flags=re.I | re.S)
    footer = foot_m.group(1) if foot_m else ""

    # Scripts after footer (or at end of body)
    after_footer = body[foot_m.end() :] if foot_m else ""
    scripts = re.findall(r"<script\b[^>]*>.*?</script>", after_footer, flags=re.I | re.S)
    # also scripts that are only tags with src
    script_block = "\n".join(scripts)

    # Everything before footer is chrome + content
    before = body[: foot_m.start()] if foot_m else body

    # Nav + drawer + overlay: from scroll-progress or nav through overlay
    # Content starts at first <section or <main after overlay
    nav_end = 0
    overlay_m = re.search(r'<div class="overlay"[^>]*>\s*</div>', before, flags=re.I | re.S)
    if overlay_m:
        nav_end = overlay_m.end()
    else:
        # fallback: after mobile-drawer
        dm = re.search(r'<div class="mobile-drawer".*?</div>\s*<div class="overlay".*?</div>', before, flags=re.I | re.S)
        if dm:
            nav_end = dm.end()
        else:
            nm = re.search(r"</nav>", before, flags=re.I)
            nav_end = nm.end() if nm else 0

    # Include scroll-progress if present before nav
    chrome_start = 0
    sp = re.search(r'<div class="scroll-progress"', before, flags=re.I)
    if sp:
        chrome_start = sp.start()

    chrome = before[chrome_start:nav_end].strip()
    main_content = before[nav_end:].strip()
    # strip trailing scripts accidentally left in main
    main_content = re.sub(r"<script\b[^>]*>.*?</script>\s*$", "", main_content, flags=re.I | re.S).strip()

    return {
        "head_inner": head_inner,
        "chrome": chrome,
        "main": main_content,
        "footer": footer,
        "scripts": script_block,
    }


def build_base_head(head_inner: str) -> str:
    """Turn original head into base.html head with blocks."""
    h = head_inner

    # Remove existing title — use block
    h = re.sub(r"<title>.*?</title>", "", h, flags=re.I | re.S)

    # description meta -> block
    h = re.sub(
        r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>',
        '<meta name="description" content="{% block meta_description %}R i D A — Reliable Innovative Distribution Alliance. UAE trusted FMCG import and distribution company delivering global brands to local shelves across all Emirates.{% endblock %}">',
        h,
        count=1,
        flags=re.I,
    )

    # canonical
    h = re.sub(
        r'<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']*["\']\s*/?>',
        '<link rel="canonical" href="{% block canonical %}{{ SITE_DOMAIN }}{{ request.path }}{% endblock %}">',
        h,
        count=1,
        flags=re.I,
    )

    # stylesheet links already rewritten to static; ensure catalog.css appended
    if "catalog.css" not in h:
        h = h.replace(
            "{% static 'css/cinematic.css' %}\">",
            "{% static 'css/cinematic.css' %}\">\n  <link rel=\"stylesheet\" href=\"{% static 'css/catalog.css' %}\">",
        )
        if "catalog.css" not in h:
            h += '\n  <link rel="stylesheet" href="{% static \'css/catalog.css\' %}">\n'

    # og:url dynamic
    h = re.sub(
        r'<meta\s+property=["\']og:url["\']\s+content=["\'][^"\']*["\']\s*/?>',
        '<meta property="og:url" content="{{ SITE_DOMAIN }}{{ request.path }}">',
        h,
        flags=re.I,
    )

    # Insert title + blocks after charset viewport area
    title_block = """
  <title>{% block title %}{{ SITE_NAME }} | {{ SITE_TAGLINE }} — FMCG Import & Distribution UAE{% endblock %}</title>
"""
    # after viewport
    h = re.sub(
        r'(<meta\s+name=["\']viewport["\'][^>]*>)',
        r"\1\n" + title_block,
        h,
        count=1,
        flags=re.I,
    )

    h += "\n  {% block extra_head %}{% endblock %}\n"
    return h.strip()


def djangoify_chrome(chrome: str) -> str:
    """Nav links to Django urls."""
    c = chrome
    # logo href
    c = re.sub(
        r'(navbar-logo-link["\'][^>]*href=)(["\'])[^"\']*\2',
        r'\1"{% url \'core:home\' %}"',
        c,
        flags=re.I,
    )
    c = re.sub(r'href=(["\'])(?:index\.html)?#about\1', 'href="{% url \'core:about\' %}"', c, flags=re.I)
    c = re.sub(r'href=(["\'])about\.html\1', 'href="{% url \'core:about\' %}"', c, flags=re.I)

    # Map nav items by data-en or text is fragile; do common href patterns
    replacements = {
        r'href=(["\'])(?:index\.html)?#brands\1': 'href="{% url \'core:home\' %}#brands"',
        r'href=(["\'])(?:index\.html)?#coverage\1': 'href="{% url \'core:home\' %}#coverage"',
        r'href=(["\'])(?:index\.html)?#contact\1': 'href="{% url \'core:home\' %}#contact"',
        r'href=(["\'])(?:index\.html)?#services\1': 'href="{% url \'core:home\' %}#brands"',
        r'href=(["\'])(?:index\.html)?#portfolio\1': 'href="{% url \'core:home\' %}#brands"',
        r'href=(["\'])why-rida\.html\1': 'href="{% url \'core:why_rida\' %}"',
    }
    for pat, repl in replacements.items():
        c = re.sub(pat, repl, c, flags=re.I)

    # About link that pointed to #about on home or about page
    c = re.sub(
        r'(<a[^>]*data-en=["\']About["\'][^>]*href=)(["\'])[^"\']*\2',
        r'\1"{% url \'core:about\' %}"',
        c,
        flags=re.I,
    )
    c = re.sub(
        r'(href=)(["\'])[^"\']*\2([^>]*data-en=["\']About["\'])',
        r'\1"{% url \'core:about\' %}"\3',
        c,
        flags=re.I,
    )
    return c


def djangoify_footer(footer: str) -> str:
    f = footer
    f = rewrite_urls(f)
    f = re.sub(r'href=(["\'])(?:index\.html)?#brands\1', 'href="{% url \'core:home\' %}#brands"', f, flags=re.I)
    f = re.sub(r'href=(["\'])(?:index\.html)?#contact\1', 'href="{% url \'core:home\' %}#contact"', f, flags=re.I)
    f = re.sub(r'href=(["\'])about\.html\1', 'href="{% url \'core:about\' %}"', f, flags=re.I)
    # contact tel/mailto already fine; WhatsApp can use context vars if hardcoded numbers
    f = f.replace("+971568860016", "{{ SITE_PHONE }}")
    f = f.replace("+971 56 886 0016", "{{ SITE_PHONE_DISPLAY }}")
    f = f.replace("sales@ridame.com", "{{ SITE_EMAIL }}")
    f = f.replace("phone=971568860016", "phone={{ SITE_WHATSAPP }}")
    return f


def djangoify_scripts(scripts: str) -> str:
    s = rewrite_static_paths(scripts)
    # Ensure defer on local scripts
    return s


def build_base(parts: dict[str, str]) -> str:
    head = build_base_head(rewrite_static_paths(parts["head_inner"]))
    chrome = djangoify_chrome(rewrite_static_paths(parts["chrome"]))
    footer = djangoify_footer(rewrite_static_paths(parts["footer"]))
    scripts = djangoify_scripts(parts["scripts"])

    # Drop JSON-LD from base if we want page-specific — keep in base for org SEO (from home)
    # Keep it — good for all pages

    base = f"""{{% load static %}}
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
{head}
</head>
<body class="{{% block body_class %}}{{% endblock %}}">
{chrome}

  {{% block content %}}{{% endblock %}}

{footer}

{scripts}
  {{% block extra_js %}}{{% endblock %}}
</body>
</html>
"""
    return base


def brand_card_loop_replace(main: str) -> str:
    """Replace static brand grid cards with Django loop if brand-grid found."""
    # Try to find the brands grid container and replace inner cards
    # Common: <div class="brand-grid"> ... many articles/cards ... </div>
    patterns = [
        r'(<div class="brand-grid"[^>]*>)(.*?)(</div>\s*(?=</div>\s*</section>|</section>))',
        r'(<div class="brands-grid"[^>]*>)(.*?)(</div>\s*(?=</div>\s*</section>|</section>))',
        r'(<div class="brand-cards"[^>]*>)(.*?)(</div>\s*(?=</div>\s*</section>|</section>))',
    ]
    loop = r"""\1
        {% for brand in brands %}
        <a class="brand-card" href="{% url 'catalog:brand_detail' brand.slug %}">
          {% if brand.logo %}
          <div class="brand-card-logo">
            <img src="{% static brand.logo %}" alt="{{ brand.name }}" loading="lazy" width="160" height="80">
          </div>
          {% endif %}
          <h3 class="brand-card-name">{{ brand.name }}</h3>
          {% if brand.tagline %}<p class="brand-card-tagline">{{ brand.tagline }}</p>{% endif %}
        </a>
        {% empty %}
        <p class="brand-empty">Brand catalog coming soon.</p>
        {% endfor %}
        \3"""

    out = main
    replaced = False
    for pat in patterns:
        if re.search(pat, out, flags=re.I | re.S):
            out = re.sub(pat, loop, out, count=1, flags=re.I | re.S)
            replaced = True
            print("  brand grid replaced with {% for brand in brands %}")
            break

    if not replaced:
        # Replace individual brands/*.html links
        out = re.sub(
            r'href=(["\'])brands/([a-z0-9-]+)\.html\1',
            r'href="{% url \'catalog:brand_detail\' slug=\'\2\' %}"',
            out,
            flags=re.I,
        )
        print("  brand grid pattern not found — only rewrote brands/*.html links")

    return out


def djangoify_main(main: str) -> str:
    m = rewrite_static_paths(main)
    m = rewrite_urls(m)
    m = brand_card_loop_replace(m)
    # section anchors used in nav
    m = re.sub(
        r'href=(["\'])(?:index\.html)?#(brands|coverage|contact|about|vision|clients)\1',
        r'href="#\2"',
        m,
        flags=re.I,
    )
    return m


def strip_page_chrome(html: str) -> str:
    """For about/why-rida: keep only main content between nav chrome and footer."""
    parts_try = html
    body_m = re.search(r"<body[^>]*>(.*?)</body>", parts_try, flags=re.I | re.S)
    body = body_m.group(1) if body_m else parts_try

    foot_m = re.search(r"<footer\b", body, flags=re.I)
    if foot_m:
        body = body[: foot_m.start()]

    # remove nav/drawer/overlay/scroll-progress
    body = re.sub(r'<div class="scroll-progress"[^>]*>.*?</div>', "", body, count=1, flags=re.I | re.S)
    body = re.sub(r"<nav\b[^>]*>.*?</nav>", "", body, count=1, flags=re.I | re.S)
    body = re.sub(r'<div class="mobile-drawer"[^>]*>.*?</div>\s*<div class="overlay"[^>]*>\s*</div>', "", body, count=1, flags=re.I | re.S)
    body = re.sub(r'<div class="overlay"[^>]*>\s*</div>', "", body, flags=re.I | re.S)
    # scripts
    body = re.sub(r"<script\b[^>]*>.*?</script>", "", body, flags=re.I | re.S)
    return body.strip()


def wrap_extends(content: str, title: str | None = None, extra_head: str = "", body_class: str = "") -> str:
    blocks = ["{% load static %}", "{% extends 'base.html' %}", ""]
    if title:
        blocks.append(f"{{% block title %}}{title}{{% endblock %}}")
        blocks.append("")
    if body_class:
        blocks.append(f"{{% block body_class %}}{body_class}{{% endblock %}}")
        blocks.append("")
    if extra_head:
        blocks.append("{% block extra_head %}")
        blocks.append(extra_head)
        blocks.append("{% endblock %}")
        blocks.append("")
    blocks.append("{% block content %}")
    blocks.append(content)
    blocks.append("{% endblock %}")
    blocks.append("")
    return "\n".join(blocks)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  wrote {path.relative_to(ROOT)} ({len(text):,} bytes)")


def update_settings() -> None:
    settings = ROOT / "config" / "settings.py"
    text = settings.read_text(encoding="utf-8")
    new_static = '''# Static files — everything lives under static/
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
'''
    text2 = re.sub(
        r"# Static:.*?(?=\nMEDIA_URL)",
        new_static + "\n",
        text,
        count=1,
        flags=re.S,
    )
    if text2 == text:
        # try alternate
        text2 = re.sub(
            r"STATIC_URL = .*?(?=\nMEDIA_URL)",
            new_static,
            text,
            count=1,
            flags=re.S,
        )
    settings.write_text(text2, encoding="utf-8", newline="\n")
    print("  updated config/settings.py STATICFILES_DIRS")


def archive_legacy_html() -> None:
    """Move root static HTML out of the way into _legacy_static/."""
    dest = ROOT / "_legacy_static"
    dest.mkdir(exist_ok=True)
    for name in ("index.html", "about.html", "why-rida.html"):
        src = ROOT / name
        if src.exists():
            target = dest / name
            shutil.move(str(src), str(target))
            print(f"  archived {name} -> _legacy_static/{name}")
    brands = ROOT / "brands"
    if brands.exists() and brands.is_dir():
        target = dest / "brands"
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(brands), str(target))
        print("  archived brands/ -> _legacy_static/brands/")


def main() -> None:
    print("== 1. Copy assets into static/ ==")
    copy_static_tree()

    print("== 2. Parse index.html ==")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    parts = split_index(index)
    print(f"  head {len(parts['head_inner']):,} chrome {len(parts['chrome']):,} main {len(parts['main']):,} footer {len(parts['footer']):,}")

    print("== 3. Write base.html ==")
    base = build_base(parts)
    write(TEMPLATES / "base.html", base)

    print("== 4. Write home.html ==")
    home_main = djangoify_main(parts["main"])
    home = wrap_extends(
        home_main,
        title="{{ SITE_NAME }} | {{ SITE_TAGLINE }} — FMCG Import & Distribution UAE",
        body_class="page-home",
        extra_head='  <link rel="preload" as="image" href="{% static \'assets/images/stock/hero.jpg\' %}" fetchpriority="high">',
    )
    write(TEMPLATES / "core" / "home.html", home)

    print("== 5. Write about.html ==")
    about_src = ROOT / "about.html"
    if about_src.exists():
        about_raw = about_src.read_text(encoding="utf-8")
        about_main = djangoify_main(strip_page_chrome(about_raw))
        about = wrap_extends(
            about_main,
            title="About | {{ SITE_NAME }} — {{ SITE_TAGLINE }}",
            body_class="page-about",
        )
        write(TEMPLATES / "core" / "about.html", about)

    print("== 6. Write why_rida.html ==")
    why_src = ROOT / "why-rida.html"
    if why_src.exists():
        why_raw = why_src.read_text(encoding="utf-8")
        why_main = djangoify_main(strip_page_chrome(why_raw))
        why = wrap_extends(
            why_main,
            title="Why R i D A | {{ SITE_NAME }}",
            body_class="page-why",
        )
        write(TEMPLATES / "core" / "why_rida.html", why)

    print("== 7. Ensure brand templates still extend base ==")
    brand_detail = TEMPLATES / "catalog" / "brand_detail.html"
    if brand_detail.exists():
        bd = brand_detail.read_text(encoding="utf-8")
        if "{% extends" not in bd:
            print("  WARNING: brand_detail does not extend base — leaving as-is")
        else:
            # fix static paths if any raw assets/
            bd2 = rewrite_static_paths(bd)
            if bd2 != bd:
                write(brand_detail, bd2)
            else:
                print("  brand_detail.html OK")

    print("== 8. Settings STATICFILES_DIRS ==")
    update_settings()

    print("== 9. Archive legacy root HTML ==")
    archive_legacy_html()

    print("DONE.")


if __name__ == "__main__":
    main()
