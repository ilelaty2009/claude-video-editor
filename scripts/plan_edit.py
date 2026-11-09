"""Convierte la transcripción en un plan de edición (public/edit.json) para Remotion.

- Quita los silencios más largos que --silencio (por defecto 0.3 s).
- Deja un pequeño margen antes y después de cada frase para que no suene cortado.
- Re-calcula el tiempo de cada palabra en el video final (para los subtítulos).
- Opcional: --quitar "palabra1,palabra2" borra muletillas (eh, este, o sea...).
- Opcional: --extras archivo.json con efectos (ver abajo).

Formato de extras (todos los campos son opcionales; los tiempos son del video ORIGINAL, en segundos):
{
  "titulo": "Gancho del inicio",
  "recortar": {"desde": 0, "hasta": 60},
  "quitar": [{"desde": 12.4, "hasta": 15.1}],   # tramos a borrar: repeticiones, falsos comienzos (ver detectar_repeticiones.py)
  "foco": {"x": 0.5, "y": 0.35},                 # dónde está la cara (0-1). Si no lo pones, se usa trabajo/X_caras.json
  "gancho": {"desde": 41.0, "hasta": 45.7},      # "cold open": la mejor frase se pone AL INICIO como adelanto (3-6 s)
  "ritmo": 5,                                    # máx. segundos sin ningún cambio visual; si pasa, se agrega un acercamiento lento solo (false = apagado)
  "musica": {"archivo": "musica/fondo.mp3", "volumen": 0.22, "volumenHablando": 0.07},  # archivo dentro de public/
  "correcciones": [{"buscar": "Jordan Islam", "reemplazo": "Dar al-Islam"}],
  "destacadas": [{"palabra": "polymath", "emoji": "🤯", "color": "#39FF88", "zoom": true}],
  "capitulos": [{"desde": 10.9, "texto": "📜 ¿Qué es Dar al-Islam?"}],
  "sfx": true,
  "barraProgreso": true,
  "look": "cine",            # "tiktok" (subtítulos grandes amarillos, por defecto) o "cine" (una línea limpia)
  "escenas": [               # escenas animadas (ver CLAUDE.md -> "Escenas animadas")
    {"tipo": "titular", "desde": 12.0, "hasta": 15.5, "arriba": "SO THE BUSINESS",
     "lineas": [{"texto": "COULD ACTUALLY"}, {"texto": "WORK.", "color": "#FFC94D", "en": 14.2}]},
    {"tipo": "chat", "desde": 2.0, "hasta": 5.0, "texto": "Write me a business plan"},
    {"tipo": "miniatura", "desde": 16, "hasta": 19, "lineas": [{"texto": "THE AGENTS", "color": "#5CC8FF"}]},
    {"tipo": "engranajes", "desde": 20, "hasta": 23, "lineas": [{"texto": "GRINDS"}]},
    {"tipo": "tarjetas", "desde": 8, "hasta": 11, "titulo": "\"THIS IS...\"",
     "tarjetas": [{"texto": "RIGHT", "tipo": "si"}, {"texto": "WRONG", "tipo": "no", "en": 9.4}]},
    {"tipo": "iconos", "desde": 5, "hasta": 8, "centro": "BUSINESS PLAN", "iconos": ["🤖", "⚙️"], "robots": 8},
    {"tipo": "zoom", "desde": 24, "hasta": 27, "escala": 1.35, "x": 0.5, "y": 0.35}
  ]
}

Uso: python scripts/plan_edit.py <transcript.json> <edit.json> [--silencio 0.3] [--extras extras.json]
"""
import argparse
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import medios  # noqa: E402


def cargar_config():
    """editor.config.json: estilos (clase, tiktok, youtube, documental), formatos y fps."""
    with open(os.path.join(RAIZ, "editor.config.json"), encoding="utf-8") as f:
        return json.load(f)


def norm(t: str) -> str:
    return re.sub(r"[^\wáéíóúñü]", "", t.lower())


