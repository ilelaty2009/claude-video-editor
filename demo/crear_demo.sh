#!/usr/bin/env bash
# Crea demo/fotosintesis_demo.mov: un video SIN PERSONAS (fondo animado + voz sintética de macOS) para probar el editor
# y hacer las capturas del README. Necesita macOS (comando `say`) y ffmpeg.
set -euo pipefail
cd "$(dirname "$0")"
say -v "Mónica" -r 165 -f guion.txt -o voz.aiff
ffmpeg -v error -y -i voz.aiff -af "apad=pad_dur=0.6" -ar 48000 voz.wav
D="$(ffmpeg -i voz.wav 2>&1 | sed -n 's/.*Duration: \([0-9:.]*\).*/\1/p' | awk -F: '{print $1*3600+$2*60+$3}')"
ffmpeg -v error -y -f lavfi -i "gradients=s=1920x1080:c0=0x0b3d2e:c1=0x1d6b4f:c2=0x0f2742:c3=0x3a7d44:n=4:speed=0.012:rate=30:duration=$D" \
  -i voz.wav -vf "drawbox=x=760:y=300:w=400:h=400:color=white@0.06:t=fill,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -shortest fotosintesis_demo.mov
rm -f voz.aiff voz.wav
echo "OK: demo/fotosintesis_demo.mov"
