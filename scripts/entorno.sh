# Pone en el PATH las herramientas que instaló instalar.command (Node portátil, ffmpeg de .venv).
# Uso: source scripts/entorno.sh
_RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
if [ -d "$_RAIZ/.tools/node/bin" ]; then
  export PATH="$_RAIZ/.tools/node/bin:$PATH"
fi
if [ -d "$_RAIZ/.venv/bin" ]; then
  export PATH="$_RAIZ/.venv/bin:$PATH"
fi
unset _RAIZ
# Descargas de modelos de Whisper por HTTP normal (el sistema Xet se traba en algunas redes)
export HF_HUB_DISABLE_XET=1
export HF_HUB_DISABLE_TELEMETRY=1
