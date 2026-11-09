#!/usr/bin/env bash
# Edita un video de punta a punta con UN comando. Ejemplos:
#   bash scripts/editar.sh videos/mi-video.mov --preset colegio-tv
#   bash scripts/editar.sh videos/mi-video.mov --preset tiktok --extras trabajo/mi-video_extras.json
#   bash scripts/editar.sh videos/mi-video.mov --formato cuadrado --calidad preview
# Todas las opciones: bash scripts/editar.sh --help      (el programa está en scripts/editor.py)
set -uo pipefail
cd "$(dirname "$0")/.."
source scripts/entorno.sh
if [ ! -x .venv/bin/python ]; then
  echo "PROBLEMA: falta el entorno de Python (.venv). QUÉ HACER: doble clic en instalar.command."
  exit 2
fi
exec .venv/bin/python scripts/editor.py "$@"
