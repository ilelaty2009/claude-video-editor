"""Encuentra dónde están las caras en el video (como "Smart Reframe" de DaVinci / "Auto Reframe" de Premiere).

Usa un detector de caras pequeño (Ultra-Light-Fast-Generic-Face-Detector, 1 MB, licencia MIT) con onnxruntime,
que ya está instalado por faster-whisper. No necesita internet.

Qué devuelve (trabajo/X_caras.json):
  - "foco": centro típico de la cara principal (x, y de 0 a 1) -> los zooms apuntan ahí.
  - "recorte_x": dónde recortar un video horizontal para pasarlo a vertical sin cortar la cara (0 a 1).
  - "muestras": cara principal cada N segundos (para revisar).

Uso: python scripts/seguir_cara.py videos/X.mov trabajo/X_caras.json [--cada 1.0]
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(AQUI, "modelos", "cara_rfb320.onnx")
W, H = 320, 240


def nms(cajas, puntajes, umbral=0.3):
    orden = puntajes.argsort()[::-1]
    quedan = []
    while orden.size:
        i = orden[0]
        quedan.append(i)
        xx1 = np.maximum(cajas[i, 0], cajas[orden[1:], 0])
        yy1 = np.maximum(cajas[i, 1], cajas[orden[1:], 1])
        xx2 = np.minimum(cajas[i, 2], cajas[orden[1:], 2])
        yy2 = np.minimum(cajas[i, 3], cajas[orden[1:], 3])
        inter = np.clip(xx2 - xx1, 0, None) * np.clip(yy2 - yy1, 0, None)
        area = lambda b: (b[..., 2] - b[..., 0]) * (b[..., 3] - b[..., 1])
        iou = inter / (area(cajas[i]) + area(cajas[orden[1:]]) - inter + 1e-9)
        orden = orden[1:][iou < umbral]
    return quedan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("salida")
    ap.add_argument("--cada", type=float, default=1.0, help="segundos entre muestras")
    ap.add_argument("--confianza", type=float, default=0.7)
    args = ap.parse_args()

    try:
        import onnxruntime as ort
    except ImportError:
        sys.exit("Falta onnxruntime (viene con faster-whisper). Corre instalar.command.")

    opciones = ort.SessionOptions()
    opciones.log_severity_level = 3  # sin avisos técnicos en pantalla
    sesion = ort.InferenceSession(MODELO, sess_options=opciones, providers=["CPUExecutionProvider"])
    nombre_in = sesion.get_inputs()[0].name

    # fotogramas a 320x240 en RGB crudo (sin deformar: se rellena con negro)
    cmd = [
        "ffmpeg", "-v", "error", "-i", args.video,
        "-vf", f"fps=1/{args.cada},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    crudo = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(crudo) // (W * H * 3)
    cuadros = np.frombuffer(crudo[: n * W * H * 3], np.uint8).reshape(n, H, W, 3)

    # medidas reales del video para quitar el relleno negro
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", args.video], capture_output=True, text=True).stderr
    import re

    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", err)
    vw, vh = (int(m.group(1)), int(m.group(2))) if m else (W, H)
    if re.search(r"rotate\s*:\s*-?(90|270)", err) or re.search(r"rotation of -?(90|270)", err):
        vw, vh = vh, vw
    esc = min(W / vw, H / vh)
    cw, ch = vw * esc / W, vh * esc / H  # parte útil (0-1) dentro del cuadro 320x240
    ox, oy = (1 - cw) / 2, (1 - ch) / 2

    muestras = []
    for k, img in enumerate(cuadros):
        x = ((img.astype(np.float32) - 127.0) / 128.0).transpose(2, 0, 1)[None]
        puntajes, cajas = sesion.run(None, {nombre_in: x})
        p = puntajes[0, :, 1]
        sel = p > args.confianza
        if not sel.any():
            muestras.append({"t": round(k * args.cada, 2), "caras": []})
            continue
        b, s = cajas[0][sel], p[sel]
        caras = []
        for i in nms(b, s):
            c = b[i]
            caras.append({
                "x": round(float(((c[0] + c[2]) / 2 - ox) / cw), 3),
                "y": round(float(((c[1] + c[3]) / 2 - oy) / ch), 3),
                "alto": round(float((c[3] - c[1]) / ch), 3),
            })
        muestras.append({"t": round(k * args.cada, 2), "caras": caras})

    # Cara principal = la que más tiempo aparece, cerca del centro y completa (no cortada en el borde).
    # (Si escogiéramos la más grande, ganaría alguien de espaldas o medio cortado junto a la cámara.)
    todas = [c for m in muestras for c in m.get("caras", [])]
    if todas:
        grupos = {}
        for c in todas:
            grupos.setdefault(min(9, int(c["x"] * 10)), []).append(c)
        def puntaje(g):
            xs = np.median([c["x"] for c in g])
            borde = 0.35 if xs < 0.1 or xs > 0.9 else 1.0
            return len(g) * (1.2 - abs(xs - 0.5)) * borde
        mejor = max(grupos.values(), key=puntaje)
        # suma los vecinos (una cara que se mueve un poco cae en dos grupos)
        cx0 = float(np.median([c["x"] for c in mejor]))
        cerca = [c for c in todas if abs(c["x"] - cx0) < 0.12]
        fx = float(np.median([c["x"] for c in cerca]))
        fy = float(np.median([c["y"] - 0.15 * c["alto"] for c in cerca]))  # a la altura de los ojos
        resultado = {"foco": {"x": round(fx, 3), "y": round(fy, 3)}, "recorte_x": round(fx, 3)}
        con = sum(1 for m in muestras if any(abs(c["x"] - fx) < 0.12 for c in m.get("caras", [])))
    else:
        resultado = {"foco": {"x": 0.5, "y": 0.42}, "recorte_x": 0.5}
        con = 0
    resultado["con_cara"] = f"{con}/{len(muestras)} muestras"
    resultado["muestras"] = muestras
    os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
    json.dump(resultado, open(args.salida, "w", encoding="utf-8"), indent=1)
    print(f"OK: cara en {resultado['con_cara']}, foco x={resultado['foco']['x']} y={resultado['foco']['y']}")


if __name__ == "__main__":
    main()
