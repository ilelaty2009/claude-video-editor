#!/usr/bin/env bash
# Revisión automática ANTES del render completo (como hace un editor profesional).
# Saca un fotograma de cada momento importante (inicio, título, la mitad de cada escena, capítulos, final)
# y los junta en UNA imagen: trabajo/<nombre>_revision.jpg. Claude la abre con Read y arregla lo que se vea mal.
# Uso: bash scripts/revisar.sh [nombre]     (usa public/edit.json, que deja: bash scripts/editar.sh X --solo-preparar)
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/entorno.sh
NOMBRE="${1:-revision}"
DIR="trabajo/revision_${NOMBRE}"
rm -rf "$DIR" && mkdir -p "$DIR"
PY=".venv/bin/python"; [ -x "$PY" ] || PY="python3"

# lista de fotogramas a revisar (y qué es cada uno)
"$PY" - <<'EOF' > "$DIR/fotogramas.txt"
import json
d = json.load(open("public/edit.json", encoding="utf-8"))
fps, total = d["fps"], d["durationInFrames"]
f = lambda ms: int(ms / 1000 * fps)
puntos = [(min(fps // 2, total - 1), "inicio")]
if d.get("titulo"):
    puntos.append((int(fps * 1.2), "titulo"))
for e in d.get("escenas", []):
    a, b = f(e["desdeMs"]), f(e["hastaMs"])
    puntos.append((a + int((b - a) * 0.75), "escena " + e["tipo"]))
for c in d.get("capitulos", []):
    puntos.append((f(c["desdeMs"]) + int(fps * 0.7), "capitulo"))
puntos.append((max(0, total - fps // 3), "final"))
vistos = set()
print("FPS", fps)
for fr, que in sorted(puntos):
    fr = max(0, min(total - 1, fr))
    if fr in vistos:
        continue
    vistos.add(fr)
    print(fr, que)
EOF

echo "Preparando vista previa (una sola vez)..."
npx remotion bundle src/index.ts --out-dir "$DIR/bundle" --log error >/dev/null
FPS="$(awk '/^FPS/{print $2}' "$DIR/fotogramas.txt")"
sed -i '' '/^FPS/d' "$DIR/fotogramas.txt"
i=0
while read -r FR QUE; do
  i=$((i + 1))
  N="$(printf %03d $i)"
  # "< /dev/null": que npx y ffmpeg no se coman la lista de fotogramas que lee este ciclo
  npx remotion still "$DIR/bundle" Edit "$DIR/$N.png" --frame="$FR" --scale=0.33 --log error < /dev/null
  # todas a JPG del mismo tipo (si no, ffmpeg reinicia el mosaico cuando cambia el formato de color)
  ffmpeg -y -loglevel error -i "$DIR/$N.png" -pix_fmt yuvj420p "$DIR/$N.jpg" < /dev/null && rm -f "$DIR/$N.png"
  echo "  $(printf %03d $i): cuadro $FR ($(awk "BEGIN{printf \"%.1f\", $FR/$FPS}") s) — $QUE"
done < "$DIR/fotogramas.txt"
ffmpeg -y -loglevel error -framerate 1 -start_number 1 -i "$DIR/%03d.jpg" \
  -vf "tile=3x$(( (i + 2) / 3 )):padding=6:color=white" -frames:v 1 -update 1 "trabajo/${NOMBRE}_revision.jpg"
rm -rf "$DIR/bundle"
echo "LISTO: trabajo/${NOMBRE}_revision.jpg ($i fotogramas, de izquierda a derecha y de arriba abajo)"
