#!/usr/bin/env python3
"""Fix template issues after static->Django migration."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

BRAND_LOOP = """
      <div class="brands-grid stagger-cards">
        {% for brand in brands %}
        <a href="{% url 'catalog:brand_detail' brand.slug %}" class="brand-card brand-card-link reveal-up" aria-label="View {{ brand.name }} products">
          <div class="brand-card-logo">
            {% if brand.logo %}
            <img src="{% static brand.logo %}" alt="{{ brand.name }}" loading="lazy" width="120" height="60">
            {% endif %}
          </div>
          <p class="brand-card-name">{{ brand.name }}</p>
        </a>
        {% empty %}
        <p class="brand-empty" data-en="Brand catalog coming soon." data-ar="كتالوج العلامات قريباً.">Brand catalog coming soon.</p>
        {% endfor %}
      </div>
"""


def unescape_django_tags(text: str) -> str:
    """Fix \\' inside {% %} tags produced by bad regex replacements."""
    def fix_tag(m: re.Match) -> str:
        inner = m.group(0)
        return inner.replace("\\'", "'").replace('\\"', '"')

    text = re.sub(r"\{%.*?%\}", fix_tag, text, flags=re.S)
    text = re.sub(r"\{\{.*?\}\}", fix_tag, text, flags=re.S)
    return text


def fix_extends_order(text: str) -> str:
    """Django requires {% extends %} to be the first template tag."""
    if "{% extends" not in text:
        return text
    # Pull extends to top; keep load static after extends
    extends = re.search(r"\{%\s*extends\s+['\"][^'\"]+['\"]\s*%\}", text)
    if not extends:
        return text
    ext = extends.group(0)
    body = text[: extends.start()] + text[extends.end() :]
    body = body.lstrip("\n")
    # remove duplicate load static at very top if present
    loads = list(re.finditer(r"\{%\s*load\s+static\s*%\}\s*", body))
    load_static = "{% load static %}\n"
    for m in reversed(loads):
        body = body[: m.start()] + body[m.end() :]
    return f"{ext}\n{load_static}\n{body.lstrip()}"


def replace_brands_grid(home: str) -> str:
    """Replace hardcoded brand cards with DB loop."""
    # Match from brands-grid open through its closing div before next sibling/section end
    pat = re.compile(
        r'<div class="brands-grid stagger-cards">.*?</div>\s*(?=\s*</div>\s*</section>|\s*</section>)',
        flags=re.I | re.S,
    )
    m = pat.search(home)
    if not m:
        # broader: brands-grid to last brand-card-link then closing divs
        pat2 = re.compile(
            r'<div class="brands-grid[^"]*">[\s\S]*?</div>\s*</div>\s*</section>',
            flags=re.I,
        )
        m2 = pat2.search(home)
        if not m2:
            print("  ERROR: brands-grid not found")
            return home
        # Only replace the grid portion — find grid start to matching close is hard;
        # replace inner from grid open to just before section close container
        start = m2.start()
        # find end of brands-grid: after last </a> following brand-card
        sub = home[start:]
        # find first </div> that closes brands-grid after all cards — count depth
        i = len('<div class="brands-grid stagger-cards">')
        # find actual open tag end
        open_end = sub.find(">") + 1
        depth = 1
        pos = open_end
        while pos < len(sub) and depth:
            next_open = sub.find("<div", pos)
            next_close = sub.find("</div>", pos)
            if next_close < 0:
                break
            if next_open >= 0 and next_open < next_close:
                depth += 1
                pos = next_open + 4
            else:
                depth -= 1
                pos = next_close + len("</div>")
        end = start + pos
        new_home = home[:start] + BRAND_LOOP.strip() + "\n" + home[end:]
        print("  brands-grid replaced (depth walk)")
        return new_home

    new_home = home[: m.start()] + BRAND_LOOP.strip() + "\n" + home[m.end() :]
    print("  brands-grid replaced")
    return new_home


def fix_base_nav_hashes(base: str) -> str:
    """Ensure nav Brands/Coverage/Contact point at home anchors from any page."""
    # Already should be from migrate; fix any leftover #only links in navbar
    # Links like href="#brands" inside navbar should be home#brands
    def fix_nav_block(block: str) -> str:
        block = re.sub(
            r'href="#brands"',
            "href=\"{% url 'core:home' %}#brands\"",
            block,
        )
        block = re.sub(
            r'href="#coverage"',
            "href=\"{% url 'core:home' %}#coverage\"",
            block,
        )
        block = re.sub(
            r'href="#contact"',
            "href=\"{% url 'core:home' %}#contact\"",
            block,
        )
        return block

    # Only fix inside navbar and mobile-drawer and footer, not main content
    for cls in ("navbar", "mobile-drawer", "footer"):
        pat = re.compile(
            rf'(<[^>]+class="[^"]*{cls}[^"]*"[\s\S]*?)(?=<section|<main|\{{% block content|</body>)',
            re.I,
        )
        # simpler approach: whole base is chrome only for nav/footer
    base = fix_nav_block(base)
    return base


def ensure_id_brands(home: str) -> str:
    """Guarantee section id=brands exists for nav deep links."""
    if re.search(r'id=["\']brands["\']', home):
        return home
    # brands-section class → add id
    home2 = re.sub(
        r'(class=["\'][^"\']*brands-section[^"\']*["\'])',
        r'id="brands" \1',
        home,
        count=1,
        flags=re.I,
    )
    if home2 != home:
        print("  added id=brands on brands-section")
        return home2
    # before Top Brands heading section
    home2 = re.sub(
        r'(<section[^>]*class=["\'][^"\']*brand)',
        r'<section id="brands" class="\1',
        home,
        count=1,
        flags=re.I,
    )
    # fix botched if any
    if 'id="brands"' in home2:
        print("  added id=brands")
    return home2


def fix_file(path: Path, is_home: bool = False, is_base: bool = False) -> None:
    text = path.read_text(encoding="utf-8")
    orig = text
    text = unescape_django_tags(text)
    if not is_base:
        text = fix_extends_order(text)
    if is_home:
        text = replace_brands_grid(text)
        text = ensure_id_brands(text)
    if is_base:
        text = fix_base_nav_hashes(text)
        # base must start with load static
        if not text.lstrip().startswith("{% load static %}"):
            text = "{% load static %}\n" + text.lstrip()
    if text != orig:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"  fixed {path.relative_to(ROOT)}")
    else:
        print(f"  no change {path.relative_to(ROOT)}")


def main() -> None:
    fix_file(TEMPLATES / "base.html", is_base=True)
    fix_file(TEMPLATES / "core" / "home.html", is_home=True)
    fix_file(TEMPLATES / "core" / "about.html")
    fix_file(TEMPLATES / "core" / "why_rida.html")
    for p in (TEMPLATES / "catalog").glob("*.html"):
        fix_file(p)

    # Quick sanity
    home = (TEMPLATES / "core" / "home.html").read_text(encoding="utf-8")
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "{% extends" in home
    assert home.strip().startswith("{% extends"), home[:80]
    assert "\\'" not in home or home.count("\\'") == 0
    assert "{% for brand in brands %}" in home
    assert "gsap" in base.lower()
    assert "{% static 'css/style.css' %}" in base or 'static "css/style.css"' in base
    print("SANITY OK")


if __name__ == "__main__":
    main()
