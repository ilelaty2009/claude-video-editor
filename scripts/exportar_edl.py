"""EXPORTAR LOS CORTES a un editor profesional (DaVinci Resolve —gratis—, Premiere, Final Cut).

    .venv/bin/python scripts/exportar_edl.py trabajo/X_edit.json videos/X.mov [salida/X.edl]

Escribe un archivo .edl (formato CMX3600, el estándar que leen todos los editores) con los cortes que hizo el
editor: silencios, repeticiones y muletillas ya quitados. Sirve para seguir editando a mano a partir del "corte
grueso". En DaVinci: File → Import → Timeline → Pre-conform EDL (y enlazar el video original).
Solo lleva los cortes (video + audio); subtítulos, escenas, música y efectos no viajan en un EDL.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import medios  # noqa: E402


def tc(cuadros: int, fps: int) -> str:
    """Código de tiempo HH:MM:SS:CC (sin "drop frame")."""
    s, c = divmod(int(cuadros), fps)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}:{c:02d}"


def a_edl(edit: dict, clip: str, fps_fuente: int) -> str:
    """Los segmentos del plan (en cuadros del plan) pasados a cuadros del video original."""
    k = fps_fuente / edit["fps"]
    lineas = [f"TITLE: {os.path.splitext(os.path.basename(clip))[0]}", "FCM: NON-DROP FRAME", ""]
    destino = 0
    for n, sg in enumerate(edit["segments"], 1):
        ini = round(sg["trimBefore"] * k)
        dur = max(1, round(sg["durationInFrames"] * k))
        lineas.append(f"{n:03d}  AX       AA/V  C        {tc(ini, fps_fuente)} {tc(ini + dur, fps_fuente)} {tc(destino, fps_fuente)} {tc(destino + dur, fps_fuente)}")
        lineas.append(f"* FROM CLIP NAME: {os.path.basename(clip)}")
        lineas.append("")
        destino += dur
    return "\n".join(lineas)


def exportar(plan: str, video: str, destino: str = "") -> str:
    with open(plan, encoding="utf-8") as f:
        edit = json.load(f)
    fps = medios.fps_de_trabajo(medios.info(video)["fps"])
    destino = destino or os.path.splitext(plan)[0].replace("_edit", "") + ".edl"
    with open(destino, "w", encoding="utf-8") as f:
        f.write(a_edl(edit, video, fps))
    return destino


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    print("OK: cortes exportados a", exportar(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
