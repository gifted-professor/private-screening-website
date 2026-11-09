"""Make the 片库 (template library) media in src/media/ from the finished films on the studio drive.

    python3 scripts/make_works.py               # posters, silent loops and the playable films
    python3 scripts/make_works.py --skip-films  # posters and silent loops only

Needs ffmpeg with libx264, Pillow, and /Volumes/SN580X mounted.

Every template gets
    work-<slug>.webp        card poster, 960×540
    work-<slug>-loop.mp4    a few silent seconds for the card, 640×360, no audio track
Templates with an original score also get
    film-<slug>.webp        player poster, 1280×720
    film-<slug>.mp4         the film with sound, 720p

Music: the 90/150-second template cuts in ai 婚礼/模板 carry the original songs (仅自己看), so for
川西、新疆、明制、唐风 only silent loops are cut from them. The playable films come from the
影楼版 / original-score cuts: 红绳 影楼用 90 秒, 十世 90 秒 (Seed Audio score), 雪国 影楼加长版,
镰仓 影楼版.

film-*.mp4 are large and stay out of git (see .gitignore). Ship them with site/ or put them on the CDN.
"""
import argparse
import os
import shutil
import subprocess
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src/media")
TPL = "/Volumes/SN580X/服务器/AIGC/ai 婚礼/模板"
FIN = "/Volumes/SN580X/服务器/AIGC/成品"

# slug: (source, loop start, loop end, poster time, playable?, player-poster time)
# Loop windows start and end on shot cuts and skip shots with on-screen captions or title cards.
WORKS = {
    "redline": (f"{FIN}/三生三世/07_剪辑/红绳_三生三世_90秒_影楼用.mp4", 13.10, 19.92, 19.0, True, 11.5),
    "shishi": (f"{TPL}/十世皆是你（十世）/90秒最终成片.mp4", 10.12, 15.20, 13.5, True, 13.5),
    "mingzhi": (f"{TPL}/三书许卿（明制大片）/150s 成片.mp4", 59.12, 64.58, 107.9, False, None),
    "tangfeng": (f"{TPL}/一眼一生（唐风）/三生三世_150s_最终成片.mp4", 80.00, 85.96, 91.5, False, None),
    "kamakura": (f"{FIN}/镰仓婚前MV素材包/07_成片/镰仓婚前MV_影楼版_v1.mp4", 8.70, 13.92, 10.2, True, 10.2),
    "xueguo": (f"{FIN}/雪国婚前MV素材包/07_成片/雪国婚前MV_影楼版_加长版_v3.mp4", 2.08, 7.54, 5.0, True, 5.0),
    "chuanxi": (f"{TPL}/此去是余生（川西）/150s 成片.mp4", 83.25, 89.90, 85.0, False, None),
    "xinjiang": (f"{TPL}/和你去撒野（新疆）/150s 成片.mp4", 63.29, 69.40, 66.0, False, None),
}


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def still(src, at, size, dest, tmp):
    png = os.path.join(tmp, "frame.png")
    run(["ffmpeg", "-y", "-ss", str(at), "-i", src, "-frames:v", "1", "-vf", f"scale={size}:flags=lanczos", png])
    Image.open(png).convert("RGB").save(dest, "WEBP", quality=80, method=6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-films", action="store_true", help="only posters and silent loops")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp()
    for slug, (src, a, b, poster, playable, pposter) in WORKS.items():
        assert os.path.exists(src), f"missing source: {src}"
        still(src, poster, "960:540", os.path.join(OUT, f"work-{slug}.webp"), tmp)
        run(["ffmpeg", "-y", "-ss", f"{a:.2f}", "-t", f"{b - a:.2f}", "-i", src, "-an",
             "-vf", "scale=640:360:flags=lanczos,fps=24,format=yuv420p",
             "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-profile:v", "high", "-g", "48",
             "-movflags", "+faststart", os.path.join(OUT, f"work-{slug}-loop.mp4")])
        if playable:
            still(src, pposter, "1280:720", os.path.join(OUT, f"film-{slug}.webp"), tmp)
            if not args.skip_films:
                run(["ffmpeg", "-y", "-i", src, "-vf", "scale=1280:720:flags=lanczos,format=yuv420p",
                     "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-profile:v", "high",
                     "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                     os.path.join(OUT, f"film-{slug}.mp4")])
        made = sorted(f for f in os.listdir(OUT) if f.startswith((f"work-{slug}", f"film-{slug}")))
        print(slug, " ".join(f"{f} {os.path.getsize(os.path.join(OUT, f)) / 1e6:.1f}MB" for f in made))
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
