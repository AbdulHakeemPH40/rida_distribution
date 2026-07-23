from pathlib import Path

p = Path("config/settings.py")
t = p.read_text(encoding="utf-8")
old = 'ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")'
new = 'ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")'
if old in t:
    p.write_text(t.replace(old, new), encoding="utf-8")
    print("ALLOWED_HOSTS updated")
elif "testserver" in t:
    print("already has testserver")
else:
    print("pattern missing")
    for i, line in enumerate(t.splitlines()):
        if "ALLOWED" in line:
            print(i, repr(line))
