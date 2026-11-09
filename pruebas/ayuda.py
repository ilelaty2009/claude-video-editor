"""Utilidades de las pruebas: crear videos y audios sintéticos con ffmpeg (sin personas, sin internet)."""
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))


def carpeta_temporal():
    return tempfile.mkdtemp(prefix="prueba_editor_")


def video_sintetico(ruta, ancho=1620, alto=1080, fps=30, segundos=2.0, con_audio=True):
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size={ancho}x{alto}:rate={fps}:duration={segundos}"]
    if con_audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={segundos}:sample_rate=48000"]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
    if con_audio:
        cmd += ["-c:a", "aac", "-shortest"]
    cmd += [ruta]
    subprocess.run(cmd, check=True)
    return ruta


def audio_sintetico(ruta, db=-30.0, segundos=6.0):
    """Ruido rosa (parecido a voz + música en su reparto de graves y agudos) al volumen pedido."""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anoisesrc=color=pink:duration={segundos}:sample_rate=48000:amplitude=0.5",
         "-af", f"volume={db + 12}dB", "-ac", "2", ruta],
        check=True,
    )
    return ruta
