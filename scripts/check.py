"""Screenshot the built site at desktop and phone sizes, and report script errors.

    python3 scripts/check.py            # writes shots/d-*.png and shots/m-*.png
    CHROME_PATH=/path/to/chrome python3 scripts/check.py

Needs: pip install -r requirements.txt && python3 -m playwright install chromium
"""
import functools
import http.server
import os
import threading
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE, NM, OUT = os.path.join(ROOT, "site"), os.path.join(ROOT, "node_modules"), os.path.join(ROOT, "shots")
os.makedirs(OUT, exist_ok=True)
CDN = {
    "gsap@3.15.0/dist/gsap.min.js": "gsap/dist/gsap.min.js",
    "gsap@3.15.0/dist/ScrollTrigger.min.js": "gsap/dist/ScrollTrigger.min.js",
    "lenis@1.3.26/dist/lenis.min.js": "lenis/dist/lenis.min.js",
}
SCENES = ["#screen", "#cinema", "#poster", "#pricing", "#extras", "#compare", "#more", "#questions",
          "#process", "#likeness", "#team", "#rules", "#faq", "#partner", "#booking", "footer"]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=SITE))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_address[1]}/index.html"


def cdn(route):
    for k, rel in CDN.items():
        if route.request.url.endswith(k) and os.path.exists(os.path.join(NM, rel)):
            return route.fulfill(path=os.path.join(NM, rel), content_type="application/javascript")
    return route.continue_()


with sync_playwright() as p:
    launch = {"executable_path": os.environ["CHROME_PATH"]} if os.environ.get("CHROME_PATH") else {}
    browser = p.chromium.launch(**launch)
    for tag, vp, mobile in (("d", {"width": 1440, "height": 900}, False), ("m", {"width": 390, "height": 844}, True)):
        ctx = browser.new_context(viewport=vp, is_mobile=mobile, has_touch=mobile, locale="zh-CN")
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route("https://cdn.jsdelivr.net/**", cdn)
        page.goto(base)
        time.sleep(3.8)
        page.screenshot(path=f"{OUT}/{tag}-00-hero.png")
        for i, sel in enumerate(SCENES, 1):
            y = page.evaluate(f"document.querySelector('{sel}').getBoundingClientRect().top + pageYOffset")
            page.evaluate(f"window.scrollTo(0, {int(y) + 10})")
            time.sleep(1.6)
            page.screenshot(path=f"{OUT}/{tag}-{i:02d}-{sel.strip('#')}.png")
        print(f"{tag}: {len(SCENES) + 1} screenshots, script errors: {errors or 'none'}")
        ctx.close()
    browser.close()
server.shutdown()
