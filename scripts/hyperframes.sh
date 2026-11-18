#!/usr/bin/env bash
# EFECTOS CON HYPERFRAMES (gratis, Apache 2.0): renderiza un efecto hecho en HTML (3D real, etc.) y lo deja en
# public/broll/ para usarlo en el editor. Los efectos están en hyperframes/<nombre>/index.html.
#   bash scripts/hyperframes.sh tarjeta3d --formato reel --variables '{"frente":"ANTES","atras":"DESPUÉS"}'
#   bash scripts/hyperframes.sh tarjeta3d --formato tv --salida antes_despues
# Sale un .webm con fondo TRANSPARENTE a 60 fps: public/broll/hf_<salida>.webm
# En los extras: {"tipo": "capa", "archivo": "broll/hf_<salida>.webm", "desde": 12.0, "hasta": 16.0}
# Necesita internet la primera vez (baja GSAP, la librería de animación, y un Chrome para renderizar).
set -uo pipefail
cd "$(dirname "$0")/.."
source scripts/entorno.sh
[ $# -ge 1 ] || { echo "Uso: bash scripts/hyperframes.sh <efecto> [--formato tv|reel|cuadrado|retrato] [--variables '{...}'] [--salida nombre]"; ls hyperframes 2>/dev/null | sed 's/^/  efecto disponible: /'; exit 1; }
EFECTO="$1"; shift
FORMATO="reel"; VARIABLES="{}"; SALIDA="$EFECTO"
while [ $# -gt 0 ]; do
  case "$1" in
    --formato) FORMATO="$2"; shift 2;;
    --variables) VARIABLES="$2"; shift 2;;
    --salida) SALIDA="$2"; shift 2;;
    *) echo "PROBLEMA: opción desconocida: $1"; exit 2;;
  esac
done
[ -f "hyperframes/$EFECTO/index.html" ] || { echo "PROBLEMA: no existe el efecto hyperframes/$EFECTO/index.html"; ls hyperframes | sed 's/^/  disponible: /'; exit 2; }
[ -x node_modules/.bin/hyperframes ] || { echo "PROBLEMA: falta HyperFrames. QUÉ HACER: corre npm install (o instalar.command)."; exit 2; }
read -r ANCHO ALTO < <(.venv/bin/python -c "import json,sys;f=json.load(open('editor.config.json'))['formatos'].get(sys.argv[1]);print(f['ancho'],f['alto']) if f else sys.exit(1)" "$FORMATO") \
  || { echo "PROBLEMA: no conozco el formato '$FORMATO' (usa tv, reel, cuadrado o retrato)."; exit 2; }
TRABAJO="trabajo/hyperframes/${SALIDA}_${FORMATO}"
rm -rf "$TRABAJO" && mkdir -p "$TRABAJO" public/broll
sed "s/__ANCHO__/$ANCHO/g; s/__ALTO__/$ALTO/g" "hyperframes/$EFECTO/index.html" > "$TRABAJO/index.html"
find "hyperframes/$EFECTO" -type f ! -name index.html -exec cp {} "$TRABAJO/" \;
DESTINO="$PWD/public/broll/hf_${SALIDA}.webm"
echo "Renderizando el efecto $EFECTO (${ANCHO}x${ALTO}, 60 fps, fondo transparente)..."
if node_modules/.bin/hyperframes render "$TRABAJO" --format webm --fps 60 --workers 1 --quiet --variables "$VARIABLES" --output "$DESTINO" > "$TRABAJO/render.log" 2>&1 && [ -s "$DESTINO" ]; then
  echo "LISTO: public/broll/hf_${SALIDA}.webm"
  echo "  En los extras: {\"tipo\": \"capa\", \"archivo\": \"broll/hf_${SALIDA}.webm\", \"desde\": SEGUNDO, \"hasta\": SEGUNDO+4}"
else
  echo "PROBLEMA: HyperFrames no pudo renderizar el efecto."
  echo "QUÉ HACER: revisa que haya internet (baja GSAP y Chrome la primera vez). Detalle técnico:"
  tail -15 "$TRABAJO/render.log" | sed 's/^/    /'
  exit 2
fi
