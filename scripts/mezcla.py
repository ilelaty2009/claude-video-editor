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


def tapar_con_pitido(pista: np.ndarray, pitidos, frecuencia: float = 1000.0, volumen: float = 0.25) -> None:
    """Censura: silencia la voz en cada tramo y pone un pitido (con bordes suaves de 5 ms, sin "clic")."""
    rampa = int(SR * 0.005)
    for p in pitidos:
        i0 = max(0, int(p["desdeMs"] / 1000 * SR))
        i1 = min(len(pista), int(p["hastaMs"] / 1000 * SR))
        if i1 - i0 <= 2 * rampa:
            continue
        env = np.ones(i1 - i0, np.float32)
        env[:rampa] = np.linspace(0, 1, rampa)
        env[-rampa:] = np.linspace(1, 0, rampa)
        tono = np.sin(2 * np.pi * frecuencia * np.arange(i1 - i0) / SR).astype(np.float32) * volumen * env
        pista[i0:i1] = pista[i0:i1] * (1 - env[:, None]) + tono[:, None]


def _db(x: np.ndarray) -> float:
    """Nivel RMS en dB (0 dB = máximo). -120 si está en silencio."""
    if x.size == 0:
        return -120.0
    return float(20 * np.log10(max(1e-6, float(np.sqrt(np.mean(np.square(x, dtype=np.float64)))))))


def _db_golpe(x: np.ndarray, ventana: float = 0.03) -> float:
    """Nivel del momento más fuerte de un sonido (RMS en ventanas de 30 ms): lo que "pega" al oído."""
    n = max(1, int(SR * ventana))
    if len(x) < n:
        return _db(x)
    mono = x.mean(axis=1) if x.ndim == 2 else x
    energia = np.convolve(mono.astype(np.float64) ** 2, np.ones(n) / n, mode="valid")
    return float(10 * np.log10(max(1e-12, float(energia.max()))))


def mascara_habla(captions, n: int) -> np.ndarray:
    m = np.zeros(n, bool)
    for c in captions:
        m[max(0, int(c["startMs"] / 1000 * SR)) : min(n, int(c["endMs"] / 1000 * SR))] = True
    return m


# Reglas de mezcla (medidas, no "a ojo"), como las de un editor de sonido:
MUSICA_MIN_BAJO_VOZ = 12.0  # la música debe quedar al menos 12 dB por debajo de la voz mientras hablan
MUSICA_META_BAJO_VOZ = 15.0  # si no cumple, se baja hasta quedar 15 dB por debajo
EFECTO_MAX_SOBRE_VOZ = 3.0  # el golpe de un efecto no debe pasar a la voz por más de 3 dB


def capas(edit: dict, carpeta_public: str) -> dict:
    """Las tres capas del audio por separado (voz, efectos, música) + dónde quedó cada efecto."""
    fps, total = float(edit["fps"]), int(edit["durationInFrames"])
    n = int(round(total / fps * SR))
    s = lambda cuadros: int(round(cuadros / fps * SR))  # noqa: E731  cuadros -> muestras

    # voz (con fundido corto en cada corte, como Clip en Edit.tsx)
    pista_voz = np.zeros((n, 2), np.float32)
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
        pista_voz[dest : dest + largo] += tramo[:largo] * env[:, None]
    tapar_con_pitido(pista_voz, edit.get("pitidos", []))

    # efectos de sonido al cuadro exacto (cada uno por separado, para poder medirlo contra la voz)
    efectos = []
    if edit.get("sfx"):
        cache = {}
        for c in edit.get("cues", []):
            if c["archivo"] not in cache:
                cache[c["archivo"]] = decodificar(os.path.join(carpeta_public, c["archivo"]))
            a = cache[c["archivo"]][s(c.get("recorte", 0)) :][: s(round(fps * 3.2))]
            dest = s(c["f"])
            largo = min(len(a), n - dest)
            if largo > 0:
                efectos.append({"cue": c, "dest": dest, "audio": a[:largo] * float(c["vol"])})

    # música con ducking
    pista_musica = np.zeros((n, 2), np.float32)
    m = edit.get("musica")
    if m:
        musica = decodificar(os.path.join(carpeta_public, m["archivo"]))
        if len(musica):
            veces = int(np.ceil(n / len(musica)))
            musica = np.tile(musica, (veces, 1))[:n]
            env = envolvente_ducking(edit.get("captions", []), total, fps, m.get("volumen", 0.22), m.get("volumenHablando", 0.07))
            pista_musica = musica * curva_por_cuadro(env, fps, n)[:, None]
    return {"voz": pista_voz, "efectos": efectos, "musica": pista_musica, "n": n, "hayMusica": bool(m)}


