"""REVISIÓN DE CADA CORTE del video terminado (como hace un editor antes de entregar).

    .venv/bin/python scripts/revisar_cortes.py salida/X_tv.mp4 trabajo/X_edit.json

1. Imagen: por cada corte, el cuadro de ANTES y el de DESPUÉS, uno al lado del otro -> trabajo/X_cortes.jpg
   (Claude la abre con Read: que no haya saltos raros, caras cortadas ni subtítulos que desaparecen).
2. Sonido: mide si en algún corte quedó un "clic" (un salto brusco de la onda) y dice en qué segundo.
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def clics(video: str, tiempos, sr: int = 48000):
    """Cortes donde la onda salta de golpe (más de 6 veces lo normal alrededor): se oiría un "clic"."""
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-map", "0:a:0", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    x = np.frombuffer(crudo, np.float32)
    malos = []
    for t in tiempos:
        i = int(t * sr)
        cerca = np.abs(np.diff(x[max(0, i - 240) : i + 240]))  # ±5 ms
        lejos = np.abs(np.diff(x[max(0, i - 4800) : i + 4800]))  # ±100 ms
        if cerca.size and lejos.size and cerca.max() > 0.08 and cerca.max() > 6 * (np.percentile(lejos, 99) + 1e-6):
            malos.append(round(t, 2))
    return malos


def principal(video: str, plan: str) -> int:
    with open(plan, encoding="utf-8") as f:
        edit = json.load(f)
    fps = edit["fps"]
    cortes = [sg["from"] / fps for sg in edit["segments"] if sg["from"] > 0]
    if not cortes:
        print("Este video no tiene cortes.")
        return 0
    base = os.path.splitext(plan)[0].replace("_edit", "")
    carpeta = base + "_cortes_tmp"
    os.makedirs(carpeta, exist_ok=True)
    muestra = cortes[:24]
    for n, t in enumerate(muestra):
        for lado, tt in (("a", t - 2 / fps), ("b", t + 2 / fps)):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0, tt):.3f}", "-i", video, "-frames:v", "1",
                            "-vf", "scale=-2:270", os.path.join(carpeta, f"{n:02d}{lado}.jpg")], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(carpeta, f"{n:02d}a.jpg"), "-i", os.path.join(carpeta, f"{n:02d}b.jpg"),
                        "-filter_complex", "hstack,pad=iw+12:ih+12:6:6:white", os.path.join(carpeta, f"par_{n:02d}.jpg")], check=True)
    columnas = 2 if edit["width"] > edit["height"] else 4
    filas = -(-len(muestra) // columnas)
    destino = base + "_cortes.jpg"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", "1", "-i", os.path.join(carpeta, "par_%02d.jpg"),
                    "-vf", f"tile={columnas}x{filas}", "-frames:v", "1", "-update", "1", destino], check=True)
    for a in os.listdir(carpeta):
        os.remove(os.path.join(carpeta, a))
    os.rmdir(carpeta)
    malos = clics(video, cortes)
    print(f"CORTES: {len(cortes)} en total; {len(muestra)} en la imagen {destino} (antes | después de cada corte, en orden).")
    print("  Tiempos: " + ", ".join(f"{t:.1f}" for t in muestra) + " s")
    print("  ✓ Ningún corte suena con clic." if not malos else "  ✗ Posible clic de audio en: " + ", ".join(f"{t} s" for t in malos))
    return 1 if malos else 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    sys.exit(principal(sys.argv[1], sys.argv[2]))
