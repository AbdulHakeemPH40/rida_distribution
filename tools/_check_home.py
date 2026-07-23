from pathlib import Path

h = Path("templates/core/home.html").read_text(encoding="utf-8")
print("for brand count", h.count("for brand"))
print("brands/oishi static", h.count("brands/oishi"))
print("catalog:brand_detail", h.count("catalog:brand_detail"))
# find brands-grid
idx = h.find("brands-grid")
print("brands-grid idx", idx)
if idx >= 0:
    chunk = h[idx : idx + 900]
    Path("tools/_home_brands_snip.txt").write_text(chunk, encoding="utf-8")
    print("wrote snip")
