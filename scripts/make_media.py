"""Regenerate the brand media in src/media/ from src/brand/ (needs ffmpeg).

    python3 scripts/make_media.py

Makes webp copies of the three 《红线尽头是你》 stills, video posters for the 5-second intro and
8-second outro, and a detail crop. The 《红线尽头是你》 film in the player and the 片库 cards come
from scripts/make_works.py.
"""
import os
import shutil
import subprocess
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
brand = os.path.join(ROOT, "src/brand")
out = os.path.join(ROOT, "src/media")
intro = os.path.join(brand, "video/intro-5s.mp4")
outro = os.path.join(brand, "video/outro-8s.mp4")
stills = ["redline-1-phoenix-crown.jpg", "redline-2-stone-bridge.jpg", "redline-3-bicycle.jpg"]
os.makedirs(out, exist_ok=True)
tmp = tempfile.mkdtemp()


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


for i, name in enumerate(stills, 1):
    Image.open(os.path.join(brand, "stills", name)).convert("RGB").save(
        os.path.join(out, f"redline-{i}.webp"), "WEBP", quality=84, method=6)

for src, at, name in ((intro, "4.4", "intro-poster"), (outro, "3.5", "outro-poster")):
    png = os.path.join(tmp, name + ".png")
    run(["ffmpeg", "-y", "-ss", at, "-i", src, "-frames:v", "1", "-vf", "scale=960:540", png])
    Image.open(png).convert("RGB").save(os.path.join(out, name + ".webp"), "WEBP", quality=82, method=6)
shutil.copyfile(intro, os.path.join(out, "intro-5s.mp4"))
shutil.copyfile(outro, os.path.join(out, "outro-8s.mp4"))
Image.open(os.path.join(brand, "stills", "redline-3-bicycle.jpg")).convert("RGB").crop((300, 600, 720, 880)).save(
    os.path.join(out, "detail-redstring.webp"), "WEBP", quality=86, method=6)
shutil.rmtree(tmp)
print("src/media regenerated")
