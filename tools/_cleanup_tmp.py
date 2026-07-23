from pathlib import Path

root = Path(__file__).resolve().parent
for name in ("_fix_hosts.py", "_check_home.py", "_home_brands_snip.txt", "_verify_django.py", "_cleanup_tmp.py"):
    p = root / name
    if p.exists():
        p.unlink()
        print("removed", p.name)
