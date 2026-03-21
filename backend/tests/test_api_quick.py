"""快速 API 端到端测试"""
import sys, os
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import requests
from pathlib import Path

NO_PROXY = {"http": None, "https": None}
BASE = "http://127.0.0.1:9500/api/v1/ppt"

r = requests.get("http://127.0.0.1:9500/health", proxies=NO_PROXY)
print(f"Health: {r.status_code} {r.text}")

pptx = Path(r"E:\Code\ai-teaching-ppt\uploads\generated\test_大龙猫.pptx")
print(f"Upload file exists: {pptx.exists()}, size: {pptx.stat().st_size}")

with open(pptx, "rb") as f:
    files = {"file_a": (pptx.name, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    r = requests.post(f"{BASE}/upload", files=files, proxies=NO_PROXY)

print(f"Upload status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    sid = data["session_id"]
    print(f"Session: {sid}")
    previews = data.get("preview_images", [])
    print(f"Preview images: {len(previews)}")

    for k, v in data["parsed"].items():
        fname = v["filename"]
        scount = v["slide_count"]
        print(f"  {k}: {fname} - {scount} slides")
        for s in v["slides"][:3]:
            si = s["slide_index"]
            texts = [e for e in s["elements"] if e.get("plain_text")]
            tables = [e for e in s["elements"] if e.get("table_data")]
            print(f"    Slide {si}: {len(texts)} texts, {len(tables)} tables")
            for t in texts[:2]:
                txt = t["plain_text"][:50].replace("\n", "\\n")
                title = " [TITLE]" if t.get("is_title") else ""
                print(f"      [{t['shape_index']}] {txt}{title}")

    r2 = requests.get(f"{BASE}/versions/{sid}", proxies=NO_PROXY)
    print(f"\nVersions status: {r2.status_code}")
    if r2.status_code == 200:
        vdata = r2.json()
        print(f"  Version count: {len(vdata['versions'])}")

    r3 = requests.get(f"{BASE}/download/{sid}", proxies=NO_PROXY)
    print(f"\nDownload status: {r3.status_code}, size: {len(r3.content)} bytes")
    if r3.status_code == 200:
        out = Path("test_downloaded.pptx")
        out.write_bytes(r3.content)
        print(f"  Saved to: {out}")

    print("\n=== ALL TESTS PASSED ===")
else:
    print(f"Error: {r.text[:500]}")
    sys.exit(1)
