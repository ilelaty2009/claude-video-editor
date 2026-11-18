#!/usr/bin/env bash
# Regenera la portada del repositorio (docs/portada.png, 1280x640) a partir de docs/portada.html.
# Usa Google Chrome sin ventana (no baja nada).
set -euo pipefail
cd "$(dirname "$0")/.."
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ ! -x "$CHROME" ]; then
  echo "PROBLEMA: no encuentro Google Chrome. QUÉ HACER: instálalo, o abre docs/portada.html y toma una captura de 1280x640."
  exit 1
fi
PERFIL=$(mktemp -d)
trap 'rm -rf "$PERFIL"' EXIT
"$CHROME" --headless=new --user-data-dir="$PERFIL" --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --window-size=1280,640 --screenshot="$PWD/docs/portada.png" "file://$PWD/docs/portada.html" >/dev/null 2>&1
echo "Listo: docs/portada.png"
