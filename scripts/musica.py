"""Compositor de música de fondo ORIGINAL (sin derechos de autor: la genera este programa, nota por nota).

Hace una pista del largo exacto del video, con intro, cuerpo y final, en uno de estos ánimos:
  calma     piano suave + colchón de acordes, 72 bpm       (clase, explicaciones, reflexiones)
  lofi      acordes de jazz, beat relajado con swing, 80 bpm (YouTube, estudio, vlogs)
  energia   beat bailable, bajo marcado, 118 bpm            (TikTok, deportes, emprendimiento)
  epica     cuerdas grandes y tambores, 88 bpm              (historia, documental, momentos importantes)

Solo usa numpy (ya está instalado). Cada video recibe una variación distinta (semilla).
Uso: python scripts/musica.py --animo lofi --duracion 63.5 --salida public/musica/auto.wav [--semilla 7]
"""
import argparse
import wave

import numpy as np

SR = 44100

# progresiones (en semitonos desde DO central = 60). Cada acorde dura 1 compás (4 tiempos).
ANIMOS = {
    "calma": {"bpm": 72, "raiz": 60, "prog": [[0, 4, 7, 11], [7, 11, 14, 17], [9, 12, 16, 19], [5, 9, 12, 16]], "bateria": None},
    "lofi": {"bpm": 80, "raiz": 62, "prog": [[0, 3, 7, 10, 14], [5, 9, 12, 15, 19], [-2, 2, 5, 9, 12], [3, 7, 10, 14, 17]], "bateria": "lofi"},
    "energia": {"bpm": 118, "raiz": 57, "prog": [[0, 3, 7], [-4, 0, 3], [3, 7, 10], [-2, 2, 5]], "bateria": "energia"},
    "epica": {"bpm": 88, "raiz": 57, "prog": [[0, 3, 7], [-4, 0, 3], [3, 7, 10], [-2, 2, 5]], "bateria": "epica"},
}


def hz(nota):
    return 440.0 * 2 ** ((nota - 69) / 12)


def env_adsr(n, a, d, s, r):
    """Envolvente de volumen (ataque, caída, sostenido, relajación) en muestras."""
    e = np.full(n, s, dtype=np.float32)
    a, d, r = min(a, n), min(d, max(0, n - a)), min(r, n)
    e[:a] = np.linspace(0, 1, a, endpoint=False) if a else e[:a]
    if d:
        e[a : a + d] = np.linspace(1, s, d, endpoint=False)
    if r:
        e[n - r :] *= np.linspace(1, 0, r)
    return e


def colchon(f, dur, rng):
    """Colchón tipo sintetizador: varias ondas un poco desafinadas (suena ancho y suave)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n, dtype=np.float32)
    for det in (-0.08, 0.0, 0.07):
        ff = f * 2 ** (det / 12)
        fase = rng.uniform(0, 2 * np.pi)
        for k, amp in ((1, 1.0), (2, 0.35), (3, 0.18), (4, 0.08)):
            x += amp * np.sin(2 * np.pi * ff * k * t + fase * k)
    return x / 5 * env_adsr(n, int(0.6 * SR), int(0.4 * SR), 0.8, int(0.5 * SR))


def piano(f, dur, vel=1.0):
    """Nota tipo piano/pluck: armónicos que se apagan rápido."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n, dtype=np.float32)
    for k, (amp, caida) in enumerate(((1.0, 2.5), (0.5, 4), (0.25, 6), (0.12, 8), (0.06, 10)), start=1):
        x += amp * np.sin(2 * np.pi * f * k * t) * np.exp(-caida * t)
    ataque = np.minimum(1, t / 0.004)
    return vel * x * ataque / 2.2


def bajo(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return (x * env_adsr(n, int(0.01 * SR), int(0.2 * SR), 0.7, int(0.08 * SR)) / 1.3).astype(np.float32)


def bombo(vel=1.0):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 45 + 90 * np.exp(-30 * t)
    return (vel * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-9 * t)).astype(np.float32)


