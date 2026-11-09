"""Build the site into site/ from src/index.template.html.

    python3 scripts/build.py                 # GSAP / Lenis load from jsDelivr
    python3 scripts/build.py --local-vendor  # copy GSAP / Lenis into site/assets/vendor (for servers in mainland China)

Needs: fonts/SourceHanSerifSC-Light.otf (scripts/fetch_fonts.sh), node_modules (npm install),
       pip install -r requirements.txt

Fonts: every character used on the page is subset into one inline woff2. The rest of the
GB2312 level-1 set (what visitors may type into the poster and booking forms) is split into
unicode-range chunks under assets/fonts/, so a browser only downloads what it renders.
"""
import argparse
import base64
import io
import os
import re
import shutil
import urllib.parse

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--template", default=os.path.join(ROOT, "src/index.template.html"))
ap.add_argument("--logo", default=os.path.join(ROOT, "src/brand/logo"))
ap.add_argument("--media", default=os.path.join(ROOT, "src/media"))
ap.add_argument("--font", default=os.path.join(ROOT, "fonts/SourceHanSerifSC-Light.otf"))
ap.add_argument("--node-modules", default=os.path.join(ROOT, "node_modules"))
ap.add_argument("--out", default=os.path.join(ROOT, "site"))
ap.add_argument("--local-vendor", action="store_true", help="serve GSAP and Lenis from site/assets/vendor")
args = ap.parse_args()

corm_dir = os.path.join(args.node_modules, "@fontsource/cormorant-garamond/files")
if os.path.isdir(args.out):
    shutil.rmtree(args.out)
for d in ("assets/fonts", "assets/img", "assets/video"):
    os.makedirs(os.path.join(args.out, d), exist_ok=True)

html = open(args.template, encoding="utf-8").read()


def path_d(name):
    svg = open(os.path.join(args.logo, name), encoding="utf-8").read()
    return re.search(r' d="([^"]+)"', svg).group(1)


key_d, icon_d, seal_d = path_d("logo-key.svg"), path_d("logo-icon.svg"), path_d("logo-seal.svg")
fav_svg = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 168 168'>"
    "<rect width='168' height='168' rx='30' fill='#1D1B1A'/>"
    "<g transform='translate(42 14) scale(.84)'>"
    f"<path fill='#F3ECE0' fill-rule='evenodd' d='{icon_d}'/></g></svg>"
)
favicon = "data:image/svg+xml," + urllib.parse.quote(fav_svg, safe=" '=:/,.-()")
html = html.replace("%%KEY_D%%", key_d).replace("%%ICON_D%%", icon_d).replace("%%SEAL_D%%", seal_d).replace("%%FAVICON%%", favicon)

scan = re.sub(r"data:[a-z+/]+;base64,[A-Za-z0-9+/=]+", "", html)
base_chars = sorted({c for c in scan if ord(c) > 0x7F})
latin = "".join(chr(i) for i in range(0x20, 0x7F)) + "·¥©×–—‘’“”′″"


def ranges(cps):
    cps = sorted(set(cps))
    out, i = [], 0
    while i < len(cps):
        j = i
        while j + 1 < len(cps) and cps[j + 1] == cps[j] + 1:
            j += 1
        out.append(f"U+{cps[i]:X}" if i == j else f"U+{cps[i]:X}-{cps[j]:X}")
        i = j + 1
    return ",".join(out)


def subset_woff2(src, text):
    font = TTFont(src)
    opts = Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    opts.hinting = False
    opts.desubroutinize = True
    opts.name_IDs = [0, 1, 2, 3, 4, 5, 6]
    opts.notdef_outline = True
    sub = Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return buf.getvalue()


def inline_face(family, data, weight, style, urange=None):
    src = "data:font/woff2;base64," + base64.b64encode(data).decode()
    ur = f"unicode-range:{urange};" if urange else ""
    return f'@font-face{{font-family:"{family}";src:url({src}) format("woff2");font-weight:{weight};font-style:{style};font-display:swap;{ur}}}'


faces = [inline_face("ZY Han Serif", subset_woff2(args.font, "".join(base_chars)), 300, "normal", ranges(ord(c) for c in base_chars))]

level1 = []
for hi in range(0xB0, 0xD8):
    for lo in range(0xA1, 0xFF):
        try:
            level1.append(bytes([hi, lo]).decode("gb2312"))
        except UnicodeDecodeError:
            pass
base_set = set(base_chars)
ext = [c for c in level1 if c not in base_set]
CHUNK = 120
for n, i in enumerate(range(0, len(ext), CHUNK), 1):
    part = ext[i : i + CHUNK]
    name = f"han-{n:02d}.woff2"
    open(os.path.join(args.out, "assets/fonts", name), "wb").write(subset_woff2(args.font, "".join(part)))
    faces.append(
        f'@font-face{{font-family:"ZY Han Serif";src:url(assets/fonts/{name}) format("woff2");'
        f"font-weight:300;font-style:normal;font-display:swap;unicode-range:{ranges(ord(c) for c in part)};}}"
    )
faces.append(inline_face("ZY Cormorant", subset_woff2(os.path.join(corm_dir, "cormorant-garamond-latin-500-normal.woff2"), latin), 500, "normal"))
faces.append(inline_face("ZY Cormorant", subset_woff2(os.path.join(corm_dir, "cormorant-garamond-latin-500-italic.woff2"), latin), 500, "italic"))
html = html.replace("%%FONTS%%", "\n".join(faces))
assert not re.findall(r"%%[A-Z0-9_]+%%", html), "unfilled placeholder in template"

for f in sorted(os.listdir(args.media)):
    sub = "video" if f.endswith(".mp4") else "img"
    shutil.copyfile(os.path.join(args.media, f), os.path.join(args.out, "assets", sub, f))

if args.local_vendor:
    os.makedirs(os.path.join(args.out, "assets/vendor"), exist_ok=True)
    libs = {
        "https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js": "gsap/dist/gsap.min.js",
        "https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js": "gsap/dist/ScrollTrigger.min.js",
        "https://cdn.jsdelivr.net/npm/lenis@1.3.26/dist/lenis.min.js": "lenis/dist/lenis.min.js",
    }
    for url, rel in libs.items():
        assert url in html, url
        name = os.path.basename(rel)
        shutil.copyfile(os.path.join(args.node_modules, rel), os.path.join(args.out, "assets/vendor", name))
        html = html.replace(url, f"assets/vendor/{name}")

for ref in sorted(set(re.findall(r"assets/[a-z]+/[A-Za-z0-9._-]+", html))):
    assert os.path.exists(os.path.join(args.out, ref)), f"missing asset: {ref}"

open(os.path.join(args.out, "index.html"), "w", encoding="utf-8").write(html)
print(f"site/index.html {len(html.encode('utf-8')) / 1024:.0f} KB · {len(base_chars)} characters inline · {len(faces) - 3} font chunks"
      + (" · vendor libs local" if args.local_vendor else " · vendor libs from jsDelivr"))
