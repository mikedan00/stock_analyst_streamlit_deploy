from pathlib import Path

required = ["app.py", "streamlit_app.py", "requirements.txt"]
for name in required:
    p = Path(name)
    if not p.exists():
        raise SystemExit(f"MISSING: {name}")
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()
    print(f"{name}: {len(lines)} lines")
    if name == "requirements.txt" and len(lines) < 5:
        raise SystemExit("requirements.txt appears collapsed or incomplete")
    if name.endswith(".py") and len(lines) < 50:
        raise SystemExit(f"{name} appears collapsed or incomplete")

if Path("packages.txt").exists():
    raise SystemExit("packages.txt should be deleted for this app")

print("OK: files look normal")
