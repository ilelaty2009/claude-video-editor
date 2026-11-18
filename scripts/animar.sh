#!/usr/bin/env bash
# Animación explicativa desde cero, a partir de una receta JSON. Ejemplos:
#   bash scripts/animar.sh demo/animaciones/palitos_pirata.json
#   bash scripts/animar.sh demo/animaciones/grafica_estudio.json --formato reel --calidad preview
# Todas las opciones: bash scripts/animar.sh --help      (el programa está en scripts/animar.py)
set -uo pipefail
cd "$(dirname "$0")/.."
source scripts/entorno.sh
if [ ! -x .venv/bin/python ]; then
  echo "PROBLEMA: falta el entorno de Python (.venv). QUÉ HACER: doble clic en instalar.command."
  exit 2
fi
exec .venv/bin/python scripts/animar.py "$@"
