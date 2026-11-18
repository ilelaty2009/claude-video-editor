"""BRAND LAB: muestras cortas de estilo con TU marca, para calificarlas Keep / Maybe / Drop.

    .venv/bin/python scripts/brand_lab.py                 (vertical, con el video de demostración)
    .venv/bin/python scripts/brand_lab.py --formato tv
    .venv/bin/python scripts/storyboard.py servir lab      (abre la página para calificar)

Hace ~20 clips de 3 s: estilos de subtítulos, transiciones, banners, pantalla dividida, títulos detrás no (eso
necesita una persona), frase cinética, lista, diagrama, número, gráfica y ventana. Los colores y fuentes salen de
brand/marca.json. Lo que califiques KEEP, Claude lo anota en brand/BRAND.md como estilo preferido; los MAYBE los
rehace con tus notas (ronda 2); los DROP no se vuelven a usar.
"""
import argparse
import copy
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import editor  # noqa: E402
import storyboard  # noqa: E402
from editor import ruta  # noqa: E402


def muestras(base: dict) -> list:
    """(qué es, cambios al plan, desde_ms, hasta_ms)."""
    total = round(base["durationInFrames"] / base["fps"] * 1000)
    hablando = (500, 3500)
    t0, t1 = 5000, 8000
    titular = {"tipo": "titular", "fondo": True, "desdeMs": t0, "hastaMs": t1, "arriba": "Con eso fabrican",
               "lineas": [{"texto": "SU PROPIO"}, {"texto": "ALIMENTO", "color": "#FFC94D", "enMs": t0 + 900}]}
    lista = []
    for sub in ("cine", "caja", "tiktok", "resaltado", "etiqueta"):
        lista.append((f"Subtítulos «{sub}»", {"subtitulos": sub, "escenas": [], "banners": []}, *hablando))
    for entrada in ("suave", "barrido", "zoom", "luz", "glitch"):
        lista.append((f"Transición «{entrada}» (titular a pantalla completa)", {"escenas": [{**titular, "entrada": entrada}], "banners": []}, t0 - 300, t1))
    for estilo in ("pastilla", "texto", "vidrio"):
        lista.append((f"Banner «{estilo}»", {"escenas": [], "banners": [{"texto": "La fotosíntesis en 1 minuto", "estilo": estilo, "desdeMs": 0, "hastaMs": 3500}]}, 0, 3500))
    for modo in ("apilada", "lado", "pip"):
        lista.append((f"Pantalla dividida «{modo}»", {"escenas": [{"tipo": "dividida", "modo": modo, "desdeMs": t0, "hastaMs": t1, "arriba": "Las plantas toman",
                                                                   "lineas": [{"texto": "LUZ"}, {"texto": "AGUA", "color": "#5CC8FF"}]}]}, t0 - 300, t1))
    lista += [
        ("Frase cinética", {"escenas": [{"tipo": "cinetica", "desdeMs": t0, "hastaMs": t1, "destacar": ["alimento,"],
                                         "palabras": [{"texto": w, "enMs": t0 + 250 * i} for i, w in enumerate("Con eso fabrican su propio alimento,".split())]}]}, t0, t1),
        ("Lista con chulitos", {"escenas": [{"tipo": "lista", "desdeMs": t0, "hastaMs": t1, "titulo": "Las plantas toman", "entrada": "barrido",
                                             "items": [{"texto": "☀️ Luz", "enMs": t0 + 600}, {"texto": "💧 Agua", "enMs": t0 + 1200}, {"texto": "🫧 CO2", "enMs": t0 + 1800}]}]}, t0, t1),
        ("Diagrama", {"escenas": [{"tipo": "diagrama", "desdeMs": t0, "hastaMs": t1, "titulo": "Fotosíntesis",
                                   "nodos": [{"icono": "☀️", "texto": "Luz", "enMs": t0 + 300}, {"icono": "🌿", "texto": "Hoja", "enMs": t0 + 900}, {"icono": "💨", "texto": "Oxígeno", "enMs": t0 + 1500}]}]}, t0, t1),
        ("Número que cuenta", {"escenas": [{"tipo": "numero", "desdeMs": t0, "hastaMs": t1, "valor": 1789, "etiqueta": "Año de ejemplo", "entrada": "zoom"}]}, t0, t1),
        ("Gráfica", {"escenas": [{"tipo": "grafica", "desdeMs": t0, "hastaMs": t1, "titulo": "Ejemplo", "valores": [3, 5, 4, 8, 12], "etiquetas": ["L", "M", "X", "J", "V"]}]}, t0, t1),
        ("Ventana con checklist", {"escenas": [{"tipo": "ventana", "desdeMs": t0, "hastaMs": t1, "texto": "Edita mi video para el colegio",
                                                "items": [{"texto": "Silencios cortados"}, {"texto": "Subtítulos listos"}], "valor": 2930}]}, t0, t1),
    ]
    return [(q, c, max(0, a), min(total, b)) for q, c, a, b in lista]


