"""Prepara la PORTADA / miniatura del video (como las de YouTube o la portada de un TikTok).

1. Escoge el mejor fotograma: cara grande, de la persona principal y NÍTIDA (sin movimiento borroso).
2. Lo saca en alta calidad (con la misma corrección de color del video).
3. Escribe public/portada.json con el texto. Luego se dibuja con:
     npx remotion still src/index.ts Portada salida/X_portada.jpg
Texto: en los extras, "portada": {"arriba": "...", "lineas": [{"texto": "...", "color": "#FFC94D"}], "etiqueta": "..."}.
Si no hay, usa el "titulo" o el primer titular del video.

Uso: python scripts/portada.py videos/X.mov trabajo/X_caras.json --extras trabajo/X_extras.json --formato tv|reel|cuadrado|retrato [--color "filtro"]
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import medios  # noqa: E402

# tamaño de la portada por formato (TV = miniatura de YouTube 1280x720)
TAMANOS = {"tv": (1280, 720), "reel": (1080, 1920), "cuadrado": (1080, 1080), "retrato": (1080, 1350)}


def nitidez(video, t, cara):
    """Qué tan nítida está la cara en el segundo t (varianza del Laplaciano: borroso = número bajo)."""
    w, h = 480, 270
    crudo = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1",
         "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,format=gray",
         "-f", "rawvideo", "-"],
        capture_output=True,
    ).stdout
    if len(crudo) < w * h:
        return 0.0
    img = np.frombuffer(crudo[: w * h], np.uint8).reshape(h, w).astype(np.float32)
    lado = max(12, int(cara["alto"] * h * 0.6))
    cx, cy = int(cara["x"] * w), int(cara["y"] * h)
    zona = img[max(0, cy - lado) : cy + lado, max(0, cx - lado) : cx + lado]
    if zona.shape[0] < 5 or zona.shape[1] < 5:
        return 0.0
    lap = zona[1:-1, 1:-1] * 4 - zona[:-2, 1:-1] - zona[2:, 1:-1] - zona[1:-1, :-2] - zona[1:-1, 2:]
    return float(lap.var())


def texto_por_defecto(extras):
    if extras.get("portada"):
        return extras["portada"]
    for e in extras.get("escenas", []):
        if e.get("tipo") == "titular" and e.get("lineas"):
            return {"arriba": e.get("arriba", ""), "lineas": [{"texto": l["texto"], "color": l.get("color")} for l in e["lineas"]]}
    titulo = (extras.get("titulo") or "").strip()
    palabras = titulo.split()
    lineas = [" ".join(palabras[i : i + 2]) for i in range(0, len(palabras), 2)] or ["MI VIDEO"]
    return {"lineas": [{"texto": l, "color": "#FFC94D" if i == len(lineas) - 1 else None} for i, l in enumerate(lineas[:3])]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("caras")
    ap.add_argument("--extras", default="")
    ap.add_argument("--formato", default="tv")
    ap.add_argument("--color", default="", help="filtro de color de ffmpeg (el mismo del video)")
    a = ap.parse_args()

    caras = json.load(open(a.caras, encoding="utf-8")) if os.path.exists(a.caras) else {"foco": {"x": 0.5, "y": 0.4}, "muestras": []}
    fx = caras["foco"]["x"]
    candidatos = []
    for m in caras.get("muestras", []):
        for c in m.get("caras", []):
            if abs(c["x"] - fx) < 0.12:
                candidatos.append((m["t"], c))
    candidatos.sort(key=lambda tc: -tc[1]["alto"])
    candidatos = candidatos[:8]  # las 8 muestras con la cara más grande
    if candidatos:
        puntajes = [(c["alto"] * np.sqrt(nitidez(a.video, t, c) + 1), t, c) for t, c in candidatos]
        _, t_mejor, cara = max(puntajes, key=lambda p: p[0])
    else:
        t_mejor, cara = 1.0, {"x": caras["foco"]["x"], "y": caras["foco"]["y"], "alto": 0.3}

    # Encuadre de miniatura profesional: la cara grande (~45% del alto en TV), a la altura de los ojos,
    # en el lado contrario al texto. Se recorta aquí mismo con ffmpeg.
    ancho, alto = TAMANOS.get(a.formato, TAMANOS["tv"])
    os.makedirs("public/portada", exist_ok=True)
    tmp = "public/portada/_completo.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t_mejor), "-i", a.video, "-frames:v", "1", tmp], check=True)
    d = medios.info(tmp)
    w, h = d["ancho"], d["alto"]
    vertical = alto > ancho
    lado_texto = "izq" if cara["x"] >= 0.5 else "der"
    meta_x = 0.5 if vertical else (0.68 if lado_texto == "izq" else 0.32)
    meta_y = 0.58 if vertical else 0.46  # en vertical el texto va arriba, la cara más abajo
    frac = 0.30 if vertical else 0.45
    aspecto = ancho / alto
    hc = min(h, cara["alto"] * h / frac)
    wc = hc * aspecto
    if wc > w:
        wc, hc = w, w / aspecto
    x0 = min(max(0, cara["x"] * w - meta_x * wc), w - wc)
    y0 = min(max(0, (cara["y"] - 0.12 * cara["alto"]) * h - meta_y * hc), h - hc)
    filtro = f"crop={int(wc)}:{int(hc)}:{int(x0)}:{int(y0)},scale={ancho}:{alto}:flags=lanczos" + ("," + a.color if a.color else "")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-vf", filtro, "-q:v", "2", "public/portada/cuadro.jpg"], check=True)
    os.remove(tmp)
    # dónde quedó la cara dentro de la portada (para el lado del texto)
    foco = {"x": (cara["x"] * w - x0) / wc, "y": ((cara["y"] - 0.12 * cara["alto"]) * h - y0) / hc}

    extras = json.load(open(a.extras, encoding="utf-8")) if a.extras and os.path.exists(a.extras) else {}
    txt = texto_por_defecto(extras)
    datos = {
        "imagen": "portada/cuadro.jpg",
        "ancho": ancho,
        "alto": alto,
        "foco": {"x": round(foco["x"], 3), "y": round(foco["y"], 3)},
        "arriba": txt.get("arriba", ""),
        "lineas": [{k: v for k, v in l.items() if v} for l in txt.get("lineas", [])],
        "etiqueta": txt.get("etiqueta", ""),
        "lado": "izq" if foco["x"] >= 0.5 else "der",
    }
    json.dump(datos, open("public/portada.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"OK: portada con el fotograma del segundo {t_mejor} ({len(candidatos)} candidatos revisados)")


if __name__ == "__main__":
    main()
