"""Headless screenshot check for Agent City.
Usage (from project root):
  python3 -m http.server 8765 --bind 127.0.0.1 &   # serve the folder (only for this check)
  python tools/screenshot.py [prefix]              # needs: pip install playwright (uses /usr/bin/google-chrome)
Shots: overview (public mode, no private.js), plaza close-up with role bubbles, Study Hall panel, Courier panel (local).
Prints console output; any PAGEERROR line means something is broken.
"""
import sys, asyncio, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "screenshots")
PREFIX = sys.argv[1] if len(sys.argv) > 1 else "latest"
BASE = "http://127.0.0.1:8765/index.html"
from playwright.async_api import async_playwright

async def shoot(b, url, steps, logs):
    pg = await b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("console", lambda m: logs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: logs.append(f"PAGEERROR: {e}"))
    await pg.goto(url)
    await pg.wait_for_function("window.__cityReady === true", timeout=120000)
    await pg.wait_for_timeout(3000)
    for js, name in steps:
        if js: await pg.evaluate(js); await pg.wait_for_timeout(3200)
        await pg.screenshot(path=f"{OUT}/{PREFIX}-{name}.png")
    await pg.close()

async def main():
    os.makedirs(OUT, exist_ok=True); logs = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        await shoot(b, BASE + "?public", [(None, "overview-public"),
            ("City.timeMode='day'; City.applyTime(); City.flyTo(new THREE.Vector3(30,26,46), new THREE.Vector3(0,3,0))", "plaza-day"),
            ("City.fly('studyhall'); City.openPanel('building','studyhall')", "studyhall"),
            ("City.closePanel(); City.fly('postoffice'); City.openPanel('building','postoffice')", "postoffice-public")], logs)
        await shoot(b, BASE, [("City.fly('noticeboard'); City.openPanel('building','noticeboard')", "noticeboard-local")], logs)
        await b.close()
    print("\n".join(logs) or "no errors/warnings")

asyncio.run(main())