def ruido_filtrado(n, rng, bajo_hz, alto_hz):
    r = rng.standard_normal(n).astype(np.float32)
    F = np.fft.rfft(r)
    fr = np.fft.rfftfreq(n, 1 / SR)
    F[(fr < bajo_hz) | (fr > alto_hz)] = 0
    return np.fft.irfft(F, n).astype(np.float32)


def platillo(rng, vel=1.0, largo=0.05):
    n = int(largo * SR)
    x = ruido_filtrado(n, rng, 7000, 16000)
    return vel * x / (np.abs(x).max() + 1e-9) * np.exp(-np.arange(n) / SR * 60)


def palmada(rng, vel=1.0):
    n = int(0.2 * SR)
    x = ruido_filtrado(n, rng, 900, 5000)
    return vel * x / (np.abs(x).max() + 1e-9) * np.exp(-np.arange(n) / SR * 22)


def tambor_grave(vel=1.0):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = 70 + 40 * np.exp(-12 * t)
    return (vel * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-4 * t)).astype(np.float32)


def poner(pista, sonido, inicio):
    i = int(inicio * SR)
    if i >= len(pista):
        return
    j = min(len(pista), i + len(sonido))
    pista[i:j] += sonido[: j - i]


def filtro_pasabajos(x, corte):
    F = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    F *= 1 / np.sqrt(1 + (fr / corte) ** 4)
    return np.fft.irfft(F, len(x)).astype(np.float32)


def reverb(x, rng, segundos=2.2, mezcla=0.25):
    """Reverberación (como un salón grande): convolución con ruido que se apaga."""
    n = int(segundos * SR)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / SR * (6.9 / segundos))
    ir = filtro_pasabajos(ir, 5000)
    ir /= np.sqrt((ir**2).sum()) + 1e-9
    m = len(x) + n
    tam = 1 << (m - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, tam) * np.fft.rfft(ir, tam), tam)[: len(x)].astype(np.float32)
    return (1 - mezcla) * x + mezcla * y


