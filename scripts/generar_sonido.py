"""GENERADOR DE SONIDOS que le falten a tu pack (hechos con matemáticas: libres de derechos, sin internet).

    .venv/bin/python scripts/generar_sonido.py swipe                 -> public/sfx/swipe.wav
    .venv/bin/python scripts/generar_sonido.py chime --nombre logro  -> public/sfx/propios/logro.wav
    .venv/bin/python scripts/generar_sonido.py todos                 -> los 7 tipos en public/sfx/

Tipos: impacto (golpe grave), swipe (deslizar), glitch (falla digital), blip (aviso corto), tap (toque),
snap (chasquido) y chime (campanita). Cada uno se iguala al volumen del pack (mismo pico que los demás sonidos),
para que ninguno suene más fuerte que el resto. `--semilla N` da una variación distinta.

TUS PROPIOS SONIDOS: ponlos en public/sfx/propios/ con el nombre de lo que suenan (whoosh.wav, pop.wav, ding.wav…):
el editor los usa en vez de los de fábrica (prioridad: propios > reales de Openverse > sintetizados).
"""
import argparse
import os
import sys
import wave

import numpy as np

SR = 44100
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX = os.path.join(RAIZ, "public", "sfx")
TIPOS = ("impacto", "swipe", "glitch", "blip", "tap", "snap", "chime")


def _t(seg: float) -> np.ndarray:
    return np.arange(int(SR * seg)) / SR


def _pasa(x: np.ndarray, bajo: float, alto: float) -> np.ndarray:
    """Filtro pasa-banda sencillo en frecuencia."""
    f = np.fft.rfft(x)
    hz = np.fft.rfftfreq(len(x), 1 / SR)
    f[(hz < bajo) | (hz > alto)] = 0
    return np.fft.irfft(f, len(x))


def sintetizar(tipo: str, semilla: int = 1) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    if tipo == "impacto":  # golpe grave que cae de tono + un "clic" de ataque
        t = _t(0.6)
        cuerpo = np.sin(2 * np.pi * (55 * t + 60 * (1 - np.exp(-t * 18)) / 18)) * np.exp(-t * 7)
        return cuerpo + _pasa(rng.standard_normal(len(t)), 800, 5000) * np.exp(-t * 90) * 0.5
    if tipo == "swipe":  # ruido que sube y baja de tono y volumen (algo que pasa rápido)
        t = _t(0.32)
        ruido = rng.standard_normal(len(t))
        partes = [_pasa(ruido, 600 + 900 * i, 1800 + 1500 * i) * np.exp(-((t - 0.06 - 0.04 * i) ** 2) / 0.0035) for i in range(5)]
        return np.sum(partes, axis=0)
    if tipo == "glitch":  # pedacitos de ruido y tonos cuadrados cortados (falla digital)
        t = _t(0.3)
        x = np.zeros(len(t))
        pos = 0
        while pos < len(t):
            largo = int(SR * rng.uniform(0.008, 0.035))
            tramo = slice(pos, min(len(t), pos + largo))
            if rng.random() < 0.7:
                f = rng.choice([220, 440, 880, 1760, 3520])
                x[tramo] = np.sign(np.sin(2 * np.pi * f * t[tramo])) * rng.uniform(0.4, 1)
            else:
                x[tramo] = rng.standard_normal(tramo.stop - tramo.start) * 0.8
            pos += largo + int(SR * rng.uniform(0, 0.012))
        return x * np.exp(-t * 6)
    if tipo == "blip":  # dos notitas que suben (aviso de interfaz)
        t = _t(0.16)
        f = np.where(t < 0.07, 880, 1320)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-((t % 0.07) * 28)) * (t < 0.15)
    if tipo == "tap":  # toque seco y corto
        t = _t(0.05)
        return np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 160) + _pasa(rng.standard_normal(len(t)), 2000, 9000) * np.exp(-t * 300) * 0.4
    if tipo == "snap":  # chasquido: ruido agudo con ataque instantáneo
        t = _t(0.09)
        return _pasa(rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t * 85)
    if tipo == "chime":  # campanita: varios armónicos que se apagan lento
        t = _t(1.2)
        return sum(np.sin(2 * np.pi * 1046.5 * m * t) * np.exp(-t * (3 + 2.2 * i)) * a for i, (m, a) in enumerate([(1, 1), (2.01, 0.5), (3.02, 0.3), (4.2, 0.15)]))
    raise ValueError(f"Tipo desconocido: {tipo}. Usa uno de: {', '.join(TIPOS)}")


def pico_del_pack() -> float:
    """Pico típico (mediana) de los sonidos que ya hay, para que el nuevo suene igual de fuerte."""
    picos = []
    for a in os.listdir(SFX) if os.path.isdir(SFX) else []:
        if a.endswith(".wav"):
            with wave.open(os.path.join(SFX, a)) as w:
                x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
                if x.size:
                    picos.append(float(np.abs(x).max()) / 32768)
    return float(np.median(picos)) if picos else 0.7


def generar(tipo: str, destino: str, semilla: int = 1) -> str:
    x = sintetizar(tipo, semilla).astype(np.float64)
    rampa = int(SR * 0.003)  # sin "clic" al empezar ni al terminar
    x[:rampa] *= np.linspace(0, 1, rampa)
    x[-rampa:] *= np.linspace(1, 0, rampa)
    x = x / max(1e-9, np.abs(x).max()) * min(0.95, pico_del_pack())
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with wave.open(destino, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    return destino


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera un sonido que le falte a tu pack.")
    ap.add_argument("tipo", choices=TIPOS + ("todos",))
    ap.add_argument("--nombre", default="", help="nombre propio: queda en public/sfx/propios/<nombre>.wav")
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--reemplazar", action="store_true", help="sobrescribe el sonido si ya existe")
    a = ap.parse_args()
    hechos = []
    for tipo in (TIPOS if a.tipo == "todos" else (a.tipo,)):
        destino = os.path.join(SFX, "propios", a.nombre + ".wav") if a.nombre else os.path.join(SFX, tipo + ".wav")
        if os.path.exists(destino) and not a.reemplazar:
            print(f"(Ya existe {os.path.relpath(destino, RAIZ)}: no lo toco. Usa --reemplazar o --nombre otro.)")
            continue
        hechos.append(os.path.relpath(generar(tipo, destino, a.semilla), RAIZ))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import oido

    oido.picos(SFX)  # vuelve a medir dónde está el golpe de cada sonido (para alinearlos al cuadro exacto)
    print("OK: " + (", ".join(hechos) or "nada nuevo"))
