"""RECORTE DE LA PERSONA (sin pantalla verde): la persona con fondo transparente, cuadro por cuadro.

Con eso el editor puede poner TÍTULOS DETRÁS DE LA CABEZA (el texto va entre el fondo y la persona) y cambiar el
FONDO (como pantalla verde, desde una toma normal). Usa MODNet (Apache 2.0, 6,6 MB, sin internet).

    .venv/bin/python scripts/recorte_persona.py public/input.mp4 public/persona.webm

Sale un video VP9 con transparencia, del mismo tamaño y fps que el de entrada. La máscara se calcula a ~512 px y se
agranda con suavizado; además se promedia con el cuadro anterior para que el borde no tiemble.
"""
import os
import subprocess
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import medios  # noqa: E402

MODELO = os.path.join(AQUI, "modelos", "persona_modnet.onnx")
URL_MODELO = "https://huggingface.co/Xenova/modnet/resolve/main/onnx/model.onnx"  # Apache 2.0, 25 MB


def asegurar_modelo(avisar=print) -> None:
    """El modelo no va en git (pesa 25 MB): se baja solo la primera vez."""
    if os.path.exists(MODELO) and os.path.getsize(MODELO) > 1_000_000:
        return
    import urllib.request

    avisar("    Bajando el modelo de recorte de personas (25 MB, una sola vez)...")
    tmp = MODELO + ".tmp"
    urllib.request.urlretrieve(URL_MODELO, tmp)
    os.replace(tmp, MODELO)


def tam_modelo(w: int, h: int, lado_corto: int = 384):
    """Tamaño para el modelo: el lado corto a 384 (medido: ~100 ms por cuadro en un M2) y múltiplos de 32."""
    esc = lado_corto / min(w, h)
    return max(32, int(round(w * esc / 32)) * 32), max(32, int(round(h * esc / 32)) * 32)


def recortar(entrada: str, salida: str, suavizado: float = 0.55, avisar=print, desde: float = 0.0, hasta: float = 0.0) -> str:
    """Recorta a la persona de `entrada` (o solo del tramo desde-hasta, en segundos) y escribe `salida` (.webm)."""
    import onnxruntime as ort

    asegurar_modelo(avisar)
    tramo = ["-ss", f"{desde:.3f}"] + (["-to", f"{hasta:.3f}"] if hasta > desde else [])
    d = medios.info(entrada)
    W, H, fps = d["ancho"], d["alto"], d["fps"] or 30
    mw, mh = tam_modelo(W, H)
    opciones = ort.SessionOptions()
    opciones.log_severity_level = 3
    sesion = ort.InferenceSession(MODELO, sess_options=opciones, providers=["CPUExecutionProvider"])
    lector = subprocess.Popen(
        ["ffmpeg", "-v", "error"] + tramo + ["-i", entrada, "-vf", f"scale={mw}:{mh}:flags=bilinear", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE,
    )
    tmp = salida + ".tmp.webm"
    escritor = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error"] + tramo + ["-i", entrada,
         "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{mw}x{mh}", "-r", f"{fps}", "-i", "-",
         "-filter_complex", f"[1:v]scale={W}:{H}:flags=bicubic,erosion,erosion,gblur=sigma=0.8[m];[0:v][m]alphamerge,format=yuva420p[v]",
         "-map", "[v]", "-an", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "30",
         "-deadline", "realtime", "-cpu-used", "8", "-row-mt", "1", "-auto-alt-ref", "0", tmp],
        stdin=subprocess.PIPE,
    )
    anterior = None
    n = 0
    tam = mw * mh * 3
    while True:
        crudo = lector.stdout.read(tam)
        if len(crudo) < tam:
            break
        img = np.frombuffer(crudo, np.uint8).reshape(mh, mw, 3).astype(np.float32)
        x = ((img / 255.0 - 0.5) / 0.5).transpose(2, 0, 1)[None]
        mate = sesion.run(None, {"input": x})[0][0, 0]
        if anterior is not None:  # menos temblor en el borde
            mate = suavizado * mate + (1 - suavizado) * anterior
        anterior = mate
        # borde más firme: quita el halo de la pared que se cuela en el contorno (sobre todo con fondos claros)
        mate = np.clip((mate - 0.18) / 0.72, 0, 1)
        escritor.stdin.write((np.clip(mate, 0, 1) * 255).astype(np.uint8).tobytes())
        n += 1
        if n % 150 == 0:
            avisar(f"    recorte de la persona: {n} cuadros…")
    lector.wait()
    escritor.stdin.close()
    if escritor.wait() != 0:
        raise RuntimeError("ffmpeg no pudo escribir el video con transparencia")
    os.replace(tmp, salida)
    return salida


if __name__ == "__main__":
    print("OK:", recortar(sys.argv[1], sys.argv[2]))
