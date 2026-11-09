#!/usr/bin/env bash
# Regenera las imágenes del README (carpeta docs/) con el PROPIO editor, a partir del video de demostración
# (demo/, sin personas). Antes hay que correr: npm run prueba:render   (deja salida/prueba_*.mp4)
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/entorno.sh
TV=salida/prueba_colegio-tv.mp4
RL=salida/prueba_tiktok.mp4
for f in "$TV" "$RL"; do [ -f "$f" ] || { echo "Falta $f: corre primero npm run prueba:render"; exit 1; }; done
mkdir -p docs

# GIF corto (titular + tarjetas), 12 cuadros por segundo para que pese poco
ffmpeg -v error -y -ss 9.4 -t 6.5 -i "$TV" \
  -vf "fps=12,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" \
  docs/demo.gif
ffmpeg -v error -y -ss 7.6 -i "$TV" -frames:v 1 -q:v 3 docs/tv.jpg
ffmpeg -v error -y -ss 7.6 -i "$RL" -frames:v 1 -vf scale=360:-2 -q:v 3 docs/reel.jpg

# Un fotograma por estilo de subtítulos (a tamaño real, reducido a la mitad)
bash scripts/editar.sh demo/fotosintesis_demo.mov --preset colegio-tv --extras demo/fotosintesis_extras.json --solo-preparar >/dev/null
cp public/edit.json trabajo/edit_capturas.json
for s in cine caja tiktok resaltado; do
  .venv/bin/python -c "import json,sys; d=json.load(open('trabajo/edit_capturas.json')); d['subtitulos']=sys.argv[1]; d['look']='tiktok' if sys.argv[1]=='tiktok' else d['look']; json.dump(d,open('public/edit.json','w'),ensure_ascii=False)" "$s"
  npx remotion still src/index.ts Edit "docs/sub_$s.jpg" --frame=200 --scale=0.5 --jpeg-quality 85 --log error
done
cp trabajo/edit_capturas.json public/edit.json
ls -la docs
