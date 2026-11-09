"""Audio profesional: medir volumen (LUFS y pico real) y masterizar la mezcla final.

- LUFS = volumen "como lo oye una persona". TikTok y YouTube usan -14 LUFS.
- dBTP = pico real (true peak): el punto más alto de la onda, incluso entre muestras. Debe quedar por debajo de -1
  para que nunca sature, ni siquiera cuando TikTok/WhatsApp vuelven a comprimir el audio.

masterizar() ajusta el volumen de la mezcla completa (voz + música + efectos), pone un limitador de pico real
(trabaja a 192 kHz para ver los picos entre muestras), codifica en AAC y VUELVE A MEDIR el archivo final.
Si no cumple, corrige y repite (máximo 4 veces).

Uso suelto: python scripts/audio.py medir archivo.mp4
"""
import re
import subprocess
import sys
from typing import Dict


def medir(ruta: str) -> Dict[str, float]:
    """Volumen integrado (LUFS), pico real (dBTP) y rango de volumen (LU), con el filtro ebur128 de ffmpeg."""
    err = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", ruta, "-map", "0:a:0", "-af", "ebur128=peak=true:framelog=quiet",
         "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    resumen = err[err.rfind("Summary:"):] if "Summary:" in err else err
    i = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", resumen)
    lra = re.search(r"LRA:\s+(-?[\d.]+) LU", resumen)
    pico = re.search(r"True peak:\s+Peak:\s+(-?[\d.]+|-inf) dBFS", resumen)
    if not i:
        raise RuntimeError(f"No pude medir el volumen de {ruta}.")

    def num(m):
        return float("-inf") if m.group(1) == "-inf" else float(m.group(1))

    return {"lufs": num(i), "pico_dbtp": num(pico) if pico else float("nan"), "lra": float(lra.group(1)) if lra else 0.0}


def _procesar(entrada: str, salida: str, ganancia_db: float, techo_dbtp: float, kbps: int) -> None:
    techo = 10 ** (techo_dbtp / 20)
    filtro = (
        f"volume={ganancia_db:.2f}dB,"
        "aresample=192000,"
        f"alimiter=limit={techo:.4f}:attack=1:release=60:level=disabled,"
        "aresample=48000"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", entrada, "-af", filtro, "-c:a", "aac", "-b:a", f"{kbps}k",
         "-ar", "48000", "-ac", "2", salida],
        check=True,
    )


def masterizar(entrada: str, salida: str, lufs: float = -14.0, pico_max: float = -1.0, kbps: int = 192,
               tolerancia: float = 0.5) -> Dict[str, float]:
    """Deja `salida` (AAC) en `lufs` ±tolerancia y con pico real <= pico_max. Devuelve la medida final."""
    antes = medir(entrada)
    if antes["lufs"] <= -60:  # ebur128 da -70 (o -inf) cuando no hay sonido
        raise RuntimeError("La mezcla está en silencio total: no hay nada que masterizar.")
    ganancia = lufs - antes["lufs"]
    techo = pico_max - 1.0  # margen: la compresión AAC sube un poco los picos
    medida = antes
    for _ in range(4):
        _procesar(entrada, salida, ganancia, techo, kbps)
        medida = medir(salida)
        ok_lufs = abs(medida["lufs"] - lufs) <= tolerancia
        ok_pico = medida["pico_dbtp"] <= pico_max
        if ok_lufs and ok_pico:
            break
        if not ok_pico:
            techo -= 0.5
        if not ok_lufs:
            ganancia += lufs - medida["lufs"]
    medida["antes_lufs"] = antes["lufs"]
    medida["antes_pico_dbtp"] = antes["pico_dbtp"]
    return medida


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "medir":
        m = medir(sys.argv[2])
        print(f"{m['lufs']:.1f} LUFS, pico real {m['pico_dbtp']:.1f} dBTP, rango {m['lra']:.1f} LU")
    else:
        print(__doc__)
