"""MEZCLA DE AUDIO del video final, hecha directo desde el plan (public/edit.json), en segundos.

Hace lo mismo que el audio de src/Edit.tsx (lo que se oye en `npm run studio`):
  - VOZ: cada tramo del video con un fundido de 2 cuadros de diseño al entrar y al salir (sin "clics" en los cortes).
  - EFECTOS: cada cue al cuadro exacto, con su volumen y recorte, máximo 3,2 s.
  - MÚSICA: en bucle, con DUCKING: baja sola cuando alguien habla (volumenHablando) y sube en las pausas (volumen),
    con un suavizado de 0,3 s para que no salte; entra en 1 s y sale en 1,5 s.
Por qué no se usa el audio de Remotion: renderizar solo el audio con Remotion recorre todos los cuadros otra vez
(medido: 91 s para 20 s de video) y renderizarlo por partes deja un desfase de 0,35 ms en cada unión (un "clic").
Esta mezcla es exacta a la muestra y tarda unos segundos. `pruebas/test_mezcla.py` revisa el ducking.

Uso suelto: python scripts/mezcla.py public/edit.json salida.wav
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

SR = 48000
FPS_DISENO = 30


def decodificar(ruta: str) -> np.ndarray:
    """Cualquier audio/video -> float32 estéreo a 48 kHz (n, 2)."""
    crudo = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", ruta, "-map", "0:a:0", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(crudo, np.float32).reshape(-1, 2).copy()


def curva_por_cuadro(valores: np.ndarray, fps: float, n: int) -> np.ndarray:
    """Pasa un valor por cuadro a un valor por muestra (interpolación lineal entre cuadros)."""
    t_cuadro = np.arange(len(valores)) / fps
    return np.interp(np.arange(n) / SR, t_cuadro, valores).astype(np.float32)


def envolvente_ducking(captions, total: int, fps: float, alto: float, bajo: float) -> np.ndarray:
    """Volumen de la música en cada cuadro: `bajo` mientras hablan, `alto` en las pausas, con fundidos."""
    hablando = np.zeros(total + 1, np.float32)
    for c in captions:
        i0 = max(0, int(np.floor((c["startMs"] - 150) / 1000 * fps)))
        i1 = min(total, int(np.ceil((c["endMs"] + 250) / 1000 * fps)))
        hablando[i0 : i1 + 1] = 1
    r = int(round(fps * 0.3))
    nucleo = np.ones(2 * r + 1, np.float32) / (2 * r + 1)
    suave = np.convolve(np.pad(hablando, r, mode="constant"), nucleo, mode="valid")[: total + 1]
    v = alto + (bajo - alto) * suave
    f = np.arange(total + 1, dtype=np.float32)
    fundido = np.interp(f, [0, fps, total - fps * 1.5, total], [0, 1, 1, 0])
    return v * fundido


def mezclar(edit: dict, carpeta_public: str) -> np.ndarray:
    fps, total = float(edit["fps"]), int(edit["durationInFrames"])
    n = int(round(total / fps * SR))
    mezcla = np.zeros((n, 2), np.float32)
    s = lambda cuadros: int(round(cuadros / fps * SR))  # noqa: E731  cuadros -> muestras

    # voz (con fundido corto en cada corte, como Clip en Edit.tsx)
    voz = decodificar(os.path.join(carpeta_public, edit["video"]))
    fundido = round(2 * fps / FPS_DISENO)
    for sg in edit["segments"]:
        d = sg["durationInFrames"]
        ini, largo, dest = s(sg["trimBefore"]), s(d), s(sg["from"])
        tramo = voz[ini : ini + largo]
        largo = min(len(tramo), n - dest)
        if largo <= 0:
            continue
        vol = np.interp(np.arange(d + 1), [0, fundido, d - fundido, d], [0, 1, 1, 0]) if fundido > 0 else np.ones(d + 1)
        env = np.interp(np.arange(largo) / SR * fps, np.arange(d + 1), vol).astype(np.float32)
        mezcla[dest : dest + largo] += tramo[:largo] * env[:, None]

    # efectos de sonido al cuadro exacto
    if edit.get("sfx"):
        cache = {}
        for c in edit.get("cues", []):
            if c["archivo"] not in cache:
                cache[c["archivo"]] = decodificar(os.path.join(carpeta_public, c["archivo"]))
            a = cache[c["archivo"]][s(c.get("recorte", 0)) :][: s(round(fps * 3.2))]
            dest = s(c["f"])
            largo = min(len(a), n - dest)
            if largo > 0:
                mezcla[dest : dest + largo] += a[:largo] * float(c["vol"])

    # música con ducking
    m = edit.get("musica")
    if m:
        musica = decodificar(os.path.join(carpeta_public, m["archivo"]))
        if len(musica):
            veces = int(np.ceil(n / len(musica)))
            musica = np.tile(musica, (veces, 1))[:n]
            env = envolvente_ducking(edit.get("captions", []), total, fps, m.get("volumen", 0.22), m.get("volumenHablando", 0.07))
            mezcla += musica * curva_por_cuadro(env, fps, n)[:, None]
    return mezcla


def guardar(audio: np.ndarray, ruta: str) -> None:
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    # (el limitador de la masterización baja los picos después; aquí solo se evita desbordar)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def mezclar_a_archivo(plan: str, salida: str) -> None:
    with open(plan, encoding="utf-8") as f:
        edit = json.load(f)
    audio = mezclar(edit, os.path.dirname(os.path.abspath(plan)))
    pico = float(np.abs(audio).max()) if len(audio) else 0.0
    if pico > 1.0:  # se saturaría al guardar en 16 bits: se baja todo un poco (la masterización lo vuelve a subir)
        audio /= pico * 1.01
    guardar(audio, salida)


if __name__ == "__main__":
    mezclar_a_archivo(sys.argv[1], sys.argv[2])
    print(f"OK: mezcla -> {sys.argv[2]}")
