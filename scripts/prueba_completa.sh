#!/usr/bin/env bash
# Prueba de punta a punta (lenta, ~5-10 min): edita el video de demostración (demo/, sin personas) en 16:9 y 9:16
# y revisa con el control de calidad: 60 fps, resolución, duración, -14 LUFS, pico real ≤ -1 dBTP.
# Uso: npm run prueba:render     (o: bash scripts/prueba_completa.sh final  para calidad final)
set -uo pipefail
cd "$(dirname "$0")/.."
CAL="${1:-preview}"
if [ ! -f demo/fotosintesis_demo.mov ]; then
  echo "Creando el video de demostración..."; bash demo/crear_demo.sh || exit 2
fi
FALLAS=0
for PRESET in colegio-tv tiktok; do
  echo "=== $PRESET ($CAL) ==="
  if ! bash scripts/editar.sh demo/fotosintesis_demo.mov --preset "$PRESET" --calidad "$CAL" \
       --extras demo/fotosintesis_extras.json --salida "salida/prueba_${PRESET}.mp4"; then
    FALLAS=$((FALLAS + 1))
  fi
done
[ "$FALLAS" -eq 0 ] && echo "PRUEBA COMPLETA: TODO BIEN" || echo "PRUEBA COMPLETA: $FALLAS formato(s) con problemas"
exit "$FALLAS"
