"""Mide videos y audios (ancho, alto, fps, duración, cuadros, si tiene audio).

Usa ffprobe si está instalado; si no, lee lo que imprime `ffmpeg -i` (el ffmpeg de .venv no trae ffprobe).
Es el ÚNICO lugar donde se leen estos datos: los demás scripts importan `info()`.

Uso suelto: python scripts/medios.py video.mov   -> imprime los datos
"""
import json
import re
import shutil
import subprocess
import sys
from typing import Dict, Optional


class ErrorMedio(Exception):
    """No se pudo leer el archivo (no existe, está dañado o no es un video)."""


def _fps_de_texto(t: str) -> float:
    if "/" in t:
        a, b = t.split("/", 1)
        return float(a) / float(b) if float(b) else 0.0
    return float(t or 0)


def _con_ffprobe(ruta: str) -> Optional[Dict]:
    if not shutil.which("ffprobe"):
        return None
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", ruta],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return None
    d = json.loads(r.stdout or "{}")
    video = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    rot = 0
    if video:
        for sd in video.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(float(sd["rotation"]))
        rot = int(float((video.get("tags") or {}).get("rotate", rot)))
    w, h = (int(video["width"]), int(video["height"])) if video else (0, 0)
    if abs(rot) in (90, 270):
        w, h = h, w
    cuadros = int(video["nb_frames"]) if video and str(video.get("nb_frames", "")).isdigit() else None
    return {
        "ancho": w,
        "alto": h,
        "fps": round(_fps_de_texto(video.get("r_frame_rate", "0")), 3) if video else 0.0,
        "duracion": float(d.get("format", {}).get("duration") or 0),
        "tiene_video": video is not None,
        "tiene_audio": audio is not None,
        "cuadros": cuadros,
        "codec": video.get("codec_name") if video else None,
    }


def _con_ffmpeg(ruta: str) -> Dict:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", ruta], capture_output=True, text=True).stderr
    if "No such file" in err or "Invalid data" in err:
        raise ErrorMedio(f"No pude abrir {ruta}: ¿existe y es un video?")
    m = re.search(r"Stream #.*?Video:.*?(\d{2,5})x(\d{2,5})", err)
    f = re.search(r"Stream #.*?Video:.*?([\d.]+) (?:fps|tbr)", err)
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    w, h = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    if re.search(r"rotate\s*:\s*-?(90|270)", err) or re.search(r"rotation of -?(90|270)", err):
        w, h = h, w
    return {
        "ancho": w,
        "alto": h,
        "fps": float(f.group(1)) if f else 0.0,
        "duracion": int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0.0,
        "tiene_video": m is not None,
        "tiene_audio": re.search(r"Stream #.*?Audio:", err) is not None,
        "cuadros": None,
        "codec": None,
    }


def info(ruta: str) -> Dict:
    datos = _con_ffprobe(ruta) or _con_ffmpeg(ruta)
    if not datos["tiene_video"] and not datos["tiene_audio"]:
        raise ErrorMedio(f"{ruta} no tiene ni video ni audio (¿archivo dañado?).")
    return datos


def contar_cuadros(ruta: str) -> int:
    """Cuenta los cuadros de video de verdad (decodificando el índice, sin re-codificar)."""
    err = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", ruta, "-map", "0:v:0", "-c", "copy", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    m = re.findall(r"frame=\s*(\d+)", err)
    return int(m[-1]) if m else 0


def fps_de_trabajo(fps_original: float) -> int:
    """Cuadros por segundo para preparar el video: los mismos del original (sin inventar cuadros), máximo 60."""
    if fps_original >= 47:
        return 60
    for estandar in (24, 25, 30):
        if abs(fps_original - estandar) < 1.0:
            return estandar
    return 30


if __name__ == "__main__":
    print(json.dumps(info(sys.argv[1]), indent=1, ensure_ascii=False))
