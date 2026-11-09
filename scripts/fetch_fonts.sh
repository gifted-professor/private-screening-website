#!/usr/bin/env bash
# Fetch 思源宋体 Light (Source Han Serif SC, SIL OFL 1.1) into fonts/ for the build.
# The npm package carries every weight (~170 MB unpacked); only the Light OTF is kept.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p fonts
tmp="$(mktemp -d)"
( cd "$tmp" && npm pack @fontpkg/source-han-serif-sc --silent >/dev/null )
tar -xzf "$tmp"/fontpkg-source-han-serif-sc-*.tgz -C "$tmp" package/SourceHanSerifSC-Light.otf
mv "$tmp/package/SourceHanSerifSC-Light.otf" fonts/
rm -rf "$tmp"
echo "fonts/SourceHanSerifSC-Light.otf ready"
