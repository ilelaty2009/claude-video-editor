"""SINCRONÍA DE SUBTÍTULOS: mide si las palabras caen justo donde suena la voz y, si están corridas, las re-sincroniza.

Compara dos "dibujos" a lo largo del tiempo: dónde HAY VOZ de verdad (energía del audio) y dónde DICE la
transcripción que hay palabras. Prueba correrlos entre -400 y +400 ms y se queda con el desfase donde mejor calzan.

    .venv/bin/python scripts/sincronia.py voz.wav transcripcion.json     -> imprime el desfase medido

Uso en el editor (automático): si el desfase pasa de 120 ms, todas las palabras se corren esa cantidad.
Si Pablo dice "los subtítulos van adelantados/atrasados", corre el editor con --resincronizar (lo vuelve a medir) o
pon "desfaseSubtitulos": ms en los extras (positivo = más tarde).
"""
import json
import subprocess
import sys

import numpy as np

PASO = 0.01  # 10 ms
UMBRAL_MS = 120  # por debajo de esto no se toca (Whisper ya tiene ±50 ms de imprecisión por palabra)


def envolvente(ruta: str) -> np.ndarray:
    """Energía de la voz cada 10 ms (0-1)."""
    sr = 16000
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-map", "0:a:0", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    x = np.frombuffer(crudo, np.float32)
    n = int(sr * PASO)
    cuadros = len(x) // n
    if cuadros == 0:
        return np.zeros(0)
    e = np.sqrt(np.mean(x[: cuadros * n].reshape(cuadros, n) ** 2, axis=1))
    return e / max(1e-9, float(np.percentile(e, 98)))


def desfase_ms(env: np.ndarray, palabras, max_ms: int = 400) -> float:
    """Cuántos ms hay que CORRER las palabras para que calcen con la voz (positivo = más tarde)."""
    if len(env) == 0 or not palabras:
        return 0.0
    habla = (env > 0.12).astype(np.float32)  # hay voz
    mascara = np.zeros(len(env), np.float32)
    for w in palabras:
        mascara[max(0, int(w["start"] / PASO)) : min(len(env), int(w["end"] / PASO))] = 1
    habla -= habla.mean()
    mascara -= mascara.mean()
    pasos = int(max_ms / 1000 / PASO)
    mejor, mejor_valor = 0, -1e18
    valores = {}
    for d in range(-pasos, pasos + 1):
        v = float(np.dot(habla[max(0, d) : len(env) + min(0, d)], mascara[max(0, -d) : len(env) - max(0, d)]))
        valores[d] = v
        if v > mejor_valor:
            mejor, mejor_valor = d, v
    # afinado: parábola con los vecinos (precisión menor a 10 ms)
    if -pasos < mejor < pasos:
        a, b, c = valores[mejor - 1], valores[mejor], valores[mejor + 1]
        den = a - 2 * b + c
        if den < 0:
            return round((mejor + 0.5 * (a - c) / den) * PASO * 1000, 1)
    return round(mejor * PASO * 1000, 1)


def correr_palabras(palabras, ms: float):
    for w in palabras:
        w["start"] = round(max(0.0, w["start"] + ms / 1000), 3)
        w["end"] = round(max(0.0, w["end"] + ms / 1000), 3)
    return palabras


def revisar(ruta_voz: str, ruta_transcripcion: str, forzar: bool = False) -> dict:
    """Mide el desfase y, si hace falta, corrige la transcripción (una sola vez: queda anotado en el archivo)."""
    with open(ruta_transcripcion, encoding="utf-8") as f:
        t = json.load(f)
    if "sincroniaMs" in t and not forzar:
        return {"desfase": t.get("desfaseMedidoMs", 0.0), "corregido": t["sincroniaMs"], "nuevo": False}
    d = desfase_ms(envolvente(ruta_voz), t["words"])
    corregido = d if abs(d) >= UMBRAL_MS else 0.0
    if corregido:
        correr_palabras(t["words"], corregido)
    t["desfaseMedidoMs"] = d
    t["sincroniaMs"] = t.get("sincroniaMs", 0.0) + corregido if forzar else corregido
    with open(ruta_transcripcion, "w", encoding="utf-8") as f:
        json.dump(t, f, ensure_ascii=False, indent=1)
    return {"desfase": d, "corregido": corregido, "nuevo": True}


if __name__ == "__main__":
    with open(sys.argv[2], encoding="utf-8") as f:
        palabras = json.load(f)["words"]
    print(f"Desfase medido: {desfase_ms(envolvente(sys.argv[1]), palabras):+.0f} ms (positivo = las palabras deberían ir más tarde)")
