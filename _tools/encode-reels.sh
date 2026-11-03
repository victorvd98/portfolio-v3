#!/bin/bash
# Turn large original vertical videos into small web versions for the reel
# carousels, plus a cover image for each (shown while the video loads).
#
# Usage (from the repo root):
#     _tools/encode-reels.sh _originals/peugeot/2008 assets/peugeot/2008
#     _tools/encode-reels.sh _originals/peugeot/2008/01_TINY_PLANET.mp4 assets/peugeot/2008
#
# Originals are never changed. Each output is named after its original:
# "01_TINY_PLANET.mp4" -> "tiny-planet.mp4" + "tiny-planet.jpg"
# (leading numbers and editing suffixes like _VDEF / _prob4 are dropped).
set -euo pipefail

src="$1"
out="$2"
mkdir -p "$out"

slug() {
    local name
    name=$(basename "$1")
    name="${name%.*}"
    echo "$name" | tr '[:upper:]' '[:lower:]' \
        | sed -E 's/^#?[0-9]+[_ -]+//; s/[_ ]+/-/g; s/-(vdef|v[0-9]+|final|prob[0-9]*)//g; s/-+$//'
}

encode() {
    local in="$1" name
    name=$(slug "$in")
    echo "→ $(basename "$in")  =>  $out/$name.mp4"
    # 1080x1920 (never upscaled), H.264 high profile, quality-based (CRF 23) but
    # capped at 4.5 Mbps (about what Instagram/TikTok serve) so busy clips stay small;
    # sound kept, start-playing-early (faststart), editing metadata dropped
    ffmpeg -loglevel error -stats -y -i "$in" \
        -map 0:v:0 -map 0:a:0? -map_metadata -1 \
        -vf "scale='min(1080,iw)':-2:flags=lanczos,format=yuv420p" \
        -c:v libx264 -preset slow -crf 23 -maxrate 4500k -bufsize 9000k -profile:v high \
        -c:a aac -b:a 128k -ac 2 \
        -movflags +faststart \
        "$out/$name.mp4"
    # cover image: a frame from 1 second in, at half size
    ffmpeg -loglevel error -y -ss 1 -i "$out/$name.mp4" -frames:v 1 \
        -vf "scale=540:-2:flags=lanczos" -q:v 4 "$out/$name.jpg"
}

if [ -d "$src" ]; then
    for f in "$src"/*; do
        case "$f" in *.mp4|*.MP4|*.mov|*.MOV|*.m4v|*.M4V) encode "$f" ;; esac
    done
else
    encode "$src"
fi