def principal(argv) -> int:
    ap = argparse.ArgumentParser(description="Muestras de estilo para calificar (Brand Lab).")
    ap.add_argument("--formato", default="reel")
    ap.add_argument("--video", default="demo/fotosintesis_demo.mov", help="video base (sin personas por defecto)")
    a = ap.parse_args(argv)
    print("1/3 Preparando el video base...")
    editor.correr(["bash", "scripts/editar.sh", a.video, "--formato", a.formato, "--estilo", "clase", "--solo-preparar"],
                  "No pude preparar el video base del Brand Lab.")
    with open(ruta("public", "edit.json"), encoding="utf-8") as f:
        base = json.load(f)
    base["sfx"] = False
    base.pop("musica", None)
    lab = storyboard.carpeta("lab")
    os.makedirs(os.path.join(lab, "fuente"), exist_ok=True)
    bundle = os.path.join(lab, "bundle")
    print("2/3 Preparando Remotion...")
    editor.correr(["npx", "remotion", "bundle", "src/index.ts", "--out-dir", bundle, "--log", "error"], "Remotion no pudo preparar el proyecto.")
    lista = muestras(base)
    salida = []
    print(f"3/3 Haciendo {len(lista)} muestras...")
    q = editor.cargar_config()["calidades"]["preview"]
    pasos = editor.Pasos(1)
    for n, (que, cambios, desde, hasta) in enumerate(lista, 1):
        plan = copy.deepcopy(base)
        plan.update(copy.deepcopy(cambios))
        props = os.path.join(lab, "fuente", f"props_{n:02d}.json")
        texto = json.dumps({"data": plan}, ensure_ascii=False)
        archivo = os.path.join(lab, "fuente", f"muestra_{n:02d}.mp4")
        fps = plan["fps"]
        ini, fin = round(desde / 1000 * fps), round(hasta / 1000 * fps) - 1
        # si se interrumpió, no repite las muestras que ya están completas y no cambiaron
        hecha = os.path.exists(archivo) and os.path.exists(props) and open(props, encoding="utf-8").read() == texto \
            and editor.medios.contar_cuadros(archivo) == fin - ini + 1
        if not hecha:
            with open(props, "w", encoding="utf-8") as f:
                f.write(texto)
            editor.render_parte(bundle, archivo, ini, fin, q, n - 1, len(lista), pasos, extra=[f"--props={props}"])
        salida.append({"archivo": os.path.relpath(archivo, ruta()), "que": que, "ref": cambios})
        print(f"    {n:2d}/{len(lista)} {que}" + (" (ya estaba)" if hecha else ""), flush=True)
    with open(os.path.join(lab, "fuente", "muestras.json"), "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    storyboard.lab("lab", os.path.join(lab, "fuente", "muestras.json"))
    subprocess.run(["rm", "-rf", bundle])
    print("LISTO. Abre la página para calificar: .venv/bin/python scripts/storyboard.py servir lab")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(principal(sys.argv[1:]))
    except editor.ErrorEditor as e:
        print(f"PROBLEMA: {e.que}\n{e.como_arreglar}\n{e.detalle}", file=sys.stderr)
        sys.exit(2)
