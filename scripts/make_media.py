"""Regenerate src/media/ from src/brand/ (needs ffmpeg with libx264 and drawtext).

    python3 scripts/make_media.py

Makes the placeholder trailer (片头 → three 《红绳》 stills marked 占位 → 片尾), the player
poster, video posters for the 5-second intro and 8-second outro, a detail crop, and webp
copies of the stills. When the finished 《红绳》 film is ready, put it at
src/media/redline-preview.mp4 instead, and update the chapter times in the template.
"""
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageEnhance, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
brand = os.path.join(ROOT, "src/brand")
out = os.path.join(ROOT, "src/media")
font = os.path.join(ROOT, "fonts/SourceHanSerifSC-Light.otf")
intro = os.path.join(brand, "video/intro-5s.mp4")
outro = os.path.join(brand, "video/outro-8s.mp4")
stills = [
    ("redline-1-phoenix-crown.jpg", "第一世 · 凤冠团扇"),
    ("redline-2-stone-bridge.jpg", "第一世 · 落花石桥"),
    ("redline-3-bicycle.jpg", "第三世 · 单车"),
]
os.makedirs(out, exist_ok=True)
tmp = tempfile.mkdtemp()
W, H = 2560, 1440


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def label(text, x, y, size, alpha, start=0.35):
    f = font.replace(":", r"\:")
    return f"drawtext=fontfile='{f}':text='{text}':x={x}:y={y}:fontsize={size}:fontcolor=0xF3ECE0:alpha='min({alpha},max(0,(t-{start})*2))'"


# 16:9 composites: blurred, darkened cover background + the sharp portrait still in the middle
for i, (name, cap) in enumerate(stills, 1):
    im = Image.open(os.path.join(brand, "stills", name)).convert("RGB")
    bg = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
    top = (bg.height - H) // 2
    bg = ImageEnhance.Brightness(bg.crop((0, top, W, top + H)).filter(ImageFilter.GaussianBlur(48))).enhance(0.42)
    fg = im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, 0))
    comp = os.path.join(tmp, f"comp-{i}.png")
    bg.save(comp)
    if i == 2:
        bg.resize((1280, 720), Image.LANCZOS).save(os.path.join(out, "player-poster.webp"), "WEBP", quality=80, method=6)
    vf = ",".join([
        "scale=w='trunc(1280*(1+0.06*t/5)/2)*2':h=-2:eval=frame", "crop=1280:720",
        label("占位预览 · 剧照拼接，待换成《红绳》成片", 40, 34, 20, 0.72, 0.2),
        label(cap, 40, "h-62", 26, 0.95),
        label("本片含 AI 生成内容", "w-tw-40", "h-58", 18, 0.85, 0),
        "fps=24,format=yuv420p,settb=1/24",
    ])
    run(["ffmpeg", "-y", "-loop", "1", "-t", "5", "-i", comp, "-vf", vf, "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-an", os.path.join(tmp, f"clip-{i}.mp4")])
    im.save(os.path.join(out, f"redline-{i}.webp"), "WEBP", quality=84, method=6)

norm = "scale=1280:720,fps=24,format=yuv420p,settb=1/24"
run(["ffmpeg", "-y", "-i", intro, "-vf", norm, "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-an", os.path.join(tmp, "clip-0.mp4")])
run(["ffmpeg", "-y", "-i", outro, "-vf", norm, "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-an", os.path.join(tmp, "clip-4.mp4")])

# intro 5s + three stills 5s each + outro 8s, 0.6s cross-fades -> 25.6s; key frames at each cut stop ghosting
args = ["ffmpeg", "-y"]
for i in range(5):
    args += ["-i", os.path.join(tmp, f"clip-{i}.mp4")]
fc = ("[0][1]xfade=transition=fade:duration=0.6:offset=4.4[a];[a][2]xfade=transition=fade:duration=0.6:offset=8.8[b];"
      "[b][3]xfade=transition=fade:duration=0.6:offset=13.2[c];[c][4]xfade=transition=fade:duration=0.6:offset=17.6,noise=alls=6:allf=t,format=yuv420p[v]")
args += ["-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "26", "-preset", "veryfast",
         "-force_key_frames", "0,5,9.4,13.8,18.2,20,22,24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
         os.path.join(out, "redline-preview.mp4")]
run(args)

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
