"""EL OÍDO del editor (nuestra versión liviana de "earshot"): Claude no puede escuchar, así que esto MIDE cada sonido
y lo describe con números y palabras, para escoger el que de verdad sirve.

Mide: duración, dónde está el golpe más fuerte (pico), qué tan rápido arranca (ataque), si es ruido (aire, whoosh)
o tono (campana, ding), si es grave o agudo (brillo), cuántos golpes separados tiene y si está saturado.
Con eso le da un puntaje de 0 a 100 para cada uso (whoosh, impacto, ding, pop, tecla, tick, riser, brillo, whoosh_corto).

Solo usa numpy + ffmpeg (funciona con el Python 3.9 del editor, sin descargar modelos de 1 GB).

Uso:
  python scripts/oido.py archivo.wav                 -> descripción + mejores usos
  python scripts/oido.py --ranking carpeta --tipo whoosh   -> ordena los sonidos de una carpeta para ese uso
  python scripts/oido.py --picos public/sfx          -> guarda public/sfx/picos.json (dónde está el golpe de cada sonido)
"""
import argparse
import json
import os
import subprocess

import numpy as np

SR = 48000

# Perfil ideal de cada uso. (mín, máx) de cada medida; fuera del rango baja el puntaje.
PERFILES = {
    "whoosh": {"dur": (0.25, 1.3), "pico_rel": (0.25, 0.75), "ruido": (0.12, 1.0), "brillo": (700, 7000), "ataque": (0.05, 0.8), "graves": (0.0, 0.4)},
    "whoosh_corto": {"dur": (0.1, 0.5), "pico_rel": (0.15, 0.7), "ruido": (0.12, 1.0), "brillo": (900, 8000), "ataque": (0.02, 0.3)},
    "impacto": {"dur": (0.25, 1.6), "pico_rel": (0.0, 0.12), "ruido": (0.0, 0.6), "brillo": (40, 1500), "ataque": (0.0, 0.02), "graves": (0.12, 1.0)},
    "riser": {"dur": (0.7, 3.0), "pico_rel": (0.72, 1.0), "ruido": (0.0, 1.0), "brillo": (300, 8000), "ataque": (0.6, 3.0)},
    "ding": {"dur": (0.25, 2.0), "pico_rel": (0.0, 0.12), "ruido": (0.0, 0.06), "brillo": (900, 6000), "ataque": (0.0, 0.03), "graves": (0.0, 0.08)},
    "pop": {"dur": (0.03, 0.35), "pico_rel": (0.0, 0.3), "ruido": (0.0, 0.5), "brillo": (300, 4000), "ataque": (0.0, 0.015)},
    "tecla": {"dur": (0.01, 0.12), "pico_rel": (0.0, 0.4), "ruido": (0.05, 1.0), "brillo": (1200, 9000), "ataque": (0.0, 0.006), "graves": (0.0, 0.15)},
    "tick": {"dur": (0.01, 0.12), "pico_rel": (0.0, 0.4), "ruido": (0.0, 0.4), "brillo": (1000, 8000), "ataque": (0.0, 0.006)},
    "brillo": {"dur": (0.4, 2.5), "pico_rel": (0.05, 0.7), "ruido": (0.0, 0.08), "brillo": (1800, 9000), "ataque": (0.0, 0.5), "graves": (0.0, 0.08)},
}
# máximo de segundos que se deja de cada sonido al prepararlo
LARGO_MAX = {"libre": 8.0, "whoosh": 1.3, "whoosh_corto": 0.5, "impacto": 1.6, "riser": 3.0, "ding": 1.8, "pop": 0.35,
             "tecla": 0.12, "tick": 0.12, "brillo": 2.2}


def cargar(ruta, sr=SR):
    """Decodifica cualquier audio (mp3, wav, ogg, flac...) a mono float32 con ffmpeg."""
    crudo = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", ruta, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
        capture_output=True,
    ).stdout
    return np.frombuffer(crudo, np.float32).copy()


def envolvente(x, ventana=0.005):
    n = max(1, int(ventana * SR))
    m = len(x) // n
    if m == 0:
        return np.array([np.sqrt((x**2).mean())]) if len(x) else np.zeros(1)
    return np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(axis=1))