def nivelar(c: dict, captions) -> dict:
    """Mide la música y CADA efecto contra la voz y corrige lo que se sale de las reglas. Devuelve el informe."""
    habla = mascara_habla(captions, c["n"])
    informe = {"vozDb": None, "musicaBajoVozDb": None, "musicaBajadaDb": 0.0, "efectos": len(c["efectos"]), "efectosBajados": 0,
               "efectoMasFuerteDb": None}
    if not habla.any():
        return informe
    voz_db = _db(c["voz"][habla])
    informe["vozDb"] = round(voz_db, 1)
    if c["hayMusica"]:
        dif = voz_db - _db(c["musica"][habla])
        if dif < MUSICA_MIN_BAJO_VOZ:  # tapa la voz: se baja
            bajar = MUSICA_META_BAJO_VOZ - dif
            c["musica"] *= 10 ** (-bajar / 20)
            informe["musicaBajadaDb"] = round(bajar, 1)
            dif = MUSICA_META_BAJO_VOZ
        informe["musicaBajoVozDb"] = round(dif, 1)
    mas_fuerte = -120.0
    for e in c["efectos"]:
        sobre = _db_golpe(e["audio"]) - voz_db
        if sobre > EFECTO_MAX_SOBRE_VOZ:  # pega más fuerte que la voz: se baja hasta quedar 1 dB encima
            e["audio"] = e["audio"] * 10 ** (-(sobre - 1.0) / 20)
            informe["efectosBajados"] += 1
            sobre = 1.0
        mas_fuerte = max(mas_fuerte, sobre)
    if c["efectos"]:
        informe["efectoMasFuerteDb"] = round(mas_fuerte, 1)
    return informe


def mezclar(edit: dict, carpeta_public: str, informe: dict = None) -> np.ndarray:
    """La mezcla final. Si se pasa `informe` (un dict), se llena con las medidas de música y efectos contra la voz."""
    c = capas(edit, carpeta_public)
    medidas = nivelar(c, edit.get("captions", []))
    if informe is not None:
        informe.update(medidas)
    mezcla = c["voz"] + c["musica"]
    for e in c["efectos"]:
        mezcla[e["dest"] : e["dest"] + len(e["audio"])] += e["audio"]
    return mezcla


def guardar(audio: np.ndarray, ruta: str) -> None:
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    # (el limitador de la masterización baja los picos después; aquí solo se evita desbordar)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def mezclar_a_archivo(plan: str, salida: str) -> dict:
    """Escribe la mezcla y devuelve el informe de niveles (también lo guarda en <salida>.niveles.json)."""
    with open(plan, encoding="utf-8") as f:
        edit = json.load(f)
    informe: dict = {}
    audio = mezclar(edit, os.path.dirname(os.path.abspath(plan)), informe)
    pico = float(np.abs(audio).max()) if len(audio) else 0.0
    if pico > 1.0:  # se saturaría al guardar en 16 bits: se baja todo un poco (la masterización lo vuelve a subir)
        audio /= pico * 1.01
    guardar(audio, salida)
    with open(salida + ".niveles.json", "w", encoding="utf-8") as f:
        json.dump(informe, f)
    return informe


def texto_informe(i: dict) -> str:
    """El informe en una línea, en español simple."""
    partes = []
    if i.get("musicaBajoVozDb") is not None:
        partes.append(f"música {i['musicaBajoVozDb']:.0f} dB debajo de la voz" + (f" (la bajé {i['musicaBajadaDb']:.0f} dB: tapaba la voz)" if i.get("musicaBajadaDb") else ""))
    if i.get("efectos"):
        partes.append(f"{i['efectos']} efectos medidos contra la voz" + (f" ({i['efectosBajados']} sonaban más fuerte que la voz y los bajé)" if i.get("efectosBajados") else ""))
    return "; ".join(partes) or "solo voz"


if __name__ == "__main__":
    print(f"OK: mezcla -> {sys.argv[2]} ({texto_informe(mezclar_a_archivo(sys.argv[1], sys.argv[2]))})")
