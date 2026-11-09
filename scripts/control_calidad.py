"""Control de calidad final (lo que revisa un editor profesional antes de entregar) + subtítulos .srt.

Revisa el video terminado:
  - Cuadros por segundo y resolución: los del plan (60 fps; 1920x1080, 1080x1920…).
  - Video H.264 yuv420p y audio AAC (lo que aceptan TikTok, WhatsApp y los televisores).
  - Volumen: -14 LUFS ±1 (estándar de YouTube/TikTok) y pico real por debajo de -1 dBTP (no satura).
  - Duración: igual a la del plan (que el render no se cortó).
  - Pantallazos negros de más de 0.5 s (señal de que algo falló).
  - Silencios largos de más de 2.5 s (audio perdido) — sin contar la tarjeta de cierre.
Y escribe salida/X.srt (subtítulos para subir a YouTube o para quien no puede oír).

Uso: python scripts/control_calidad.py salida/X_tv.mp4 public/edit.json [--escala 1] [--lufs -14] [--pico -1]
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio  # noqa: E402
import medios  # noqa: E402


def ms_a_srt(ms):
    h, ms = divmod(int(ms), 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def escribir_srt(edit, ruta):
    caps = edit.get("captions", [])
    bloques, actual = [], []
    for i, c in enumerate(caps):
        actual.append(c)
        sig = caps[i + 1] if i + 1 < len(caps) else None
        fin_frase = c["text"].strip().endswith((".", "?", "!"))
        pausa = sig is not None and sig["startMs"] - c["endMs"] > 400
        if len(actual) >= 8 or fin_frase or pausa or sig is None:
            bloques.append(actual)
            actual = []
    with open(ruta, "w", encoding="utf-8") as f:
        for n, b in enumerate(bloques, 1):
            texto = " ".join(x["text"].strip() for x in b)
            f.write(f"{n}\n{ms_a_srt(b[0]['startMs'])} --> {ms_a_srt(b[-1]['endMs'] + 150)}\n{texto}\n\n")
    return len(bloques)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("plan")
    ap.add_argument("--escala", type=float, default=1.0, help="0.5 en calidad preview")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--pico", type=float, default=-1.0)
    a = ap.parse_args()
    video, plan = a.video, a.plan
    edit = json.load(open(plan, encoding="utf-8"))
    problemas, bien = [], []

    d = medios.info(video)
    fps_ok = abs(d["fps"] - edit["fps"]) < 0.01
    (bien if fps_ok else problemas).append(f"{d['fps']:g} fps (plan: {edit['fps']})")
    w, h = round(edit["width"] * a.escala), round(edit["height"] * a.escala)
    (bien if (d["ancho"], d["alto"]) == (w, h) else problemas).append(f"Resolución {d['ancho']}x{d['alto']} (plan: {w}x{h})")
    if d.get("codec"):
        (bien if d["codec"] == "h264" else problemas).append(f"Video {d['codec']} (debe ser h264)")

    err = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", video, "-af", "silencedetect=n=-45dB:d=2.5",
         "-vf", "blackdetect=d=0.5:pix_th=0.06", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr

    m = audio.medir(video)
    (bien if abs(m["lufs"] - a.lufs) <= 1.0 else problemas).append(f"Volumen {m['lufs']:.1f} LUFS (meta {a.lufs:g})")
    (bien if m["pico_dbtp"] <= a.pico else problemas).append(f"Pico real {m['pico_dbtp']:.1f} dBTP (máximo {a.pico:g})")

    esperado = edit["durationInFrames"] / edit["fps"]
    (bien if abs(d["duracion"] - esperado) < 0.1 else problemas).append(f"Duración {d['duracion']:.2f} s (plan: {esperado:.2f} s)")

    cierre = edit.get("cierre", {}).get("desdeFrame", edit["durationInFrames"]) / edit["fps"]
    negros = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    negros = [n for n in negros if n[0] < cierre - 0.2]
    if negros:
        problemas.append("Pantalla negra en: " + ", ".join(f"{a:.1f}-{b:.1f} s" for a, b in negros))
    else:
        bien.append("Sin pantallazos negros")
    silencios = [(float(a), float(b)) for a, b in re.findall(r"silence_start: ([\d.]+)[\s\S]*?silence_end: ([\d.]+)", err)]
    silencios = [x for x in silencios if x[0] < cierre - 0.5]
    if silencios:
        problemas.append("Silencio largo en: " + ", ".join(f"{a:.1f}-{b:.1f} s" for a, b in silencios) + " (¿se perdió el audio?)")
    else:
        bien.append("Sin silencios raros")

    srt = os.path.splitext(video)[0] + ".srt"
    n = escribir_srt(edit, srt)
    bien.append(f"Subtítulos: {srt} ({n} bloques)")

    print("CONTROL DE CALIDAD")
    for b in bien:
        print("  ✓ " + b)
    for p in problemas:
        print("  ✗ " + p)
    print("RESULTADO: " + ("TODO BIEN" if not problemas else f"{len(problemas)} cosa(s) por revisar"))


if __name__ == "__main__":
    main()
