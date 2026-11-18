"""ANIMACIONES EXPLICATIVAS desde cero (sin grabar nada): de una "receta" JSON a un video terminado.

    bash scripts/animar.sh demo/animaciones/palitos_pirata.json
    bash scripts/animar.sh mi_receta.json --formato reel --calidad preview

Tipos (cada uno es también un comando con barra para Claude Code: /minimalista, /palitos, /despiece, /mapa-ruta, /grafica):
  minimal   formas simples, puntos que se mueven y animaciones limpias (fondo negro)
  palitos   caricatura con monitos de palitos, fondos, objetos, poses y globos de diálogo
  despiece  un producto que se separa en sus piezas ("vista explotada") con etiquetas
  mapa      mapa 3D con la ruta animada entre dos lugares
  grafica   tus números se vuelven una gráfica que se construye sola, con contador

Receta (campos comunes): {"tipo", "formato" (tv|reel|cuadrado|retrato), "idioma" (es|en), "voz" (true|false|"Paulina"),
  "musica" ("calma"|"lofi"|"energia"|"epica"|false), "pasos": [{"texto": "lo que se narra/lee", ...}]}
Cada paso dura lo que tarda la voz en decir su texto (o lo que diga "segundos"). Ejemplos en demo/animaciones/.

La voz narrada usa las voces de macOS (comando `say`, gratis y sin internet): Paulina (español) y Samantha (inglés).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import wave

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import audio  # noqa: E402
import editor  # noqa: E402
import medios  # noqa: E402
import mezcla  # noqa: E402
from editor import ErrorEditor, ruta  # noqa: E402

TIPOS = ("minimal", "palitos", "despiece", "mapa", "grafica")
VOCES = {"es": "Paulina", "en": "Samantha"}
CAMPOS = ("tema", "titulo", "fondo", "producto", "origen", "destino", "tiempo", "distancia", "calles", "valores",
          "etiquetas", "etiqueta", "prefijo", "sufijo", "decimales", "grafica")


def leer_receta(p: str) -> dict:
    try:
        with open(p, encoding="utf-8") as f:
            r = json.load(f)
    except FileNotFoundError:
        raise ErrorEditor(f"No encuentro la receta '{p}'.", "Revisa el nombre del archivo (los ejemplos están en demo/animaciones/).")
    except json.JSONDecodeError as e:
        raise ErrorEditor(f"La receta tiene un error de escritura (línea {e.lineno}).", "Revisa comas y comillas en esa línea.")
    if r.get("tipo") not in TIPOS:
        raise ErrorEditor(f"Tipo de animación desconocido: '{r.get('tipo')}'.", "Usa uno de estos: " + ", ".join(TIPOS))
    if not r.get("pasos"):
        raise ErrorEditor("La receta no tiene 'pasos'.", 'Agrega al menos uno: "pasos": [{"texto": "..."}]')
    return r


def decir(texto: str, voz: str, destino: str) -> float:
    """Voz narrada con macOS (gratis, sin internet). Devuelve la duración en segundos."""
    tmp = destino + ".aiff"
    r = subprocess.run(["say", "-v", voz, "-r", "172", "-o", tmp, texto], capture_output=True, text=True)
    if r.returncode != 0:
        raise ErrorEditor(f"No pude generar la voz con '{voz}'.", "Prueba con \"voz\": false en la receta, o con otra voz (say -v '?').", r.stderr)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-ar", "48000", "-ac", "2", destino], check=True)
    os.remove(tmp)
    return medios.info(destino)["duracion"]


def leer_wav(p: str) -> np.ndarray:
    with wave.open(p) as w:
        datos = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return datos.reshape(-1, w.getnchannels())


def principal(argv) -> int:
    ap = argparse.ArgumentParser(prog="bash scripts/animar.sh", description="Convierte una receta JSON en una animación explicativa.")
    ap.add_argument("receta")
    ap.add_argument("--formato", default="", help="tv, reel, cuadrado o retrato (si no, el de la receta; si no, tv)")
    ap.add_argument("--calidad", default="final", choices=["preview", "final", "maxima"])
    ap.add_argument("--salida", default="", help="archivo final (por defecto salida/<receta>_<formato>.mp4)")
    ap.add_argument("--solo-preparar", action="store_true", help="arma public/animacion.json sin renderizar (para revisar cuadros)")
    ap.add_argument("--broll", action="store_true", help="además copia el video a public/broll/ para usarlo dentro de una edición")
    a = ap.parse_args(argv)
    cfg = editor.cargar_config()
    r = leer_receta(a.receta)
    formato = editor.FORMATOS_ALIAS.get(a.formato or r.get("formato", "tv"), a.formato or r.get("formato", "tv"))
    if formato not in cfg["formatos"]:
        raise ErrorEditor(f"No conozco el formato '{formato}'.", "Usa tv, reel, cuadrado o retrato.")
    W, H, fps = cfg["formatos"][formato]["ancho"], cfg["formatos"][formato]["alto"], cfg["fps"]
    nombre = os.path.splitext(os.path.basename(a.receta))[0]
    pasos_ui = editor.Pasos(4)
    inicio = time.time()

    pasos_ui("Voz narrada y tiempos de cada paso...")
    idioma = r.get("idioma", "es")
    voz = r.get("voz", True)
    voz = VOCES.get(idioma, "Paulina") if voz is True else (voz or None)
    if voz and not shutil.which("say"):
        pasos_ui.nota("(Este computador no tiene la voz de macOS: la animación sale sin narración.)")
        voz = None
    trabajo = tempfile.mkdtemp(prefix="animar_", dir=ruta("trabajo"))
    t = 0.4  # pequeña pausa al inicio
    pasos, voces = [], []
    for i, p in enumerate(r["pasos"]):
        texto = p.get("texto", "")
        dur_voz = 0.0
        if voz and texto:
            archivo = os.path.join(trabajo, f"voz_{i:02d}.wav")
            dur_voz = decir(texto, voz, archivo)
            voces.append((t + 0.15, archivo, dur_voz))
        lectura = max(2.2, len(texto.split()) * 0.42 + 1.0)  # si no hay voz: lo que tarda alguien en leerlo
        dur = float(p.get("segundos") or (max(2.0, dur_voz + 0.55) if dur_voz else lectura))
        paso = {k: v for k, v in p.items() if k not in ("segundos",)}
        paso.update({"texto": texto, "desdeMs": round(t * 1000), "hastaMs": round((t + dur) * 1000)})
        pasos.append(paso)
        t += dur
    total_s = t + 0.6
    pasos[0]["desdeMs"] = 0
    pasos[-1]["hastaMs"] = round(total_s * 1000)
    data = {"tipo": r["tipo"], "width": W, "height": H, "fps": fps, "durationInFrames": int(round(total_s * fps)), "pasos": pasos}
    data.update({k: r[k] for k in CAMPOS if k in r})
    if "capas" in r:
        data["capasDespiece"] = r["capas"]
    editor.escribir_json(ruta("public", "animacion.json"), data)
    pasos_ui.nota(f"{len(pasos)} pasos, {total_s:.1f} s, {W}x{H} a {fps} fps" + (f", voz {voz}" if voz else ", sin voz") + ".")

    if a.solo_preparar:
        shutil.rmtree(trabajo, ignore_errors=True)
        print("LISTO (sin renderizar): public/animacion.json. Un cuadro: npx remotion still src/index.ts Animacion trabajo/x.png --frame=N")
        return 0
    pasos_ui(f"Dibujando la animación a {fps} fps (calidad {a.calidad})...")
    q = cfg["calidades"][a.calidad]
    bundle = os.path.join(trabajo, "bundle")
    editor.correr(["npx", "remotion", "bundle", "src/index.ts", "--out-dir", bundle, "--log", "error"],
                  "Remotion no pudo preparar el proyecto (error en el código de src/).", "Corre: npm test")
    video = os.path.join(trabajo, "video.mp4")
    editor.render_parte(bundle, video, 0, data["durationInFrames"] - 1, q, 0, 1, pasos_ui, composicion="Animacion")

    pasos_ui("Voz, música y efectos (audio masterizado a -14 LUFS)...")
    n = int(round(total_s * mezcla.SR))
    pista = np.zeros((n, 2), np.float32)
    for desde, archivo, _ in voces:
        v = leer_wav(archivo)
        i0 = int(desde * mezcla.SR)
        largo = min(len(v), n - i0)
        pista[i0 : i0 + largo] += v[:largo] * 0.9
    sfx = mezcla.decodificar(ruta("public", "sfx", "whoosh_corto.wav"))
    for p in pasos[1:]:
        i0 = int(p["desdeMs"] / 1000 * mezcla.SR)
        largo = min(len(sfx), n - i0)
        if largo > 0:
            pista[i0 : i0 + largo] += sfx[:largo] * 0.18
    animo = r.get("musica", "calma")
    if animo:
        musica = os.path.join(trabajo, "musica.wav")
        rr = subprocess.run([sys.executable, ruta("scripts", "musica.py"), "--animo", animo, "--duracion", f"{total_s:.2f}",
                             "--salida", musica, "--semilla", "7"], capture_output=True, text=True)
        if rr.returncode == 0:
            m = mezcla.decodificar(musica)[:n]
            habla = [{"startMs": d * 1000, "endMs": (d + dv) * 1000} for d, _, dv in voces]
            total_f = data["durationInFrames"]
            env = mezcla.envolvente_ducking(habla, total_f, fps, 0.2, 0.06) if voces else np.full(total_f + 1, 0.2, np.float32)
            pista[: len(m)] += m * mezcla.curva_por_cuadro(env, fps, n)[: len(m), None]
        else:
            pasos_ui.nota("(No se pudo componer la música; sigue sin música.)")
    mezcla_wav = os.path.join(trabajo, "mezcla.wav")
    pico = float(np.abs(pista).max()) if n else 0
    if pico > 1:
        pista /= pico * 1.01
    mezcla.guardar(pista, mezcla_wav)
    master = os.path.join(trabajo, "master.m4a")
    medida = audio.masterizar(mezcla_wav, master, cfg["audio"]["lufs"], cfg["audio"]["picoMaximoDbtp"], q["audioKbps"])
    salida = a.salida or ruta("salida", f"{nombre}_{formato}{'_preview' if a.calidad == 'preview' else ''}.mp4")
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    editor.correr(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", master, "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
                   "-movflags", "+faststart", salida], "No pude juntar el video con el audio.")

    pasos_ui("Control de calidad...")
    d = medios.info(salida)
    esc = q.get("escala", 1)
    revisiones = [
        (abs(d["fps"] - fps) < 0.01, f"{d['fps']:g} fps"),
        ((d["ancho"], d["alto"]) == (round(W * esc), round(H * esc)), f"{d['ancho']}x{d['alto']}"),
        (abs(d["duracion"] - total_s) < 0.15, f"duración {d['duracion']:.1f} s"),
        (abs(medida["lufs"] - cfg["audio"]["lufs"]) <= 1, f"volumen {medida['lufs']:.1f} LUFS"),
        (medida["pico_dbtp"] <= cfg["audio"]["picoMaximoDbtp"], f"pico real {medida['pico_dbtp']:.1f} dBTP"),
    ]
    for ok, texto in revisiones:
        print(("  ✓ " if ok else "  ✗ ") + texto)
    if a.broll:
        destino = ruta("public", "broll", os.path.basename(salida))
        shutil.copy2(salida, destino)
        pasos_ui.nota(f"Copiado para usarlo en una edición: {os.path.relpath(destino, ruta())} (escena broll o dividida, \"archivo\": \"broll/{os.path.basename(salida)}\")")
    shutil.rmtree(trabajo, ignore_errors=True)
    print(f"LISTO: {os.path.relpath(salida, ruta())}  (tardó {int(time.time() - inicio)} s)")
    return 0 if all(ok for ok, _ in revisiones) else 1


def main():
    try:
        with editor.Candado():
            sys.exit(principal(sys.argv[1:]))
    except ErrorEditor as e:
        print("\n" + "=" * 60, file=sys.stderr)
        print(f"  PROBLEMA: {e.que}", file=sys.stderr)
        if e.como_arreglar:
            print(f"  QUÉ HACER: {e.como_arreglar}", file=sys.stderr)
        if e.detalle:
            print("  Detalle técnico (para Claude):\n    " + e.detalle.replace("\n", "\n    "), file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\nDetenido.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
