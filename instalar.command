#!/bin/bash
# Instalador del editor de videos de Pablo (doble clic para correrlo).
# No usa Homebrew ni GitHub y no pide contraseña:
#   Node     -> nodejs.org (portátil, dentro de esta carpeta)
#   Python   -> el de Apple (Herramientas de línea de comandos)
#   ffmpeg + Whisper -> pypi.org (dentro de .venv)
#   Modelo de voz -> huggingface.co
cd "$(dirname "$0")"
clear
echo "=============================================="
echo "  Instalando tu editor de videos con Claude"
echo "  (tarda 5-15 min la primera vez)"
echo "=============================================="
echo

fallar() {
  echo
  echo "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  echo "  ERROR: $1"
  echo "  Tómale un pantallazo y mándaselo a Claude."
  echo "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  read -n 1 -s -r -p "Presiona cualquier tecla para cerrar..."
  exit 1
}

# 0) Revisar internet: estas páginas tienen que abrir
echo ">> Revisando la conexión..."
BLOQUEADOS=""
for h in nodejs.org pypi.org files.pythonhosted.org registry.npmjs.org huggingface.co storage.googleapis.com; do
  if curl -s -o /dev/null --max-time 15 "https://$h"; then
    echo "   OK  $h"
  else
    echo "   NO  $h"
    BLOQUEADOS="$BLOQUEADOS $h"
  fi
done
if [ -n "$BLOQUEADOS" ]; then
  fallar "Esta red bloquea:$BLOQUEADOS
  Prueba con otra red (la de tu casa o datos del celular) y vuelve a abrir instalar.command."
fi

# 1) Python (viene con las Herramientas de línea de comandos de Apple)
echo ">> Revisando Python..."
if ! xcode-select -p >/dev/null 2>&1; then
  echo "   Falta una herramienta de Apple. Se va a abrir una ventana: dale a 'Instalar'."
  xcode-select --install >/dev/null 2>&1 || true
  fallar "Cuando termine la instalación de Apple, vuelve a abrir instalar.command."
fi
PY="$(command -v python3)"
"$PY" -c "import sys; assert sys.version_info >= (3, 9)" 2>/dev/null || fallar "Python 3.9 o más nuevo no encontrado."
echo "   $("$PY" --version)"

# 2) Node (portátil, se guarda en .tools/node)
if [ -x .tools/node/bin/node ]; then
  echo ">> Node ya está instalado"
else
  echo ">> Descargando Node desde nodejs.org..."
  case "$(uname -m)" in arm64) ARQ=arm64;; *) ARQ=x64;; esac
  ARCHIVO="$(curl -fsSL https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt | awk '{print $2}' | grep "darwin-$ARQ.tar.gz$")" \
    || fallar "No se pudo leer la lista de versiones de Node."
  mkdir -p .tools
  curl -fL --progress-bar "https://nodejs.org/dist/latest-v22.x/$ARCHIVO" -o .tools/node.tgz || fallar "No se pudo descargar Node."
  rm -rf .tools/node && mkdir -p .tools/node
  tar -xzf .tools/node.tgz -C .tools/node --strip-components=1 || fallar "No se pudo descomprimir Node."
  rm -f .tools/node.tgz
fi
export PATH="$PWD/.tools/node/bin:$PATH"
node -v >/dev/null 2>&1 || fallar "Node no funciona."
echo "   Node $(node -v)"

# 3) Whisper + ffmpeg (dentro de .venv)
echo ">> Instalando Whisper y ffmpeg..."
[ -d .venv ] || "$PY" -m venv .venv || fallar "No se pudo crear el entorno de Python."
.venv/bin/pip install --quiet --upgrade pip || fallar "No se pudo actualizar pip."
.venv/bin/pip install --quiet faster-whisper numpy imageio-ffmpeg || fallar "No se pudo instalar Whisper/ffmpeg."
FF="$(.venv/bin/python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" || fallar "No se encontró ffmpeg."
chmod +x "$FF" 2>/dev/null || true
ln -sf "$FF" .venv/bin/ffmpeg
export PATH="$PWD/.venv/bin:$PATH"
ffmpeg -version >/dev/null 2>&1 || fallar "ffmpeg no funciona."
echo "   $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"

echo ">> Descargando el modelo de voz (unos 460 MB, una sola vez)..."
# Descarga normal por HTTP (el sistema "Xet" se traba en algunas redes) y con barra de progreso.
export HF_HUB_DISABLE_XET=1
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DOWNLOAD_TIMEOUT=60
for intento in 1 2 3; do
  .venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-small')" && break
  echo "   (se cortó la descarga, reintento $intento de 3...)"
  sleep 5
done
.venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8'); print('   modelo OK')" \
  || fallar "No se pudo descargar el modelo de voz. Revisa que el hotspot siga prendido y vuelve a abrir instalar.command."

# 4) Remotion
echo ">> Instalando Remotion..."
npm install --no-audit --no-fund || fallar "No se pudo instalar Remotion."

echo ">> Descargando el navegador que usa Remotion para renderizar..."
npx remotion browser ensure >/dev/null 2>&1 || fallar "No se pudo descargar el navegador de Remotion."
echo "   navegador OK"

# 5) Skills oficiales de Remotion para Claude (opcional, usan GitHub)
echo ">> Instalando las skills de Remotion para Claude (opcional)..."
npx -y skills add remotion-dev/skills -a claude-code -s '*' -y --copy >/dev/null 2>&1 \
  && echo "   skills OK" \
  || echo "   (no se pudieron instalar; no pasa nada, el editor funciona igual)"

# 6) Prueba final
echo ">> Probando que todo funcione..."
chmod +x scripts/*.sh
npx remotion compositions src/index.ts >/dev/null 2>&1 || fallar "Remotion no arrancó."
echo "   Remotion OK"

echo
echo "=============================================="
echo "  TODO LISTO :)"
echo "  Ahora abre Claude -> pestaña Code -> esta carpeta,"
echo "  y pídele que edite un video de la carpeta videos/."
echo "=============================================="
read -n 1 -s -r -p "Presiona cualquier tecla para cerrar..."