def aplicar_correcciones(words, correcciones):
    """Reemplaza secuencias de palabras (comparando sin mayúsculas ni signos) manteniendo los tiempos."""
    for c in correcciones:
        buscar = [norm(x) for x in c["buscar"].split() if norm(x)]
        nuevas = c.get("reemplazo", "").split()
        if not buscar:
            continue
        i = 0
        while i <= len(words) - len(buscar):
            if [norm(w["text"]) for w in words[i : i + len(buscar)]] == buscar:
                ini, fin = words[i]["start"], words[i + len(buscar) - 1]["end"]
                prob = min(w.get("prob", 1) for w in words[i : i + len(buscar)])
                if nuevas:
                    paso = (fin - ini) / len(nuevas)
                    repl = [
                        {"text": t, "start": round(ini + k * paso, 3), "end": round(ini + (k + 1) * paso, 3), "prob": prob}
                        for k, t in enumerate(nuevas)
                    ]
                else:
                    repl = []
                words[i : i + len(buscar)] = repl
                i += max(len(repl), 1)
            else:
                i += 1
    return words


def ruta_foco(caras, segmentos, fps, ajustar, paso_s=0.5):
    """Recorrido suave de la cara principal en el video EDITADO: [{"f": cuadro, "x", "y"}].

    Usa las muestras de seguir_cara.py (1 por segundo), escoge la cara más cercana a la principal, suaviza
    (promedio de 3 muestras, para que la cámara no tiemble) y pasa los tiempos del original al video editado.
    """
    muestras = caras.get("muestras") or []
    fx0 = float(caras["foco"]["x"])
    puntos = []
    for m in muestras:
        cerca = [c for c in m.get("caras", []) if abs(c["x"] - fx0) < 0.2]
        if cerca:
            c = min(cerca, key=lambda c: abs(c["x"] - fx0))
            puntos.append((float(m["t"]), c["x"], c["y"] - 0.15 * c["alto"]))
    if len(puntos) < 2:
        return []
    suaves = []
    for i in range(len(puntos)):
        ventana = puntos[max(0, i - 1) : i + 2]
        suaves.append((puntos[i][0], sum(p[1] for p in ventana) / len(ventana), sum(p[2] for p in ventana) / len(ventana)))

    def en(t):
        if t <= suaves[0][0]:
            return suaves[0][1:]
        for (t0, x0, y0), (t1, x1, y1) in zip(suaves, suaves[1:]):
            if t <= t1:
                k = (t - t0) / max(1e-6, t1 - t0)
                return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
        return suaves[-1][1:]

    ruta = []
    paso = max(1, int(round(paso_s * fps)))
    for sg in segmentos:
        for f in list(range(0, sg["durationInFrames"], paso)) + [sg["durationInFrames"] - 1]:
            x, y = ajustar(*en((sg["trimBefore"] + f) / fps))
            ruta.append({"f": sg["from"] + f, "x": x, "y": y})
    ruta.sort(key=lambda p: p["f"])
    return ruta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("out")
    ap.add_argument("--fps", type=int, default=0, help="cuadros por segundo (por defecto el de editor.config.json: 60)")
    ap.add_argument("--silencio", type=float, default=0.3, help="segundos de pausa que se cortan")
    ap.add_argument("--antes", type=float, default=0.08, help="margen antes de hablar (s)")
    ap.add_argument("--despues", type=float, default=0.15, help="margen después de hablar (s)")
    ap.add_argument("--quitar", default="", help="muletillas a borrar, separadas por coma")
    ap.add_argument("--titulo", default="")
    ap.add_argument("--extras", default="", help="archivo JSON con efectos")
    ap.add_argument("--encuadre", default="recorte")
    ap.add_argument("--ancho", type=int, default=1080)
    ap.add_argument("--alto", type=int, default=1920)
    ap.add_argument("--video", default="input.mp4", help="archivo dentro de public/")
    ap.add_argument("--caras", default="", help="trabajo/X_caras.json de seguir_cara.py (foco automático)")
    ap.add_argument("--original", default="", help="video original (para saber su forma al mover el foco)")
    ap.add_argument("--estilo", default="", help="clase | tiktok | youtube | documental")
    ap.add_argument("--formato", default="", help="tv | reel | cuadrado | retrato (para la zona segura)")
    ap.add_argument("--subtitulos", default="", help="tiktok | cine | caja | resaltado")
    args = ap.parse_args()
    cfg = cargar_config()
    args.fps = args.fps or int(cfg.get("fps", 60))

    data = json.load(open(args.transcript, encoding="utf-8"))
    extras = json.load(open(args.extras, encoding="utf-8")) if args.extras and os.path.exists(args.extras) else {}
    estilo = cfg["estilos"].get(args.estilo or extras.get("estilo", ""), {})
    for clave, valor in estilo.items():
        if clave != "color":
            extras.setdefault(clave, valor)  # lo que diga extras manda sobre el estilo
    if args.subtitulos:
        extras["subtitulos"] = args.subtitulos  # la línea de comandos manda sobre todo
    total = float(data["duration"])
    fillers = {norm(x) for x in args.quitar.split(",") if x.strip()}
    words = [dict(w) for w in data["words"] if norm(w["text"]) not in fillers]
    words = aplicar_correcciones(words, extras.get("correcciones", []))
    if "recortar" in extras:
        d0 = float(extras["recortar"].get("desde", 0))
        d1 = float(extras["recortar"].get("hasta", total))
        words = [w for w in words if w["start"] >= d0 and w["end"] <= d1]
    for q in extras.get("quitar", []):
        q0, q1 = float(q["desde"]), float(q["hasta"])
        words = [w for w in words if not (q0 <= (w["start"] + w["end"]) / 2 <= q1)]
    if not words:
        raise SystemExit("No se detectó voz en el video.")

    fps = args.fps

    def armar(ws, inicio_frame):
        """Agrupa palabras en bloques de habla (corta pausas > silencio) y los vuelve segmentos + subtítulos."""
        if not ws:
            return [], [], inicio_frame
        blocks = []
        cur = [ws[0]]
        for w in ws[1:]:
            if w["start"] - cur[-1]["end"] > args.silencio:
                blocks.append(cur)
                cur = [w]
            else:
                cur.append(w)
        blocks.append(cur)
        segs, caps = [], []
        out_f = inicio_frame
        prev_end_f = 0
        for b in blocks:
            s0 = max(b[0]["start"] - args.antes, 0.0)
            e0 = min(b[-1]["end"] + args.despues, total)
            s_f = max(int(round(s0 * fps)), prev_end_f)  # nunca solapar con el anterior
            e_f = int(round(e0 * fps))
            if e_f - s_f < 2:
                continue
            segs.append({"trimBefore": s_f, "durationInFrames": e_f - s_f, "from": out_f})
            for w in b:
                w0 = (w["start"] * fps - s_f) / fps + out_f / fps
                w1 = (w["end"] * fps - s_f) / fps + out_f / fps
                caps.append(
                    {
                        "text": " " + w["text"],
                        "startMs": round(w0 * 1000),
                        "endMs": round(w1 * 1000),
                        "timestampMs": round((w0 + w1) / 2 * 1000),
                        "confidence": w.get("prob"),
                    }
                )
            out_f += e_f - s_f
            prev_end_f = e_f
        return segs, caps, out_f

    # 1) "gancho" (cold open): la frase más fuerte va primero, como adelanto; luego empieza el video normal
    gancho_frames = 0
    seg_gancho, cap_gancho = [], []
    if extras.get("gancho"):
        g0, g1 = float(extras["gancho"]["desde"]), float(extras["gancho"]["hasta"])
        palabras_g = [w for w in words if g0 <= (w["start"] + w["end"]) / 2 <= g1]
        seg_gancho, cap_gancho, gancho_frames = armar(palabras_g, 0)

    # 2) el video completo, empezando después del gancho
    segments, captions, out_frame = armar(words, gancho_frames)
    # 3) palabras destacadas (color, emoji, zoom)
    for d in extras.get("destacadas", []):
        objetivo = [norm(x) for x in d["palabra"].split() if norm(x)]
        if not objetivo:
            continue
        for i in range(len(captions) - len(objetivo) + 1):
            if [norm(c["text"]) for c in captions[i : i + len(objetivo)]] == objetivo:
                for k in range(len(objetivo)):
                    captions[i + k]["color"] = d.get("color", "#39FF88")
                    captions[i + k]["destacada"] = True
                if d.get("emoji"):
                    captions[i]["emoji"] = d["emoji"]
                if d.get("zoom", True):
                    captions[i]["zoom"] = True

    # 4) capítulos: pasar tiempo del original al tiempo del video editado
    def a_salida(t: float) -> float:
        f = t * fps
        for seg in segments:
            if f < seg["trimBefore"]:
                return seg["from"] / fps  # cayó en un silencio cortado: empieza con el siguiente bloque
            if f < seg["trimBefore"] + seg["durationInFrames"]:
                return (seg["from"] + f - seg["trimBefore"]) / fps
        return out_frame / fps

    def a_ms(t) -> int:
        return round(a_salida(float(t)) * 1000)

    escenas = []
    for e in extras.get("escenas", []):
        e = dict(e)
        desde = float(e.pop("desde"))
        hasta = float(e.pop("hasta", desde + 3))
        e["desdeMs"], e["hastaMs"] = a_ms(desde), a_ms(hasta)
        if e["hastaMs"] - e["desdeMs"] < 300:  # quedó casi toda en un silencio cortado
            e["hastaMs"] = e["desdeMs"] + 1500
        for clave in ("lineas", "tarjetas", "items"):
            for item in e.get(clave, []) or []:
                if "en" in item:
                    item["enMs"] = a_ms(item.pop("en"))
        escenas.append(e)
    escenas.sort(key=lambda e: e["desdeMs"])

    capitulos = [
        {"desdeMs": round(a_salida(float(c["desde"])) * 1000), "texto": c["texto"]} for c in extras.get("capitulos", [])
    ]

    # sonidos especiales pedidos en los extras: [{"en": 12.3, "archivo": "sfx/real/aplausos.wav", "vol": 0.3}]
    # (se calculan ANTES de pegar el gancho, porque a_salida usa los segmentos del video normal)
    sonidos_extra = [
        {"golpe": int(round(a_salida(float(x["en"])) * fps)), "archivo": x["archivo"], "vol": float(x.get("vol", 0.3)),
         "que": x.get("que", "sonido especial")}
        for x in extras.get("sonidos", [])
    ]

    # 5) RITMO ("pattern interrupts", como los editores de MrBeast): que nunca pasen más de N segundos sin un cambio
    #    visual. Cuenta como cambio: un corte, una escena, un zoom de golpe o un capítulo. Si hay un hueco largo,
    #    se agrega un acercamiento lento automático para que la imagen no se quede quieta.
    ritmo = extras.get("ritmo", 5)
    cambios = sorted(
        {sg["from"] for sg in segments}
        | {round(e["desdeMs"] / 1000 * fps) for e in escenas}
        | {round(e["hastaMs"] / 1000 * fps) for e in escenas}
        | {round(c["startMs"] / 1000 * fps) for c in captions if c.get("zoom")}
        | {round(c["desdeMs"] / 1000 * fps) for c in capitulos}
        | {gancho_frames, out_frame}
    )
    huecos = [(a, b) for a, b in zip(cambios, cambios[1:]) if b > a]
    automaticos = 0
    if ritmo:
        limite = float(ritmo) * fps
        for a, b in huecos:
            if b - a > limite:
                escenas.append({"tipo": "zoom", "desdeMs": round(a / fps * 1000), "hastaMs": round(b / fps * 1000), "escala": 1.12, "auto": True})
                automaticos += 1
        escenas.sort(key=lambda e: e["desdeMs"])
    promedio = (out_frame - gancho_frames) / fps / max(1, len(huecos))
    mayor = max([(b - a) / fps for a, b in huecos] or [0])

    segments = seg_gancho + segments
    captions = cap_gancho + captions

    formato = cfg["formatos"].get(args.formato, {})
    edit = {
        "formato": args.formato or ("tv" if args.ancho > args.alto else "reel"),
        "zonaSegura": formato.get("zonaSegura", {"arriba": 0.06, "abajo": 0.08, "izquierda": 0.06, "derecha": 0.06}),
        "subtitulos": extras.get("subtitulos") or ("cine" if extras.get("look") == "cine" else "tiktok"),
        "video": args.video,
        "fps": fps,
        "width": args.ancho,
        "height": args.alto,
        "durationInFrames": out_frame,
        "encuadre": args.encuadre,
        "segments": segments,
        "captions": captions,
        "capitulos": capitulos,
        "sfx": bool(extras.get("sfx", False)),
        "barraProgreso": bool(extras.get("barraProgreso", extras.get("look") != "cine")),
        "look": extras.get("look", "tiktok"),
        "escenas": escenas,
    }
    if gancho_frames:
        edit["gancho"] = {"hastaFrame": gancho_frames}
    aspecto = None
    if args.original:
        try:
            d = medios.info(args.original)
            aspecto = d["ancho"] / d["alto"] if d["alto"] else None
        except Exception:
            aspecto = None

    def ajustar(fx, fy):
        """Pasa un punto del video original (0-1) a dónde quedó en el formato final."""
        salida_aspecto = args.ancho / args.alto
        if aspecto and args.encuadre in ("completo", "relleno"):
            if args.encuadre == "relleno":
                return 0.5, 0.4
            if aspecto < salida_aspecto:  # barras a los lados
                fx = 0.5 + (fx - 0.5) * aspecto / salida_aspecto
            else:  # barras arriba y abajo
                fy = 0.5 + (fy - 0.5) * salida_aspecto / aspecto
        elif args.encuadre == "recorte":
            fx = 0.5  # el recorte ya se centró en la cara
        return round(fx, 3), round(fy, 3)

    if extras.get("foco"):
        edit["foco"] = {"x": float(extras["foco"].get("x", 0.5)), "y": float(extras["foco"].get("y", 0.45))}
    elif args.caras and os.path.exists(args.caras):
        # foco automático (detector de caras), ajustado a cómo quedó el video en el formato final
        caras = json.load(open(args.caras, encoding="utf-8"))
        fx, fy = ajustar(float(caras["foco"]["x"]), float(caras["foco"]["y"]))
        edit["foco"] = {"x": fx, "y": fy}
        # SEGUIMIENTO DE CARA: dónde está la cara principal en cada momento (si la persona se mueve, los zooms la siguen)
        ruta = ruta_foco(caras, segments, fps, ajustar)
        if ruta:
            edit["focoRuta"] = ruta
    if extras.get("musica"):
        m = extras["musica"]
        m = {"archivo": m} if isinstance(m, str) else dict(m)
        if m.get("animo") and not m.get("archivo"):
            # música original: editar.sh la compone después con scripts/musica.py, del largo exacto del video
            m["archivo"] = "musica/auto.wav"
            edit["musica"] = m
        else:
            ruta = os.path.join(os.path.dirname(os.path.abspath(args.out)), m["archivo"])
            if os.path.exists(ruta):
                edit["musica"] = m
            else:
                print(f"AVISO: no encontré la música public/{m['archivo']}; sigo sin música.")
    if extras.get("cierre"):
        c = extras["cierre"] if isinstance(extras["cierre"], dict) else {}
        dur = int(round(float(c.get("segundos", 3.0)) * fps))
        edit["cierre"] = {
            "desdeFrame": out_frame,
            "titulo": c.get("titulo", "¡Gracias!"),
            "subtitulo": c.get("subtitulo", ""),
            "linea": c.get("linea", ""),
        }
        edit["durationInFrames"] = out_frame + dur
    titulo = extras.get("titulo") or args.titulo
    if titulo:
        edit["titulo"] = titulo
    edit["sonidosExtra"] = sonidos_extra
    # diseño de sonido al cuadro exacto (scripts/sonidos.py, método "Real SFX")
    try:
        import sys as _sys

        _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import sonidos

        base = os.path.basename(args.transcript).replace("_transcripcion.json", "")
        reporte = os.path.join(os.path.dirname(os.path.abspath(args.transcript)), f"{base}_sonidos.md")
        sonidos.poner_cues(edit, os.path.dirname(os.path.abspath(args.out)), reporte)
        n_real = sum(1 for c in edit["cues"] if c["real"])
        print(f"SONIDO: {len(edit['cues'])} efectos al cuadro exacto ({n_real} reales). Reporte: {reporte}")
    except Exception as err:
        edit["cues"] = []
        print(f"AVISO: no pude armar los efectos de sonido ({err}); el video sale sin efectos.")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(edit, f, ensure_ascii=False, indent=1)

    cut = total - out_frame / fps
    n_dest = sum(1 for c in captions if c.get("emoji") or c.get("zoom"))
    print(
        f"OK: {len(segments)} cortes, {total:.1f}s -> {out_frame / fps:.1f}s (se quitaron {cut:.1f}s), "
        f"{n_dest} momentos destacados, {len(capitulos)} capítulos, {len(escenas)} escenas, look {edit['look']}"
    )
    print(
        f"RITMO: un cambio visual cada {promedio:.1f} s en promedio; el hueco más largo mide {mayor:.1f} s"
        + (f"; agregué {automaticos} acercamientos automáticos" if automaticos else "")
        + (f". Gancho al inicio: {gancho_frames / fps:.1f} s" if gancho_frames else "")
    )


if __name__ == "__main__":
    main()
