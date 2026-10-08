"""Headless screenshot check for Agent City.
Usage (from project root):
  python3 -m http.server 8765 --bind 127.0.0.1 &   # serve the folder (only for this check)
  python tools/screenshot.py [prefix]              # needs: pip install playwright (uses /usr/bin/google-chrome)
Prints console output; any PAGEERROR line means something is broken.
"""
import sys, asyncio, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "screenshots")
PREFIX = sys.argv[1] if len(sys.argv) > 1 else "latest"
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"])
        pg = await b.new_page(viewport={"width":1440,"height":900})
        logs=[]
        pg.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
        pg.on("pageerror", lambda e: logs.append(f"PAGEERROR: {e}"))
        await pg.goto("http://127.0.0.1:8765/index.html")
        await pg.wait_for_function("window.__cityReady === true", timeout=90000)
        await pg.wait_for_timeout(4000)
        await pg.screenshot(path=f"{OUT}/{PREFIX}-overview.png")
        await pg.evaluate("window.__city.fly('library')"); await pg.wait_for_timeout(3500)
        await pg.evaluate("window.__city.openPanel('library')"); await pg.wait_for_timeout(800)
        await pg.screenshot(path=f"{OUT}/{PREFIX}-library.png")
        await pg.evaluate("document.getElementById('panelClose').click(); window.__city.fly('market')"); await pg.wait_for_timeout(3500)
        await pg.evaluate("window.__city.openPanel('market')"); await pg.wait_for_timeout(800)
        await pg.screenshot(path=f"{OUT}/{PREFIX}-market.png")
        print("\n".join(logs) or "no console output")
        await b.close()
asyncio.run(main())
