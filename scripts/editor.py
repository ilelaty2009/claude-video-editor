"""EDITOR DE VIDEOS — de video crudo a video terminado con un solo comando.

    bash scripts/editar.sh videos/mi-video.mov --preset colegio-tv
    bash scripts/editar.sh videos/mi-video.mov --preset tiktok --extras trabajo/mi-video_extras.json

Pasos (cada uno guarda su resultado en caché: si el video y las opciones no cambiaron, no se repite):
  1. Revisar herramientas y el video.
  2. Caras (para zooms y recortes) y color automático.
  3. Voz limpia + video preparado en el formato pedido.
  4. Transcripción (Whisper).            -> se reusa sola si el video es el mismo
  5. Plan de edición (cortes, subtítulos, escenas, sonidos) y música original.
  6. Render a 60 fps POR PARTES.          -> si se interrumpe, al volver a correr solo hace las partes que faltan
  7. Audio masterizado (-14 LUFS, pico real < -1 dBTP), portada, control de calidad y subtítulos .srt.

Toda la configuración está en editor.config.json (presets, formatos, calidades, audio).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Dict, List, Optional

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

import audio  # noqa: E402
import medios  # noqa: E402
import mezcla  # noqa: E402

VERSION_CACHE = "3"  # subir este número si cambia cómo se prepara el video (invalida la caché vieja)
PY = sys.executable


class ErrorEditor(Exception):
    """Error con un mensaje en español claro y qué hacer para arreglarlo."""

    def __init__(self, que: str, como_arreglar: str = "", detalle: str = ""):
        super().__init__(que)
        self.que, self.como_arreglar, self.detalle = que, como_arreglar, detalle


# ---------------------------------------------------------------- utilidades
def ruta(*partes: str) -> str:
    return os.path.join(RAIZ, *partes)


def cargar_config() -> Dict:
    try:
        with open(ruta("editor.config.json"), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ErrorEditor("Falta editor.config.json.", "Recupéralo con: git checkout editor.config.json")
    except json.JSONDecodeError as e:
        raise ErrorEditor(
            f"editor.config.json tiene un error de escritura (línea {e.lineno}).",
            "Revisa comas y comillas en esa línea, o recupera el original con: git checkout editor.config.json",
        )


def correr(cmd: List[str], que: str, como_arreglar: str = "", **kw) -> subprocess.CompletedProcess:
    """Corre un comando; si falla, lanza ErrorEditor con las últimas líneas del error."""
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=RAIZ, **kw)
    if r.returncode != 0:
        detalle = "\n".join((r.stderr or r.stdout or "").strip().splitlines()[-12:])
        raise ErrorEditor(que, como_arreglar, detalle)
    return r


def huella_archivo(p: str) -> str:
    """Huella rápida del contenido (tamaño + primeros y últimos 4 MB): cambia si el video cambia."""
    h = hashlib.sha1()
    tam = os.path.getsize(p)
    h.update(str(tam).encode())
    with open(p, "rb") as f:
        h.update(f.read(4 << 20))
        if tam > 8 << 20:
            f.seek(-(4 << 20), os.SEEK_END)
            h.update(f.read())
    return h.hexdigest()


def huella_texto(*cosas) -> str:
    return hashlib.sha1(json.dumps(cosas, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def huella_carpeta(carpeta: str, excluir=()) -> str:
    h = hashlib.sha1()
    for base, dirs, archivos in os.walk(carpeta):
        dirs.sort()
        for a in sorted(archivos):
            p = os.path.join(base, a)
            rel = os.path.relpath(p, carpeta)
            if any(rel.startswith(x) for x in excluir) or a == ".DS_Store":
                continue
            h.update(rel.encode())
            h.update(huella_archivo(p).encode())
    return h.hexdigest()


def leer_json(p: str) -> Optional[Dict]:
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def escribir_json(p: str, datos: Dict) -> None:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)  # escritura atómica: si se corta, no queda un JSON a medias


def copiar(origen: str, destino: str) -> None:
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.exists(destino):
        os.remove(destino)
    try:
        os.link(origen, destino)  # sin ocupar espacio extra
    except OSError:
        shutil.copy2(origen, destino)


class Pasos:
    def __init__(self, total: int):
        self.total, self.n, self.t0 = total, 0, time.time()
        self.tiempos: List[tuple] = []

    def __call__(self, texto: str) -> None:
        self._cerrar()
        self.n += 1
        self.actual = texto
        print(f"{self.n}/{self.total} {texto}", flush=True)

    def _cerrar(self) -> None:
        if self.n:
            self.tiempos.append((self.actual, time.time() - self.t0))
        self.t0 = time.time()

    def resumen(self) -> str:
        self._cerrar()
        return " | ".join(f"{t.split()[0].strip('.')} {s:.0f}s" for t, s in self.tiempos)

    def nota(self, texto: str) -> None:
        print(f"    {texto}", flush=True)


# ---------------------------------------------------------------- opciones
FORMATOS_ALIAS = {"16:9": "tv", "horizontal": "tv", "9:16": "reel", "vertical": "reel", "tiktok": "reel",
                  "1:1": "cuadrado", "4:5": "retrato"}


def leer_opciones(argv: List[str], cfg: Dict) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="bash scripts/editar.sh",
        description="Edita un video de punta a punta. Ejemplo: bash scripts/editar.sh videos/X.mov --preset colegio-tv",
    )
    ap.add_argument("video", help="el video crudo (por ejemplo videos/mi-video.mov)")
    ap.add_argument("--preset", choices=sorted(cfg["presets"]), help="configuración lista: colegio-tv, tiktok…")
    ap.add_argument("--formato", help="tv (16:9), reel (9:16), cuadrado (1:1) o retrato (4:5)")
    ap.add_argument("--estilo", choices=sorted(cfg["estilos"]), help="clase, tiktok, youtube o documental")
    ap.add_argument("--calidad", choices=sorted(cfg["calidades"]), help="preview (rápida), final o maxima")
    ap.add_argument("--subtitulos", choices=["tiktok", "cine", "caja", "resaltado"], help="estilo de subtítulos")
    ap.add_argument("--extras", default="", help="trabajo/X_extras.json (escenas, destacadas, capítulos…)")
    ap.add_argument("--titulo", default="")
    ap.add_argument("--encuadre", default="", help="auto, completo, relleno o recorte")
    ap.add_argument("--modelo", default="small", help="modelo de Whisper: small (rápido) o medium (más preciso)")
    ap.add_argument("--idioma", default="es", help="es, en o auto")
    ap.add_argument("--pistas", default="", help="nombres difíciles para Whisper, separados por coma")
    ap.add_argument("--silencio", default="0.3", help="segundos de pausa que se cortan")
    ap.add_argument("--quitar", default="", help="muletillas a borrar, ej: 'eh,este'")
    ap.add_argument("--audio", default="limpio", choices=["limpio", "original"])
    ap.add_argument("--color", default="", choices=["", "natural", "cine", "calido", "vivo", "no"])
    ap.add_argument("--reusar", action="store_true", help="usa la transcripción guardada aunque cambien modelo/idioma")
    ap.add_argument("--sin-cache", action="store_true", help="rehace todo desde cero")
    ap.add_argument("--solo-preparar", action="store_true", help="prepara todo sin renderizar (para revisar.sh)")
    ap.add_argument("--salida", default="", help="nombre del archivo final (por defecto salida/<video>_<formato>.mp4)")
    a = ap.parse_args(argv)

    # compatibilidad: RENDER_FLAGS="--frames=0-1" significaba "preparar sin renderizar"
    if "--frames=0-1" in os.environ.get("RENDER_FLAGS", ""):
        a.solo_preparar = True

    preset = cfg["presets"].get(a.preset or "", {})
    a.formato = FORMATOS_ALIAS.get(a.formato or "", a.formato) or preset.get("formato", "tv")
    if a.formato not in cfg["formatos"]:
        raise ErrorEditor(f"No conozco el formato '{a.formato}'.",
                          "Usa uno de estos: " + ", ".join(f"{k} = {v['nombre']}" for k, v in cfg["formatos"].items()))
    a.estilo = a.estilo or preset.get("estilo", "")
    a.calidad = a.calidad or preset.get("calidad", "final")
    est = cfg["estilos"].get(a.estilo, {})
    a.color = a.color or est.get("color", "natural")
    return a


# ---------------------------------------------------------------- pasos
def revisar_herramientas() -> None:
    faltan = [h for h in ("ffmpeg", "node", "npx") if not shutil.which(h)]
    if faltan:
        raise ErrorEditor(
            "Faltan herramientas: " + ", ".join(faltan) + ".",
            "Haz doble clic en instalar.command (o corre: source scripts/entorno.sh antes de editar).",
        )
    if not os.path.isdir(ruta("node_modules", "remotion")):
        raise ErrorEditor("Remotion no está instalado (falta node_modules).", "Haz doble clic en instalar.command.")
    libre = shutil.disk_usage(RAIZ).free / 1e9
    if libre < 2:
        raise ErrorEditor(f"Queda muy poco espacio en el disco ({libre:.1f} GB).",
                          "Libera al menos 2 GB (por ejemplo borra videos viejos de salida/) y vuelve a correr.")


def revisar_video(p: str) -> Dict:
    if not os.path.exists(p):
        cerca = sorted(os.listdir(ruta("videos"))) if os.path.isdir(ruta("videos")) else []
        raise ErrorEditor(f"No encuentro el video '{p}'.",
                          ("Videos que sí hay en videos/: " + ", ".join(cerca)) if cerca else
                          "Pon tu video en la carpeta videos/ y escribe su nombre exacto.")
    try:
        d = medios.info(p)
    except medios.ErrorMedio as e:
        raise ErrorEditor(str(e), "Prueba exportando el video otra vez desde el celular o la cámara.")
    if not d["tiene_video"]:
        raise ErrorEditor(f"'{p}' no tiene imagen (¿es solo audio?).", "Usa un archivo de video (.mov, .mp4).")
    if not d["tiene_audio"]:
        raise ErrorEditor(f"'{p}' no tiene sonido: sin voz no hay subtítulos ni cortes.",
                          "Revisa que el micrófono estuviera prendido al grabar.")
    if d["duracion"] < 1:
        raise ErrorEditor(f"'{p}' dura menos de 1 segundo.", "Revisa que el video se haya copiado completo.")
    return d


def paso_caras(video: str, nombre: str, huella: str, sin_cache: bool) -> Dict:
    destino = ruta("trabajo", f"{nombre}_caras.json")
    previo = leer_json(destino)
    if previo and previo.get("huella") == huella and not sin_cache:
        return previo
    r = subprocess.run([PY, ruta("scripts", "seguir_cara.py"), video, destino], capture_output=True, text=True, cwd=RAIZ)
    datos = leer_json(destino) if r.returncode == 0 else None
    if not datos:
        print("    (No se pudo buscar caras; los zooms van al centro.)")
        datos = {"foco": {"x": 0.5, "y": 0.42}, "recorte_x": 0.5, "muestras": []}
    datos["huella"] = huella
    escribir_json(destino, datos)
    return datos


def paso_color(video: str, look: str, cache: Dict) -> str:
    if look == "no":
        return ""
    clave = f"color_{look}"
    if clave not in cache:
        r = subprocess.run([PY, ruta("scripts", "color_auto.py"), video, "--look", look], capture_output=True, text=True)
        cache[clave] = r.stdout.strip() if r.returncode == 0 else ""
    return cache[clave]


FILTRO_VOZ = (
    # highpass: quita retumbe | afftdn: ruido de fondo | acompressor: empareja voces | equalizer: claridad
    # | deesser: suaviza las "s" que silban | loudnorm: volumen base (la mezcla final se vuelve a masterizar)
    "highpass=f=80,afftdn=nr=10:nf=-40:tn=1,"
    "acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,"
    "equalizer=f=250:t=q:w=1.0:g=-1.5,equalizer=f=3500:t=q:w=1.2:g=2,deesser=i=0.3,"
    "loudnorm=I=-15:TP=-2:LRA=11"
)


def paso_voz(video: str, carpeta: str, modo: str) -> str:
    destino = os.path.join(carpeta, f"voz_{modo}.wav")
    if os.path.exists(destino):
        return destino
    base = ["ffmpeg", "-y", "-v", "error", "-i", video, "-map", "0:a:0", "-ar", "48000", "-ac", "2"]
    tmp = destino + ".tmp.wav"
    if modo == "limpio":
        r = subprocess.run(base + ["-af", FILTRO_VOZ, tmp], capture_output=True, text=True)
        if r.returncode != 0:
            print("    (No se pudo limpiar el audio; sigo con el audio original.)")
            modo = "original"
    if modo == "original":
        correr(base + [tmp], "No pude sacar el audio del video.")
    os.replace(tmp, destino)
    return destino


def plan_encuadre(formato: str, encuadre: str, d: Dict, cfg: Dict) -> str:
    f = cfg["formatos"][formato]
    enc = encuadre or f.get("encuadre", "auto")
    if formato == "tv":
        return "completo"  # en TV la imagen nunca se recorta
    if enc == "auto":
        return "relleno" if d["ancho"] > d["alto"] * 1.05 else "recorte"
    return enc


def filtro_video(formato: str, encuadre: str, cfg: Dict, fps: int, color: str, rx: float) -> str:
    W, H = cfg["formatos"][formato]["ancho"], cfg["formatos"][formato]["alto"]
    pre = f"fps={fps}" + (f",{color}" if color else "")
    if encuadre == "completo":
        # imagen completa; si no es del mismo formato, los lados se rellenan con el mismo video difuminado
        return (f"[0:v]{pre},split=2[a][b];"
                f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:3,eq=brightness=-0.15[fondo];"
                f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[frente];"
                f"[fondo][frente]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v]")
    if encuadre == "relleno":
        # video horizontal dentro de un formato más alto: video completo arriba del centro, fondo difuminado,
        # y espacio abajo para los subtítulos. En reel se usa un poco más alto (recortando los lados, centrado en la cara).
        if formato == "reel":
            frente = f"scale=-2:880:flags=lanczos,crop='min(iw,{W})':880:(iw-min(iw\\,{W}))*{rx:.3f}:0"
            centro = 0.41
        else:
            frente = f"scale={W}:-2:flags=lanczos"
            centro = 0.42
        return (f"[0:v]{pre},split=2[a][b];"
                f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:3,eq=brightness=-0.12:saturation=1.2[fondo];"
                f"[b]{frente},setsar=1[frente];"
                f"[fondo][frente]overlay=(W-w)/2:max(0\\,{H}*{centro}-h/2),setsar=1,format=yuv420p[v]")
    # recorte: llena todo el cuadro, centrado en la cara
    return (f"[0:v]{pre},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{H}:(in_w-{W})*{rx:.3f}:(in_h-{H})/2,setsar=1,format=yuv420p[v]")


def paso_preparar(video: str, voz: str, carpeta: str, filtro: str) -> str:
    destino = os.path.join(carpeta, f"video_{huella_texto(filtro, VERSION_CACHE)[:12]}.mp4")
    if os.path.exists(destino):
        return destino
    tmp = destino + ".tmp.mp4"
    correr(
        ["ffmpeg", "-y", "-v", "error", "-i", video, "-i", voz, "-filter_complex", filtro,
         # "todo intra" (-g 1): cada cuadro se puede sacar sin decodificar los anteriores. Así lo hacen los editores pro con
         # sus archivos intermedios. Medido: con GOP largo el extractor de Remotion se caía una y otra vez en un Mac de
         # 8 GB ("Request closed"); con todo intra, la misma parte salió al primer intento.
         "-map", "[v]", "-map", "1:a:0", "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-g", "1", "-bf", "0",
         "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", tmp],
        "No pude preparar el video.", "Si el color automático falla, prueba con --color no.",
    )
    os.replace(tmp, destino)
    return destino


def paso_transcribir(voz: str, nombre: str, huella: str, a: argparse.Namespace) -> str:
    destino = ruta("trabajo", f"{nombre}_transcripcion.json")
    params = {"huella": huella, "modelo": a.modelo, "idioma": a.idioma, "pistas": a.pistas}
    previo = leer_json(destino)
    if previo and not a.sin_cache:
        mismos = all(previo.get(k) == v for k, v in params.items())
        if mismos or (a.reusar and previo.get("huella") in (None, huella)):
            return destino
    correr([PY, ruta("scripts", "transcribe.py"), voz, destino, "--modelo", a.modelo, "--idioma", a.idioma,
            "--pistas", a.pistas],
           "Whisper no pudo transcribir el video.",
           "Si dice que falta el modelo, conéctate a internet una vez (lo descarga solo) o corre instalar.command.")
    datos = leer_json(destino)
    datos.update(params)
    escribir_json(destino, datos)
    return destino


def paso_plan(a, trans: str, caras_ruta: str, encuadre: str, cfg: Dict, nombre: str) -> Dict:
    f = cfg["formatos"][a.formato]
    cmd = [PY, ruta("scripts", "plan_edit.py"), trans, ruta("public", "edit.json"),
           "--fps", str(cfg["fps"]), "--silencio", a.silencio, "--quitar", a.quitar, "--titulo", a.titulo,
           "--extras", a.extras, "--encuadre", encuadre, "--ancho", str(f["ancho"]), "--alto", str(f["alto"]),
           "--formato", a.formato, "--caras", caras_ruta, "--original", a.video, "--estilo", a.estilo]
    if a.subtitulos:
        cmd += ["--subtitulos", a.subtitulos]
    r = correr(cmd, "No pude armar el plan de edición.",
               "Revisa que el archivo de extras sea JSON válido (comas y comillas).")
    for linea in r.stdout.strip().splitlines():
        print("    " + linea)
    plan = leer_json(ruta("public", "edit.json"))
    shutil.copy2(ruta("public", "edit.json"), ruta("trabajo", f"{nombre}_edit.json"))
    return plan


def paso_musica(plan: Dict, huella: str) -> Dict:
    m = plan.get("musica") or {}
    if not m.get("animo"):
        return plan
    dur = plan["durationInFrames"] / plan["fps"]
    semilla = int(huella[:6], 16) % 100000 if m.get("semilla") is None else int(m["semilla"])
    destino = ruta("public", "musica", f"auto_{m['animo']}_{semilla}_{dur:.2f}.wav")
    if not os.path.exists(destino):
        r = subprocess.run([PY, ruta("scripts", "musica.py"), "--animo", m["animo"], "--duracion", f"{dur:.3f}",
                            "--salida", destino, "--semilla", str(semilla)], capture_output=True, text=True, cwd=RAIZ)
        if r.returncode != 0:
            print("    (No se pudo componer la música; sigo sin música.)")
            plan.pop("musica", None)
            escribir_json(ruta("public", "edit.json"), plan)
            return plan
    plan["musica"]["archivo"] = os.path.relpath(destino, ruta("public"))
    escribir_json(ruta("public", "edit.json"), plan)
    print(f"    Música original: {m['animo']} ({dur:.0f} s, semilla {semilla}).")
    return plan


def memoria_gb() -> Dict[str, float]:
    """RAM total y la que se puede usar ya (libre + inactiva), en GB. Solo macOS; en otro sistema devuelve 0."""
    try:
        total = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout) / 1e9
        vm = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
        pagina = int((re.search(r"page size of (\d+)", vm) or [0, 16384])[1])
        libres = sum(int(m) for m in re.findall(r"Pages (?:free|inactive|speculative):\s+(\d+)", vm))
        return {"total": total, "disponible": libres * pagina / 1e9}
    except (ValueError, OSError):
        return {"total": 0.0, "disponible": 0.0}


def flags_memoria(mem: Dict[str, float]) -> List[str]:
    """Hilos y caché de Remotion según la memoria. Medido en un Mac de 8 GB lleno: con los valores por defecto
    (4 hilos, caché de hasta 1,4 GB) el sistema se quedaba sin memoria y una parte de 10 s tardaba 16 min."""
    if not mem["total"]:
        return []
    if mem["total"] <= 8.6 or mem["disponible"] < 2.5:
        return ["--concurrency", "2", "--offthreadvideo-cache-size-in-bytes", str(256 * 1024 * 1024)]
    if mem["total"] <= 16.5:
        return ["--concurrency", "4", "--offthreadvideo-cache-size-in-bytes", str(768 * 1024 * 1024)]
    return []


def flags_calidad(q: Dict) -> List[str]:
    f = ["--codec", "h264", "--crf", str(q["crf"]), "--x264-preset", q["x264Preset"], "--pixel-format", "yuv420p",
         "--color-space", "bt709", "--image-format", q["imagen"], "--log", "error"] + flags_memoria(memoria_gb())
    if q["imagen"] == "jpeg":
        f += ["--jpeg-quality", str(q["calidadJpeg"])]
    if q.get("escala", 1) != 1:
        f += ["--scale", str(q["escala"])]
    return f


def matar_arbol(pid: int) -> None:
    """Cierra un proceso y TODOS sus descendientes (Remotion abre un navegador con varios procesos que, si no,
    quedarían vivos gastando memoria)."""
    def hijos(p: int) -> List[int]:
        r = subprocess.run(["pgrep", "-P", str(p)], capture_output=True, text=True)
        directos = [int(x) for x in r.stdout.split()]
        return directos + [n for h in directos for n in hijos(h)]

    for p in [pid] + hijos(pid):
        try:
            os.kill(p, 9)
        except (ProcessLookupError, PermissionError):
            pass


def render_parte(bundle: str, archivo: str, ini: int, fin: int, q: Dict, p: int, n_partes: int, pasos: Pasos,
                 intentos: int = 4) -> None:
    """Renderiza una parte. Si Remotion falla o se queda colgado (pasa a veces: el extractor de cuadros se cae y el
    proceso espera para siempre), se corta por tiempo y se reintenta. Al final se cuentan los cuadros de verdad."""
    cuadros = fin - ini + 1
    limite = max(1800, cuadros * 6.0)  # muy por encima de lo normal (~0,1–1 s por cuadro)
    cmd = ["npx", "remotion", "render", bundle, "Edit", archivo, f"--frames={ini}-{fin}", "--muted",
           "--timeout", "900000"] + flags_calidad(q)  # 15 min por cuadro: con poca memoria hay pausas largas
    detalle = ""
    for intento in range(1, intentos + 1):
        proc = subprocess.Popen(cmd, cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                start_new_session=True)
        try:
            salida, error = proc.communicate(timeout=limite)
            ok = proc.returncode == 0 and medios.contar_cuadros(archivo) == cuadros
            detalle = "\n".join((error or salida or "").strip().splitlines()[-12:]) or f"cuadros: {medios.contar_cuadros(archivo)}"
            if not ok:  # registro completo para diagnosticar (queda junto a las partes)
                with open(archivo + f".intento{intento}.log", "w") as f:
                    f.write(f"codigo {proc.returncode}\n{salida}\n{error}")
        except subprocess.TimeoutExpired:
            matar_arbol(proc.pid)  # se cierra Remotion y su navegador
            proc.communicate()
            ok, detalle = False, f"Se quedó colgado más de {limite:.0f} s."
        except KeyboardInterrupt:
            matar_arbol(proc.pid)
            raise
        if ok:
            return
        if intento < intentos:
            pasos.nota(f"(La parte {p + 1} falló; reintento {intento} de {intentos - 1}…)")
    raise ErrorEditor(f"El render se detuvo en la parte {p + 1} de {n_partes} (falló {intentos} veces).",
                      "Vuelve a correr el mismo comando: sigue desde esta parte (las anteriores ya están guardadas). "
                      "Si vuelve a fallar, prueba con --calidad preview para ver si el problema es de memoria.", detalle)


def paso_render(plan: Dict, cfg: Dict, a, nombre: str, salida: str, pasos: Pasos) -> Dict:
    q = cfg["calidades"][a.calidad]
    fps, total = plan["fps"], plan["durationInFrames"]
    clave = huella_texto(
        huella_archivo(ruta("public", "edit.json")),
        huella_carpeta(ruta("src")),
        huella_carpeta(ruta("public"), excluir=("portada",)),
        q, VERSION_CACHE,
    )[:12]
    carpeta = ruta("trabajo", "render", f"{nombre}_{a.formato}_{a.calidad}_{clave}")
    # partes viejas de este mismo video/formato con otro plan: ya no sirven
    prefijo = f"{nombre}_{a.formato}_{a.calidad}_"
    for viejo in os.listdir(ruta("trabajo", "render")) if os.path.isdir(ruta("trabajo", "render")) else []:
        if viejo.startswith(prefijo) and not viejo.endswith(clave):
            shutil.rmtree(ruta("trabajo", "render", viejo), ignore_errors=True)
    os.makedirs(carpeta, exist_ok=True)
    segundos = float(os.environ.get("EDITOR_SEGUNDOS_POR_PARTE", cfg["render"]["segundosPorParte"]))
    por_parte = max(1, int(segundos * fps))
    partes = [(i, min(i + por_parte, total) - 1) for i in range(0, total, por_parte)]

    hechas = [p for p in range(len(partes)) if os.path.exists(os.path.join(carpeta, f"parte_{p:03d}.ok"))]
    if hechas:
        pasos.nota(f"Reanudando: {len(hechas)} de {len(partes)} partes ya estaban listas.")

    bundle = os.path.join(carpeta, "bundle")
    video_bundle = os.path.join(bundle, "public", plan["video"])
    completo = os.path.exists(os.path.join(bundle, "index.html")) and os.path.exists(video_bundle) and \
        os.path.getsize(video_bundle) == os.path.getsize(ruta("public", plan["video"]))
    if not completo:  # falta o quedó incompleto (p. ej. sin el video): se rehace
        shutil.rmtree(bundle, ignore_errors=True)
        correr(["npx", "remotion", "bundle", "src/index.ts", "--out-dir", bundle, "--log", "error"],
               "Remotion no pudo preparar el proyecto (error en el código de src/).",
               "Corre: npx tsc --noEmit  para ver el error, o vuelve a la versión anterior con git.")

    mem = memoria_gb()
    if mem["total"] and mem["disponible"] < 2.0:
        pasos.nota(f"Ojo: hay poca memoria libre ({mem['disponible']:.1f} GB de {mem['total']:.0f} GB). El render va a ir más lento; "
                   "cerrar Chrome, Spotify u otras apps pesadas lo acelera mucho.")
    t0 = time.time()
    for p, (ini, fin) in enumerate(partes):
        ok = os.path.join(carpeta, f"parte_{p:03d}.ok")
        archivo = os.path.join(carpeta, f"parte_{p:03d}.mp4")
        if os.path.exists(ok):
            continue
        if not os.path.exists(video_bundle):  # alguien borró el video de la copia: se repone antes de seguir
            pasos.nota("(El video preparado desapareció de la copia de Remotion; lo vuelvo a poner.)")
            copiar(ruta("public", plan["video"]), video_bundle)
        render_parte(bundle, archivo, ini, fin, q, p, len(partes), pasos)
        with open(ok, "w") as f:
            f.write(str(fin - ini + 1))
        hechos = fin + 1
        vel = hechos / max(0.1, time.time() - t0) if not hechas else 0
        resto = f", faltan ~{(total - hechos) / vel:.0f} s" if vel else ""
        pasos.nota(f"Parte {p + 1}/{len(partes)} lista ({hechos / fps:.0f} de {total / fps:.0f} s de video{resto}).")

    # audio: la mezcla completa (voz + música con ducking + efectos) de una sola vez, exacta a la muestra
    # (scripts/mezcla.py; así no hay "clics" entre partes y no hay que recorrer todos los cuadros otra vez)
    mezcla_wav = os.path.join(carpeta, "mezcla.wav")
    try:
        mezcla.mezclar_a_archivo(ruta("public", "edit.json"), mezcla_wav)
    except Exception as e:
        raise ErrorEditor("No pude mezclar el audio.", "Revisa que existan los archivos de música/efectos del plan.", str(e))
    lista = os.path.join(carpeta, "partes.txt")
    with open(lista, "w") as f:
        for p in range(len(partes)):
            f.write(f"file 'parte_{p:03d}.mp4'\n")
    video_solo = os.path.join(carpeta, "video.mp4")
    correr(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", video_solo],
           "No pude unir las partes del video.")
    master = os.path.join(carpeta, "master.m4a")
    medida = audio.masterizar(mezcla_wav, master, cfg["audio"]["lufs"], cfg["audio"]["picoMaximoDbtp"], q["audioKbps"])
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    tmp = salida + ".tmp.mp4"
    correr(["ffmpeg", "-y", "-v", "error", "-i", video_solo, "-i", master, "-map", "0:v:0", "-map", "1:a:0",
            "-c", "copy", "-movflags", "+faststart", tmp], "No pude juntar el video con el audio.")
    os.replace(tmp, salida)
    pasos.nota(f"Audio: {medida['antes_lufs']:.1f} → {medida['lufs']:.1f} LUFS, pico real {medida['pico_dbtp']:.1f} dBTP.")
    return {"carpeta": carpeta, "bundle": bundle, "audio": medida}


def paso_portada(a, caras_ruta: str, color: str) -> bool:
    r = subprocess.run([PY, ruta("scripts", "portada.py"), a.video, caras_ruta, "--extras", a.extras,
                        "--formato", a.formato, "--color", color], capture_output=True, text=True, cwd=RAIZ)
    return r.returncode == 0


def control_calidad(salida: str, plan: Dict, cfg: Dict, a, medida_audio: Dict) -> List[str]:
    r = subprocess.run([PY, ruta("scripts", "control_calidad.py"), salida, ruta("public", "edit.json"),
                        "--escala", str(cfg["calidades"][a.calidad].get("escala", 1)),
                        "--lufs", str(cfg["audio"]["lufs"]), "--pico", str(cfg["audio"]["picoMaximoDbtp"])],
                       capture_output=True, text=True, cwd=RAIZ)
    print(r.stdout.rstrip())
    return [l for l in r.stdout.splitlines() if l.strip().startswith("✗")]


# ---------------------------------------------------------------- principal
def principal(argv: List[str]) -> int:
    cfg = cargar_config()
    a = leer_opciones(argv, cfg)
    pasos = Pasos(4 if a.solo_preparar else 7)
    inicio = time.time()

    pasos("Revisando herramientas y el video...")
    revisar_herramientas()
    d = revisar_video(a.video)
    if a.extras and not os.path.exists(a.extras):
        raise ErrorEditor(f"No encuentro el archivo de extras '{a.extras}'.", "Revisa el nombre (está en trabajo/?).")
    nombre = os.path.splitext(os.path.basename(a.video))[0]
    huella = huella_archivo(a.video)
    carpeta = ruta("trabajo", "cache", f"{nombre}_{huella[:10]}")
    if a.sin_cache and os.path.isdir(carpeta):
        shutil.rmtree(carpeta)
    os.makedirs(carpeta, exist_ok=True)
    cache_json = os.path.join(carpeta, "cache.json")
    cache = leer_json(cache_json) or {}
    fps_in = medios.fps_de_trabajo(d["fps"])
    formato = cfg["formatos"][a.formato]
    pasos.nota(f"{d['ancho']}x{d['alto']}, {d['fps']:g} fps, {d['duracion']:.0f} s → {a.formato} "
               f"{formato['ancho']}x{formato['alto']} a {cfg['fps']} fps, estilo {a.estilo or 'ninguno'}, calidad {a.calidad}.")
    if d["duracion"] > 180 and not a.solo_preparar:
        pasos.nota("Es un video de más de 3 minutos: el render puede tardar bastante.")

    pasos("Caras y color automático...")
    caras = paso_caras(a.video, nombre, huella, a.sin_cache)
    color = paso_color(a.video, a.color, cache)
    escribir_json(cache_json, cache)
    if color:
        pasos.nota(f"Color: corrección automática + look \"{a.color}\".")

    pasos("Preparando voz y video...")
    voz = paso_voz(a.video, carpeta, a.audio)
    encuadre = plan_encuadre(a.formato, a.encuadre, d, cfg)
    try:
        preparado = paso_preparar(a.video, voz, carpeta, filtro_video(a.formato, encuadre, cfg, fps_in, color, caras.get("recorte_x", 0.5)))
    except ErrorEditor:
        if not color:
            raise
        pasos.nota("(El color automático falló en este video; sigo sin corrección de color.)")
        preparado = paso_preparar(a.video, voz, carpeta, filtro_video(a.formato, encuadre, cfg, fps_in, "", caras.get("recorte_x", 0.5)))
    copiar(preparado, ruta("public", "input.mp4"))
    trans = paso_transcribir(voz, nombre, huella, a)

    pasos("Plan de edición, sonidos y música...")
    plan = paso_plan(a, trans, ruta("trabajo", f"{nombre}_caras.json"), encuadre, cfg, nombre)
    plan = paso_musica(plan, huella)
    if a.solo_preparar:
        print(f"LISTO (sin renderizar): public/edit.json. Revisa con: bash scripts/revisar.sh {nombre}")
        return 0

    salida = a.salida or ruta("salida", f"{nombre}_{a.formato}{'_preview' if a.calidad == 'preview' else ''}.mp4")
    portada_ok = a.calidad != "preview" and paso_portada(a, ruta("trabajo", f"{nombre}_caras.json"), color)

    pasos(f"Renderizando a {cfg['fps']} fps por partes (calidad {a.calidad})...")
    r = paso_render(plan, cfg, a, nombre, salida, pasos)

    pasos("Portada...")
    if portada_ok:
        destino = os.path.splitext(salida)[0] + "_portada.jpg"
        rr = subprocess.run(["npx", "remotion", "still", r["bundle"], "Portada", destino, "--log", "error"],
                            capture_output=True, text=True, cwd=RAIZ)
        pasos.nota(f"Portada: {os.path.relpath(destino, RAIZ)}" if rr.returncode == 0 else "(No se pudo hacer la portada.)")
    else:
        pasos.nota("(En calidad preview no se hace portada.)" if a.calidad == "preview" else "(No se pudo hacer la portada.)")

    pasos("Control de calidad...")
    problemas = control_calidad(salida, plan, cfg, a, r["audio"])
    shutil.rmtree(r["carpeta"], ignore_errors=True)  # partes temporales: ya no se necesitan
    minutos, segundos = divmod(int(time.time() - inicio), 60)
    print(f"    Tiempo por paso: {pasos.resumen()}")
    print(f"LISTO: {os.path.relpath(salida, RAIZ)}  (tardó {minutos} min {segundos} s)")
    return 1 if problemas else 0


class Candado:
    """Evita correr dos ediciones a la vez (las dos escribirían el mismo public/edit.json)."""

    def __init__(self):
        self.archivo = ruta("trabajo", ".editando")

    def __enter__(self):
        os.makedirs(os.path.dirname(self.archivo), exist_ok=True)
        try:
            pid = int(open(self.archivo).read().strip() or 0)
        except (FileNotFoundError, ValueError):
            pid = 0
        if pid and pid != os.getpid():
            try:
                os.kill(pid, 0)  # ¿sigue vivo ese proceso?
                raise ErrorEditor("Ya hay otra edición corriendo en este momento.",
                                  "Espera a que termine (o ciérrala) y vuelve a correr el comando.")
            except ProcessLookupError:
                pass  # quedó de una edición que se cerró de golpe: se puede seguir
        with open(self.archivo, "w") as f:
            f.write(str(os.getpid()))
        return self

    def __exit__(self, *_):
        try:
            os.remove(self.archivo)
        except FileNotFoundError:
            pass


def _al_cerrar(signum, frame):
    # cerrar la terminal o `kill` envían SIGTERM/SIGHUP: se trata igual que Ctrl+C, así también se cierra el render
    raise KeyboardInterrupt


def main() -> None:
    import signal

    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _al_cerrar)
    # si se lanzó en segundo plano desde un script, Ctrl+C llega "ignorado": se reactiva siempre
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        if any(x in sys.argv for x in ("-h", "--help")):
            sys.exit(principal(sys.argv[1:]))
        with Candado():
            sys.exit(principal(sys.argv[1:]))
    except ErrorEditor as e:
        print("\n" + "=" * 60, file=sys.stderr)
        print(f"  PROBLEMA: {e.que}", file=sys.stderr)
        if e.como_arreglar:
            print(f"  QUÉ HACER: {e.como_arreglar}", file=sys.stderr)
        if e.detalle:
            print("  Detalle técnico (para Claude):", file=sys.stderr)
            for linea in e.detalle.splitlines():
                print("    " + linea, file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\nDetenido. Para seguir donde quedó, vuelve a correr el mismo comando.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
