"""GRABACIONES DE PANTALLA "CINEMATOGRÁFICAS" (como Screen Studio): zoom automático a donde está pasando algo.

Mira la grabación a baja resolución, busca qué parte cambia (donde escribes, haces clic o se mueve algo) y arma un
recorrido de cámara: se acerca a esa zona, se queda quieta mientras sigue la acción y vuelve a la vista completa
cuando cambia toda la pantalla. Los movimientos son suaves (la escena `pantalla` los interpola con curvas).

    .venv/bin/python scripts/pantalla.py public/broll/mi_grabacion.mp4     -> imprime el recorrido (JSON)

El editor lo hace solo para cada escena {"tipo": "pantalla", "archivo": "broll/mi_grabacion.mp4"} de los extras.
"""
import json
import subprocess
import sys

import numpy as np

ANCHO = 192  # resolución de análisis (rápido y suficiente para saber DÓNDE pasa algo)
FPS = 8


def actividad(ruta: str):
    """Por cada cuadro de análisis: caja (x0, y0, x1, y1 en 0-1) de lo que cambió, o None si nada cambió."""
    crudo = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", ruta, "-vf", f"fps={FPS},scale={ANCHO}:-2,format=gray", "-f", "rawvideo", "-"],
        capture_output=True, check=True,
    ).stdout
    info = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-vf", f"scale={ANCHO}:-2", "-frames:v", "1", "-f", "rawvideo",
                           "-pix_fmt", "gray", "-"], capture_output=True).stdout
    alto = len(info) // ANCHO
    n = len(crudo) // (ANCHO * alto)
    cuadros = np.frombuffer(crudo[: n * ANCHO * alto], np.uint8).reshape(n, alto, ANCHO).astype(np.int16)
    cajas = [None]
    for i in range(1, n):
        dif = np.abs(cuadros[i] - cuadros[i - 1]) > 18
        if dif.sum() < 6:  # casi nada: el cursor quieto, ruido
            cajas.append(None)
            continue
        ys, xs = np.nonzero(dif)
        # ignora píxeles sueltos lejanos (el reloj, una notificación): se queda con el 90 % central de los cambios
        x0, x1 = np.percentile(xs, [5, 95])
        y0, y1 = np.percentile(ys, [5, 95])
        cajas.append((x0 / ANCHO, y0 / alto, (x1 + 1) / ANCHO, (y1 + 1) / alto))
    return cajas, alto / ANCHO


def recorrido(cajas, aspecto: float, zoom_max: float = 2.2, quieto_s: float = 1.2):
    """Convierte las cajas de actividad en puntos de cámara {t, x, y, z}: z = acercamiento (1 = pantalla completa)."""
    puntos = []
    actual = {"x": 0.5, "y": 0.5, "z": 1.0}
    desde = -99.0
    ultima = 0.0  # última vez que pasó algo
    for i, c in enumerate(cajas):
        t = i / FPS
        if c is None:
            # sin acción por 2,5 s: la cámara vuelve a mostrar toda la pantalla
            if actual["z"] > 1.0 and t - ultima >= 2.5 and t - desde >= quieto_s:
                actual = {"x": 0.5, "y": 0.5, "z": 1.0}
                desde = t
                puntos.append({"t": round(t, 2), **actual})
            continue
        ultima = t
        w, h = c[2] - c[0], (c[3] - c[1])
        # tamaño de la zona en "pantallas": si cambia casi todo, mejor vista completa
        tam = max(w, h / max(aspecto, 1e-6) * aspecto)
        z = 1.0 if tam > 0.55 else float(np.clip(0.55 / max(tam, 0.05), 1.0, zoom_max))
        objetivo = {"x": (c[0] + c[2]) / 2, "y": (c[1] + c[3]) / 2, "z": round(z, 2)}
        lejos = abs(objetivo["x"] - actual["x"]) > 0.12 / actual["z"] or abs(objetivo["y"] - actual["y"]) > 0.12 / actual["z"] or abs(objetivo["z"] - actual["z"]) > 0.35
        if lejos and t - desde >= quieto_s:  # no saltar de un lado a otro: cada toma dura al menos 1,2 s
            actual = objetivo
            desde = t
            puntos.append({"t": round(t, 2), **{k: round(v, 3) for k, v in actual.items()}})
    if not puntos or puntos[0]["t"] > 0:
        puntos.insert(0, {"t": 0.0, "x": 0.5, "y": 0.5, "z": 1.0})
    return puntos


def analizar(ruta: str):
    cajas, aspecto = actividad(ruta)
    return recorrido(cajas, aspecto)


if __name__ == "__main__":
    print(json.dumps(analizar(sys.argv[1]), indent=1))
