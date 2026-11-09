#!/usr/bin/env bash
# Prepara un video de referencia (uno cuyo estilo te gusta) para que Claude lo estudie.
# Saca 2 fotogramas por segundo + cada cambio de plano, y transcribe el audio.
# Uso: bash scripts/analizar_referencia.sh referencias/ejemplo.mp4
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/entorno.sh
REF="$1"
NOMBRE="$(basename "${REF%.*}")"
OUT="trabajo/ref_${NOMBRE}"
mkdir -p "$OUT/fotogramas" "$OUT/cambios_de_plano"

echo "Datos del video:"
if command -v ffprobe >/dev/null; then
  ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$REF" | tee "$OUT/info.txt"
else
  ffmpeg -hide_banner -i "$REF" 2>&1 | grep -E "Duration|Video:" | tee "$OUT/info.txt" || true
fi

echo "Sacando 2 fotogramas por segundo..."
ffmpeg -y -loglevel error -i "$REF" -vf "fps=2,scale=540:-1" "$OUT/fotogramas/f_%04d.jpg"

echo "Detectando cambios de plano (ritmo de cortes)..."
ffmpeg -y -loglevel info -i "$REF" -vf "select='gt(scene,0.3)',showinfo,scale=540:-1" -vsync vfr \
  "$OUT/cambios_de_plano/c_%04d.jpg" 2> "$OUT/cambios.log" || true
grep -o "pts_time:[0-9.]*" "$OUT/cambios.log" | cut -d: -f2 > "$OUT/tiempos_de_corte.txt" || true
echo "Cortes detectados: $(wc -l < "$OUT/tiempos_de_corte.txt")"

echo "Transcribiendo el audio..."
.venv/bin/python scripts/transcribe.py "$REF" "$OUT/transcripcion.json" --idioma auto || true

echo "LISTO: $OUT  (Claude: mira los fotogramas y escribe las reglas en estilo.md)"