def componer(animo, duracion, semilla):
    cfg = ANIMOS[animo]
    rng = np.random.default_rng(semilla)
    bpm = cfg["bpm"] * rng.uniform(0.97, 1.03)
    tiempo = 60 / bpm
    compas = 4 * tiempo
    total = duracion + 2.5
    n = int(total * SR)
    armonia = np.zeros(n, np.float32)
    melodia = np.zeros(n, np.float32)
    graves = np.zeros(n, np.float32)
    bateria = np.zeros(n, np.float32)
    prog = cfg["prog"][rng.integers(len(cfg["prog"])) :] + cfg["prog"][: rng.integers(len(cfg["prog"]))] or cfg["prog"]
    raiz = cfg["raiz"] + int(rng.choice([-2, 0, 0, 2]))
    n_compases = int(np.ceil(total / compas))
    intro, final = 2, 2  # compases sin batería al inicio y al final (entra y sale suave)

    for c in range(n_compases):
        t0 = c * compas
        acorde = [raiz + x for x in prog[c % len(prog)]]
        # colchón de acordes
        if animo != "energia" or c % 2 == 0:
            for nota in acorde:
                fuerza = {"calma": 0.22, "lofi": 0.24, "energia": 0.3, "epica": 0.34}[animo]
                poner(armonia, colchon(hz(nota), compas * (2 if animo == "energia" else 1) + 0.6, rng) * fuerza, t0)
                if animo == "epica":  # cuerdas una octava abajo: suena más grande
                    poner(armonia, colchon(hz(nota - 12), compas + 0.6, rng) * 0.16, t0)
        # bajo
        if animo in ("lofi", "energia", "epica") and c >= 1:
            pasos = [0, 2.5] if animo == "lofi" else ([0, 1, 2, 3] if animo == "energia" else [0])
            for p in pasos:
                largo = tiempo * (0.9 if animo == "energia" else 1.8)
                octava = 24 if animo == "epica" else 12
                poner(graves, bajo(hz(acorde[0] - octava), largo) * (0.22 if animo == "epica" else 0.3), t0 + p * tiempo)
        # melodía / arpegio de piano
        if animo in ("calma", "lofi", "epica", "energia"):
            notas = sorted(acorde)
            patron = rng.permutation(len(notas))
            for k in range(8):
                if animo == "epica" and k % 2:
                    continue
                if animo != "energia" and rng.random() < (0.25 if animo == "lofi" else 0.12):
                    continue  # silencios: suena más humano
                nota = notas[patron[k % len(notas)]] + 12 * (1 if animo != "epica" else 0)
                if animo == "energia":  # arpegio rítmico y parejo
                    poner(melodia, piano(hz(notas[k % len(notas)] + 12), 0.5) * 0.26, t0 + k * tiempo / 2)
                    continue
                swing = 0.08 * tiempo if (animo == "lofi" and k % 2) else 0
                vel = rng.uniform(0.55, 0.9)
                poner(melodia, piano(hz(nota), 1.6) * 0.32 * vel, t0 + k * tiempo / 2 + swing)
        # batería
        estilo = cfg["bateria"]
        if estilo and intro <= c < n_compases - final:
            for b in range(4):
                tb = t0 + b * tiempo
                if estilo == "lofi":
                    if b in (0, 2):
                        poner(bateria, bombo(0.55), tb + (0.03 if b == 2 else 0))
                    if b in (1, 3):
                        poner(bateria, palmada(rng, 0.28), tb)
                    for s in range(2):
                        poner(bateria, platillo(rng, 0.18 if s == 0 else 0.1), tb + s * tiempo / 2 + (0.09 * tiempo if s else 0))
                elif estilo == "energia":
                    poner(bateria, bombo(0.6), tb)
                    if b in (1, 3):
                        poner(bateria, palmada(rng, 0.45), tb)
                    poner(bateria, platillo(rng, 0.22, 0.04), tb + tiempo / 2)
                elif estilo == "epica":
                    if b == 0 or (b == 2 and c % 2):
                        poner(bateria, tambor_grave(0.55), tb)
                    if b == 3 and c % 4 == 3:
                        for r in range(3):
                            poner(bateria, tambor_grave(0.5), tb + r * tiempo / 3)

    if animo == "lofi":
        armonia = filtro_pasabajos(armonia, 2200)
        melodia = filtro_pasabajos(melodia, 3200)
        vinilo = ruido_filtrado(n, rng, 2000, 9000) * 0.004
        bateria += vinilo
    mezcla = reverb(armonia + melodia, rng, 2.8 if animo in ("calma", "epica") else 1.6, 0.35) + graves + bateria * 0.8
    mezcla = mezcla[: int(duracion * SR)]
    # quita graves inútiles (< 40 Hz): en parlantes de TV solo ensucian y le roban volumen a la voz
    F = np.fft.rfft(mezcla)
    fr = np.fft.rfftfreq(len(mezcla), 1 / SR)
    F *= 1 / np.sqrt(1 + (40 / np.maximum(fr, 1)) ** 4)
    mezcla = np.fft.irfft(F, len(mezcla)).astype(np.float32)
    # fundido de entrada y salida
    fi, fo = int(1.5 * SR), int(2.5 * SR)
    mezcla[:fi] *= np.linspace(0, 1, fi)
    mezcla[-fo:] *= np.linspace(1, 0, fo)
    # volumen parejo y sin saturar (compresión suave tipo "tanh")
    mezcla /= np.percentile(np.abs(mezcla), 99.5) + 1e-9
    mezcla = np.tanh(mezcla * 0.9) * 0.7
    estereo = np.stack([mezcla, np.roll(mezcla, int(0.012 * SR))], axis=1)  # algo de amplitud estéreo
    return estereo


def guardar(audio, ruta):
    datos = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(datos.tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--animo", default="calma", choices=sorted(ANIMOS))
    ap.add_argument("--duracion", type=float, required=True, help="segundos")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--semilla", type=int, default=None, help="misma semilla = misma canción")
    a = ap.parse_args()
    semilla = a.semilla if a.semilla is not None else int(np.random.default_rng().integers(1_000_000))
    import os

    os.makedirs(os.path.dirname(os.path.abspath(a.salida)), exist_ok=True)
    guardar(componer(a.animo, a.duracion, semilla), a.salida)
    print(f"OK: música '{a.animo}' de {a.duracion:.1f} s (semilla {semilla}) -> {a.salida}")
