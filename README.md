# 只映给你 · PRIVATE SCREENING 官网

把你们的爱情故事，做成一部电影。这个仓库放官网的源码，以及可以直接部署的成品。

整站是一场私人放映：锁孔入场，然后分成序幕和四幕（看片 / 选片 / 怎么做 / 预约），一共 16 场，右上角「节目单」可以随时跳转。

## 目录

```
site/                   可直接部署的成品：index.html + assets/（动效库已放本地，适合国内服务器）
src/index.template.html 页面源码：文案、样式、交互都在这一个文件里
src/brand/              品牌原始素材：logo、《红线尽头是你》剧照、5 秒片头、8 秒片尾
src/media/              页面用的图片和视频（两个 make_ 脚本生成，也可以直接替换）
scripts/build.py        把 src 构建到 site/：字体子集、拷贝素材
scripts/make_media.py   从 src/brand 生成剧照 webp、片头片尾封面（需要 ffmpeg）
scripts/make_works.py   从工作室硬盘的成片生成「片库」：封面、静音循环、可播放的成片（需要 ffmpeg，挂载 /Volumes/SN580X）
scripts/check.py        桌面和手机尺寸截图，检查脚本报错
scripts/fetch_fonts.sh  下载思源宋体 Light 到 fonts/（构建用，不进仓库）
```

## 本地预览

```bash
python3 -m http.server 8000 --directory site
# 浏览器打开 http://localhost:8000
```

不要直接双击 index.html：浏览器不允许本地文件加载字体，页面会退回系统字体。

## 改内容

文案、价格、问答、章节时间都在 `src/index.template.html` 里。改完重新构建：

```bash
npm install                               # GSAP、Lenis、Cormorant Garamond
bash scripts/fetch_fonts.sh               # 思源宋体 Light → fonts/
pip install -r requirements.txt
python3 scripts/build.py --local-vendor   # 动效库放本地（国内部署用这个）
# python3 scripts/build.py                # 动效库走 jsDelivr
```

放映厅的《红线尽头是你》和「片库」八个故事的素材来自 `/Volumes/SN580X/服务器/AIGC/ai 婚礼/模板` 和成品区，换片、改预览片段或封面时间点都在 `scripts/make_works.py` 顶部的 `WORKS` 里改，然后：

```bash
python3 scripts/make_works.py             # 约半分钟；--skip-films 只出封面和静音循环
```

配乐规则：模板文件夹里的 90 / 150 秒成片配的是原曲，只能自己看。网页上能带声音放的只有原创配乐的四部（红线尽头是你的影楼版、十世皆是你、踏雪共白头和夏天的约定的影楼精简版），川西、新疆、明制、唐风只放静音循环，卡片点进去是预约。

页面上出现的字会内嵌进 index.html，其余常用字（GB2312 一级字）拆成小文件按需加载。改了文案一定要重新构建，新加的字才会用上思源宋体。

截图检查（可选）：

```bash
python3 -m playwright install chromium
python3 scripts/check.py                  # 截图在 shots/
```

## 还在占位的内容

| 位置 | 现在 | 换成 |
|---|---|---|
| 像不像（对比滑块） | 左边是占位图 | 同一对真人的原照片和剧照（要有授权） |
| 幕后 | 三张照片和姓名待填 | 团队照片和姓名 |
| 不只是婚礼 | 六张示意图待补 | 示意图；做不做、怎么收费待定 |
| 预约 | 企业微信「即将开通」 | 企业微信二维码 |
| 页脚 | 没有备案号 | ICP 备案号 |

## 上线前

- 放在中国大陆的服务器要先做 ICP 备案，页脚加上备案号。
- 用 `--local-vendor` 构建，动效库不依赖海外 CDN；字体已经在本地。
- 视频放对象存储或 CDN，确认支持 Range 请求（播放器拖进度条需要）。
- 样片和片库八个故事里的新人都已签肖像和案例授权（2026-11-08 确认）；以后往片库加新片，也要先有授权。
- `film-*.mp4`（片库能播放的四部，共约 40 MB）不进 git，构建前先跑 `scripts/make_works.py`，部署时和 site/ 一起上传或放 CDN。

## 第三方

- 思源宋体 Source Han Serif、Cormorant Garamond：SIL Open Font License 1.1
- GSAP 3.15：GreenSock 标准许可，免费使用
- Lenis 1.3：MIT