def medir(x):
    """Medidas del sonido (x mono a 48 kHz)."""
    if len(x) < 64 or np.abs(x).max() < 1e-4:
        return {"vacio": True}
    env = envolvente(x)
    paso = 0.005
    tope = env.max()
    umbral = tope * 0.05  # -26 dB del pico: lo que se oye
    activos = np.where(env > umbral)[0]
    ini, fin = activos[0], activos[-1]
    dur = (fin - ini + 1) * paso
    i_pico = int(env.argmax())
    pico_rel = (i_pico - ini) / max(1, fin - ini)
    i10 = ini + int(np.argmax(env[ini : i_pico + 1] > tope * 0.1)) if i_pico > ini else ini
    ataque = (i_pico - i10) * paso
    # espectro (solo la parte que suena)
    seg = x[ini * int(paso * SR) : (fin + 1) * int(paso * SR)]
    n_fft = 2048
    if len(seg) < n_fft:  # sonidos muy cortos (teclas, tics): se rellena con silencio
        seg = np.pad(seg, (0, n_fft - len(seg)))
    marcos = [seg[i : i + n_fft] * np.hanning(n_fft) for i in range(0, len(seg) - n_fft + 1, n_fft // 2)]
    P = np.array([np.abs(np.fft.rfft(m)) ** 2 + 1e-12 for m in marcos])
    f = np.fft.rfftfreq(n_fft, 1 / SR)
    peso = P.sum(axis=1)
    centroide = float(((P * f).sum(axis=1) / P.sum(axis=1) * peso).sum() / peso.sum())
    # "ruido" = planitud espectral (1 = ruido blanco, ~0 = tono puro). Se mide en 100 Hz–12 kHz.
    banda = (f > 100) & (f < 12000)
    Pb = P[:, banda]
    planitud = np.exp(np.log(Pb).mean(axis=1)) / Pb.mean(axis=1)
    ruido = float((planitud * peso).sum() / peso.sum())
    graves = float(P[:, f < 150].sum() / P.sum())
    # golpes separados (un "pack" con 5 whooshes tiene 5): picos de la envolvente separados por silencio
    # (envolvente suavizada de 25 ms: un tono grave no cuenta como muchos golpes; deben separarse por >= 60 ms de casi silencio)
    lisa = np.convolve(env, np.ones(5) / 5, mode="same")
    sobre = lisa > lisa.max() * 0.15
    golpes, hueco, dentro = 0, 99, False
    for v in sobre:
        if v and not dentro:
            if hueco >= 12 or golpes == 0:
                golpes += 1
            dentro, hueco = True, 0
        elif not v:
            dentro = False
            hueco += 1
    saturado = float(np.mean(np.abs(x) > 0.995))
    return {
        "dur": round(dur, 3),
        "pico_seg": round((i_pico - ini) * paso, 3),  # desde que empieza a sonar
        "inicio_seg": round(ini * paso, 3),  # silencio antes de que empiece
        "pico_rel": round(pico_rel, 3),
        "ataque": round(ataque, 4),
        "brillo": round(centroide),
        "ruido": round(ruido, 3),
        "graves": round(graves, 3),
        "golpes": golpes,
        "saturado": round(saturado, 4),
    }


def puntaje(m, tipo):
    if m.get("vacio"):
        return 0.0
    if tipo == "libre":  # sonido especial: solo se revisa la calidad
        s = 100.0
        if m["dur"] > 8:
            s -= 30
        if m["dur"] < 0.05:
            s -= 40
        if m["saturado"] > 0.001:
            s -= 35
        s -= min(30, 6 * max(0, m["golpes"] - 3))
        return round(max(0.0, s), 1)
    perfil = PERFILES[tipo]
    total = 0.0
    for clave, (lo, hi) in perfil.items():
        v = m[clave]
        if lo <= v <= hi:
            total += 1.0
        else:
            # cae suave fuera del rango (en escala logarítmica para tiempos y frecuencias)
            if clave in ("dur", "brillo", "ataque"):
                d = abs(np.log((v + 1e-3) / ((lo if v < lo else hi) + 1e-3)))
                total += float(np.exp(-d * 1.5))
            else:
                d = (lo - v) if v < lo else (v - hi)
                total += float(np.exp(-d * 6))
    s = total / len(perfil) * 100
    if m["golpes"] > 1 and tipo not in ("riser", "brillo"):
        s *= 0.85 ** (m["golpes"] - 1)  # varios golpes: no sirve tal cual
    if m["saturado"] > 0.001:
        s *= 0.7
    if m["graves"] > 0.5 and tipo not in ("impacto",):
        s *= 0.85
    return round(s, 1)


def describir(m):
    if m.get("vacio"):
        return "silencio (no suena nada)"
    forma = "arranca de golpe y se apaga" if m["pico_rel"] < 0.15 else ("crece hasta el final" if m["pico_rel"] > 0.75 else "sube y baja")
    textura = "ruidoso (aire, roce)" if m["ruido"] > 0.15 else ("tonal (como campana o nota)" if m["ruido"] < 0.05 else "mezcla de tono y ruido")
    altura = "grave" if m["brillo"] < 800 else ("medio" if m["brillo"] < 2500 else "agudo/brillante")
    extra = []
    if m["golpes"] > 1:
        extra.append(f"{m['golpes']} golpes separados")
    if m["saturado"] > 0.001:
        extra.append("SATURADO")
    if m["inicio_seg"] > 0.05:
        extra.append(f"{m['inicio_seg']:.2f} s de silencio al inicio")
    return f"{m['dur']:.2f} s, {forma}, {textura}, {altura}, golpe a los {m['pico_seg']:.2f} s" + (" — " + ", ".join(extra) if extra else "")


def mejor_evento(x):
    """Si el archivo trae varios golpes (packs), recorta el más fuerte."""
    env = envolvente(x)
    tope = env.max()
    sobre = env > tope * 0.05
    i = int(env.argmax())
    a = i
    while a > 0 and (sobre[a - 1] or env[max(0, a - 20) : a].max() > tope * 0.05):
        a -= 1
        if not sobre[a] and env[max(0, a - 20) : a].max() <= tope * 0.05:
            break
    b = i
    while b < len(env) - 1 and (sobre[b + 1] or env[b + 1 : b + 21].max() > tope * 0.05):
        b += 1
        if not sobre[b] and env[b + 1 : b + 21].max() <= tope * 0.05:
            break
    p = int(0.005 * SR)
    return x[max(0, a * p - int(0.01 * SR)) : (b + 1) * p]


def preparar(entrada, salida, tipo):
    """Deja el sonido listo: un solo golpe, sin silencio al inicio, largo máximo, fundido final, pico a -6 dB, 48 kHz estéreo."""
    x = cargar(entrada)
    if tipo != "libre":  # un sonido especial (aplausos, lluvia) se deja entero
        x = mejor_evento(x)
    m = medir(x)
    if m.get("vacio"):
        raise ValueError("sonido vacío")
    ini = max(0, int((m["inicio_seg"] - 0.008) * SR))
    x = x[ini : ini + int(LARGO_MAX[tipo] * SR)]
    fo = min(len(x) // 3, int(0.06 * SR))
    if fo > 0:
        x[-fo:] *= np.linspace(1, 0, fo)
    x = x / (np.abs(x).max() + 1e-9) * 10 ** (-6 / 20)
    datos = (np.clip(np.stack([x, x], axis=1), -1, 1) * 32767).astype("<i2")
    import wave

    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    with wave.open(salida, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(datos.tobytes())
    return medir(x)


def picos(carpeta):
    """Guarda dónde está el golpe de cada sonido (para alinearlo al cuadro exacto, como Real SFX)."""
    res = {}
    for raiz, _, archivos in os.walk(carpeta):
        for a in sorted(archivos):
            if a.lower().endswith(".wav"):
                ruta = os.path.join(raiz, a)
                rel = os.path.relpath(ruta, carpeta).replace(os.sep, "/")
                m = medir(cargar(ruta))
                if not m.get("vacio"):
                    res[rel[:-4]] = round(m["inicio_seg"] + m["pico_seg"], 3)
    json.dump(res, open(os.path.join(carpeta, "picos.json"), "w"), indent=1)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", nargs="?")
    ap.add_argument("--tipo", choices=sorted(PERFILES))
    ap.add_argument("--ranking", help="carpeta con candidatos")
    ap.add_argument("--picos", help="carpeta de sonidos (escribe picos.json)")
    a = ap.parse_args()
    if a.picos:
        r = picos(a.picos)
        print(f"OK: picos de {len(r)} sonidos -> {a.picos}/picos.json")
    elif a.ranking:
        filas = []
        for n in sorted(os.listdir(a.ranking)):
            ruta = os.path.join(a.ranking, n)
            if os.path.isfile(ruta):
                m = medir(mejor_evento(cargar(ruta)))
                filas.append((puntaje(m, a.tipo), n, describir(m)))
        for s, n, d in sorted(filas, reverse=True):
            print(f"{s:5.1f}  {n}  — {d}")
    elif a.archivo:
        m = medir(cargar(a.archivo))
        print(describir(m))
        usos = sorted(((puntaje(m, t), t) for t in PERFILES), reverse=True)[:3]
        print("Sirve para: " + ", ".join(f"{t} ({s:.0f})" for s, t in usos))
        if a.tipo:
            print(f"Puntaje como {a.tipo}: {puntaje(m, a.tipo)}")
    else:
        ap.print_help()
