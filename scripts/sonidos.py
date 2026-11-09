"""DISEÑO DE SONIDO al cuadro exacto (nuestra versión de "Real SFX").

Lee el plan del video (public/edit.json), encuentra cada momento que necesita un sonido (algo que aparece, una
transición, un número que cuenta, una tecla del chat, un título, un capítulo, el cierre…) y arma una LISTA DE CUES:
  {"f": cuadro donde empieza a sonar, "archivo": "sfx/whoosh.wav", "vol": 0.3, "que": "escena lista: ítem 2"}

Lo que lo hace sonar profesional (lo mismo que hace Real SFX):
  - ALINEA POR EL GOLPE: cada sonido tiene su punto más fuerte (un whoosh crece y luego cae). Se adelanta el sonido
    para que ese golpe caiga justo en el cuadro donde pasa la cosa en pantalla (picos medidos por scripts/oido.py).
  - SONIDOS REALES PRIMERO: si existe public/sfx/real/<tipo>.wav (bajado de Openverse con buscar_sonidos.py), lo usa;
    si no, usa el sintetizado de public/sfx/<tipo>.wav.
  - NO AMONTONA: si dos sonidos caen a menos de 3 cuadros, deja el más fuerte (salvo las teclas del chat).
  - DEBAJO DE LA VOZ: si alguien está hablando en ese momento, el efecto baja un 25 %.
Escribe además trabajo/X_sonidos.md: dónde quedó cada sonido y los 5 momentos que vale la pena escuchar.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Las animaciones de src/ se diseñaron contando cuadros a 30 fps (ver src/tiempo.ts). Aquí se calcula igual, en
# "cuadros de diseño", y al final se pasa al fps real del video (60): así sonido e imagen coinciden a cualquier fps.
FPS_DISENO = 30

PANTALLA_COMPLETA = {"engranajes", "tarjetas", "iconos", "cita", "numero", "lista", "linea_tiempo", "broll"}


def _ms2f(ms, fps):
    return int(round(ms / 1000 * fps))


def cues_de_escena(e, fps):
    """Los sonidos de una escena, igual que la animación de src/escenas/. Devuelve cuadros REALES (a `fps`)."""
    desde = _ms2f(e["desdeMs"], fps)
    k = fps / FPS_DISENO
    dur = max(8, _ms2f(e["hastaMs"] - e["desdeMs"], FPS_DISENO))  # en cuadros de diseño

    def en(ms, defecto):
        return _ms2f(ms - e["desdeMs"], FPS_DISENO) if ms is not None else defecto

    g = []
    t = e["tipo"]
    if t in PANTALLA_COMPLETA:
        entrada = e.get("entrada") or "suave"
        if entrada == "luz":
            g.append((0, "brillo", 0.28, "transición con luz"))
        elif entrada == "zoom":
            g.append((0, "riser", 0.16, "sube antes del zoom"))
            g.append((0, "impacto", 0.22, "golpe del zoom"))
        else:
            g.append((0, "whoosh", 0.32, "transición"))
    if t in ("titular", "miniatura", "engranajes", "iconos"):
        if t == "miniatura" or (t == "titular" and not e.get("fondo")):
            g.append((0, "whoosh_corto", 0.28, "entra el texto"))
        for i, l in enumerate(e.get("lineas") or []):
            g.append((en(l.get("enMs"), 4 + i * 8), "impacto", 0.1, f"línea '{l.get('texto', '')}'"))
    elif t == "chat":
        texto = e.get("texto") or ""
        fin = max(10.0, min(dur * 0.7, len(texto) * 1.4 + 8))
        f = 6
        while f < fin:
            g.append((f, "tecla", 0.12, "tecla del chat"))
            f += 3
        g.append((int(round(fin)) + 6, "pop", 0.45, "se envía el mensaje"))
    elif t == "lista":
        for i, it in enumerate(e.get("items") or []):
            g.append((en(it.get("enMs"), 8 + i * 12) + 5, "ding", 0.13, f"ítem '{it.get('texto', '')}'"))
    elif t == "linea_tiempo":
        for i, it in enumerate(e.get("items") or []):
            g.append((en(it.get("enMs"), 12 + i * 12), "pop", 0.4, f"fecha '{it.get('texto', '')}'"))
    elif t == "tarjetas":
        for i, tj in enumerate(e.get("tarjetas") or []):
            g.append((en(tj.get("enMs"), 6 + i * 14), "whoosh_corto", 0.3, f"tarjeta '{tj.get('texto', '')}'"))
    elif t == "numero":
        fin = 4 + int(round(FPS_DISENO * 1.1))
        for f in range(4, fin, 3):
            g.append((f, "tick", 0.08, "el número cuenta"))
        g.append((fin, "impacto", 0.25, "el número llega"))
    elif t == "nombre":
        g.append((0, "whoosh_corto", 0.3, "cartel de nombre"))
    elif t == "cita" and (e.get("entrada") or "suave") != "luz":
        g.append((2, "brillo", 0.2, "aparece la cita"))
    return [(desde + int(round(f * k)), a, v, f"{t}: {q}") for f, a, v, q in g if f < dur]


def poner_cues(edit, carpeta_public, reporte=None):
    fps = edit["fps"]
    total = edit["durationInFrames"]
    if not edit.get("sfx", True):
        edit["cues"] = []
        return edit
    crudos = []
    for e in edit.get("escenas", []):
        if e.get("tipo") == "zoom" or e.get("sonido") is False:
            continue
        crudos += cues_de_escena(e, fps)
    if edit.get("look") != "cine":  # emojis del look tiktok
        for c in edit.get("captions", []):
            if c.get("emoji"):
                crudos.append((_ms2f(c["startMs"], fps) - int(round(2 * fps / FPS_DISENO)), "pop", 0.45, f"emoji {c['emoji']}"))
    for c in edit.get("capitulos", []):
        crudos.append((_ms2f(c["desdeMs"], fps), "whoosh", 0.5, f"capítulo '{c['texto']}'"))
    inicio = (edit.get("gancho") or {}).get("hastaFrame", 0)
    if edit.get("gancho") and not edit.get("titulo"):
        crudos.append((inicio - int(round(10 * fps / FPS_DISENO)), "whoosh", 0.4, "fin del gancho"))
    if edit.get("titulo"):
        crudos.append((inicio, "whoosh", 0.6, "título"))
    if edit.get("cierre"):
        crudos.append((edit["cierre"]["desdeFrame"], "brillo", 0.3, "tarjeta de cierre"))

    especiales = edit.get("sonidosExtra", [])
    # picos (dónde está el golpe de cada sonido)
    sfx_dir = os.path.join(carpeta_public, "sfx")
    ruta_picos = os.path.join(sfx_dir, "picos.json")
    picos = json.load(open(ruta_picos)) if os.path.exists(ruta_picos) else {}
    reales = {n[:-4] for n in os.listdir(os.path.join(sfx_dir, "real"))} if os.path.isdir(os.path.join(sfx_dir, "real")) else set()
    faltan = [n for n in {c[1] for c in crudos} if (("real/" + n) if n in reales else n) not in picos]
    if faltan:
        try:
            import oido

            picos = oido.picos(sfx_dir)
        except Exception as err:  # sin picos se alinea por el inicio (como antes)
            print(f"AVISO: no pude medir los golpes de los sonidos ({err}).")

    # quién habla en cada cuadro (para bajar los efectos debajo de la voz)
    hablando = bytearray(total + 1)
    for c in edit.get("captions", []):
        for f in range(max(0, _ms2f(c["startMs"], fps)), min(total, _ms2f(c["endMs"], fps)) + 1):
            hablando[f] = 1

    cues = []
    for f, nombre, vol, que in sorted(crudos):
        clave = ("real/" + nombre) if nombre in reales else nombre
        pico = picos.get(clave, 0.0)
        inicio_f = f - int(round(pico * fps))
        recorte = 0
        if inicio_f < 0:
            recorte, inicio_f = -inicio_f, 0
        if f >= total or f < 0:
            continue
        v = vol * (0.75 if hablando[min(f, total)] else 1.0)
        cues.append({"f": inicio_f, "golpe": f, "archivo": f"sfx/{clave}.wav", "recorte": recorte, "vol": round(v, 3),
                     "que": que, "real": nombre in reales})
    for x in especiales:  # sonidos pedidos a mano: se respetan tal cual (golpe alineado si se conoce)
        rel = x["archivo"][len("sfx/"):-4] if x["archivo"].startswith("sfx/") else ""
        pico = picos.get(rel, 0.0)
        ini = x["golpe"] - int(round(pico * fps))
        if 0 <= x["golpe"] < total:
            cues.append({"f": max(0, ini), "golpe": x["golpe"], "archivo": x["archivo"], "recorte": max(0, -ini),
                         "vol": x["vol"], "que": x["que"], "real": "/real/" in x["archivo"], "fijo": True})
    # no amontonar: dos golpes a menos de 0.1 s -> queda el más fuerte (las teclas sí van seguidas)
    limpios = []
    minimo = max(1, int(round(0.1 * fps)))
    for c in sorted(cues, key=lambda c: (c["golpe"], -c["vol"])):
        if limpios and c["golpe"] - limpios[-1]["golpe"] < minimo and not c.get("fijo") and not limpios[-1].get("fijo") \
                and "tecla" not in c["archivo"] and "tick" not in c["archivo"]:
            if c["vol"] > limpios[-1]["vol"]:
                limpios[-1] = c
            continue
        limpios.append(c)
    edit["cues"] = limpios

    if reporte:
        escribir_reporte(limpios, fps, reporte)
    return edit


def escribir_reporte(cues, fps, ruta):
    def t(f):
        return f"{f / fps:5.2f} s"

    importantes = sorted(
        (c for c in cues if "tecla" not in c["archivo"] and "tick" not in c["archivo"]),
        key=lambda c: -c["vol"],
    )[:5]
    importantes.sort(key=lambda c: c["golpe"])
    reales = sum(1 for c in cues if c["real"])
    lineas = [
        "# Sonidos del video (dónde quedó cada uno)",
        "",
        f"{len(cues)} sonidos: {reales} reales (Openverse) y {len(cues) - reales} sintetizados. "
        "Cada uno está alineado para que su golpe caiga en el cuadro exacto.",
        "",
        "## 5 momentos para escuchar con audífonos",
        "",
    ]
    lineas += [f"- **{t(c['golpe'])}** — {c['que']} (`{c['archivo']}`)" for c in importantes]
    lineas += ["", "## Lista completa", "", "| golpe | sonido | volumen | qué pasa |", "|---|---|---|---|"]
    lineas += [f"| {t(c['golpe'])} | {c['archivo']}{' (real)' if c['real'] else ''} | {c['vol']} | {c['que']} |" for c in cues]
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    open(ruta, "w", encoding="utf-8").write("\n".join(lineas) + "\n")


if __name__ == "__main__":
    # uso suelto: python scripts/sonidos.py public/edit.json trabajo/X_sonidos.md
    plan = sys.argv[1]
    d = json.load(open(plan, encoding="utf-8"))
    poner_cues(d, os.path.dirname(os.path.abspath(plan)), sys.argv[2] if len(sys.argv) > 2 else None)
    json.dump(d, open(plan, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"OK: {len(d['cues'])} sonidos colocados")
