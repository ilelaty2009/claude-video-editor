"""Corrección de color automática (como "Auto Color" de DaVinci Resolve), solo con ffmpeg.

Mide el video (brillo promedio, tinte, saturación) y devuelve un filtro de ffmpeg que:
  1. Corrige el balance de blancos (si el salón tiene luz amarilla o azulada, lo neutraliza).
  2. Corrige la exposición (si quedó oscuro u opaco, lo sube; si quedó quemado, lo baja).
  3. Aplica un "look":
       natural  = solo la corrección (colores reales).
       cine     = sombras un poco azul-verdosas y pieles cálidas (el look "teal & orange" de películas y YouTubers).
       calido   = un poco más cálido y suave (bueno para reflexiones y videos emotivos).
       vivo     = más contraste y color (bueno para TikTok).
Uso: python scripts/color_auto.py video.mp4 --look cine   -> imprime el filtro (vacío si --look no)
"""
import argparse
import re
import subprocess


def medir(video):
    cmd = [
        "ffmpeg", "-v", "error", "-i", video,
        "-vf", "fps=1/2,scale=192:-2,signalstats,metadata=print:file=-",
        "-an", "-f", "null", "-",
    ]
    salida = subprocess.run(cmd, capture_output=True, text=True).stdout
    vals = {}
    for clave in ("YAVG", "UAVG", "VAVG", "SATAVG", "YLOW", "YHIGH"):
        nums = [float(x) for x in re.findall(rf"lavfi\.signalstats\.{clave}=([\d.]+)", salida)]
        if nums:
            vals[clave] = sorted(nums)[len(nums) // 2]  # mediana: no la engaña un cuadro raro
    return vals


def filtro(v, look):
    if look == "no" or not v:
        return ""
    partes = []
    # 1) balance de blancos ("mundo gris": en promedio la escena debería ser neutra; U y V neutros = 128)
    du = (v.get("UAVG", 128) - 128) / 128.0  # + = azulado
    dv = (v.get("VAVG", 128) - 128) / 128.0  # + = rojizo/amarillento
    k = 1.6  # qué tanto se corrige (suave: deja algo del ambiente)
    rm = max(-0.25, min(0.25, -dv * k))
    bm = max(-0.25, min(0.25, -du * k))
    if abs(rm) > 0.01 or abs(bm) > 0.01:
        partes.append(f"colorbalance=rm={rm:.3f}:bm={bm:.3f}:gm={-(rm + bm) / 3:.3f}")
    # 2) exposición: solo si de verdad está oscuro o quemado. Entre 85 y 175 se deja igual:
    #    en un salón con pared blanca el promedio sale alto aunque las caras estén bien, y bajarlo las oscurece.
    y = v.get("YAVG", 120)
    if y < 85:
        gamma = min(1.45, (100 / max(y, 20)) ** 0.6)
    elif y > 175:
        gamma = max(0.85, (165 / y) ** 0.5)
    else:
        gamma = 1.0
    contraste = 1.06 if (v.get("YHIGH", 200) - v.get("YLOW", 40)) < 150 else 1.0  # imagen "lavada" -> más contraste
    sat = 1.08 if v.get("SATAVG", 30) < 25 else 1.0
    partes.append(f"eq=gamma={gamma:.3f}:contrast={contraste:.2f}:saturation={sat:.2f}")
    # 3) look
    if look == "cine":
        partes.append("colorbalance=rs=-0.06:gs=0.01:bs=0.08:rh=0.05:gh=0.01:bh=-0.05")
        partes.append("curves=master='0/0.02 0.25/0.21 0.5/0.5 0.75/0.79 1/0.98'")
        partes.append("vibrance=intensity=0.15")
    elif look == "calido":
        partes.append("colorbalance=rm=0.05:bm=-0.05:rh=0.03:bh=-0.03")
        partes.append("curves=master='0/0.04 0.5/0.52 1/0.97'")
    elif look == "vivo":
        partes.append("eq=contrast=1.08:saturation=1.18")
        partes.append("vibrance=intensity=0.2")
    return ",".join(partes)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--look", default="natural", choices=["natural", "cine", "calido", "vivo", "no"])
    ap.add_argument("--detalle", action="store_true", help="muestra las medidas")
    a = ap.parse_args()
    medidas = medir(a.video) if a.look != "no" else {}
    if a.detalle:
        print("medidas:", medidas)
    print(filtro(medidas, a.look))
