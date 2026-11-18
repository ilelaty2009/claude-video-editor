"""STORYBOARD DE REVISIÓN: una página con un clip corto por cada tramo ("beat") del video, para calificar
cada uno KEEP (se queda), MAYBE (cambiarlo: di cómo) o DROP (quitar ese gráfico), con notas.

Flujo (como en la guía Claude × Remotion, pero gratis y sin internet):
  1. bash scripts/editar.sh videos/X.mov --preset … --extras trabajo/X_extras.json --storyboard
     (renderiza rápido en calidad preview y arma trabajo/storyboard_X/)
  2. python scripts/storyboard.py servir X      -> abre la página en el navegador; Pablo califica y aprieta "Enviar"
     (las respuestas quedan en trabajo/storyboard_X/respuestas.json)
  3. Claude lee respuestas.json, cambia los extras y contesta cada nota:
     python scripts/storyboard.py responder X notas_de_claude.json   ({"beat_03": "Listo: lo puse 0,5 s antes"})
  4. Se repite (ronda 2, 3…) hasta que todo sea KEEP; luego el render final.

También sirve para el BRAND LAB (muestras de estilo para calificar): python scripts/storyboard.py lab NOMBRE muestras.json
"""
import html
import http.server
import json
import os
import socketserver
import subprocess
import sys
import threading
import webbrowser
from typing import Dict, List

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

NOMBRES = {
    "titular": "Titular", "chat": "Chat", "miniatura": "Miniatura", "engranajes": "Engranajes", "tarjetas": "Tarjetas",
    "iconos": "Íconos", "zoom": "Acercamiento", "nombre": "Cartel de nombre", "cita": "Cita", "numero": "Número",
    "lista": "Lista", "linea_tiempo": "Línea de tiempo", "broll": "B-roll", "dividida": "Pantalla dividida",
    "grafica": "Gráfica", "mapa": "Mapa", "cta": "Llamada a la acción", "cinetica": "Frase cinética",
    "diagrama": "Diagrama", "ventana": "Ventana de app", "collage": "Collage", "anotacion": "Anotación", "pantalla": "Grabación de pantalla",
}


def carpeta(nombre: str) -> str:
    return os.path.join(RAIZ, "trabajo", f"storyboard_{nombre}")


def texto_dicho(edit: Dict, a: int, b: int) -> str:
    return " ".join(c["text"].strip() for c in edit.get("captions", []) if a <= c["startMs"] < b)


def resumen_escena(e: Dict) -> str:
    partes = [e.get("arriba", ""), " ".join(l.get("texto", "") for l in e.get("lineas", []) or []), e.get("texto", ""),
              e.get("titulo", ""), " · ".join(i.get("texto", "") for i in e.get("items", []) or [])]
    return " ".join(p for p in partes if p).strip()[:120]


def beats_de(edit: Dict) -> List[Dict]:
    """Los tramos a revisar: título, cada escena (no las automáticas), capítulos, banners, cierre y lo que queda
    en medio (persona hablando) en tramos de ~6 s."""
    fps = edit["fps"]
    total = round(edit["durationInFrames"] / fps * 1000)
    beats = []
    if edit.get("titulo"):
        inicio = round((edit.get("gancho") or {}).get("hastaFrame", 0) / fps * 1000)
        beats.append({"tipo": "titulo", "que": f"Título: “{edit['titulo']}”", "desdeMs": inicio, "hastaMs": inicio + 2500, "ref": {"extra": "titulo"}})
    for e in edit.get("escenas", []):
        if e.get("auto"):
            continue
        beats.append({"tipo": e["tipo"], "que": f"{NOMBRES.get(e['tipo'], e['tipo'])}: {resumen_escena(e)}".rstrip(": "),
                      "desdeMs": e["desdeMs"], "hastaMs": e["hastaMs"], "ref": {"escena": e.get("idExtra")}})
    for i, b in enumerate(edit.get("banners", [])):
        beats.append({"tipo": "banner", "que": f"Banner: “{b['texto']}”", "desdeMs": b["desdeMs"], "hastaMs": min(b["hastaMs"], b["desdeMs"] + 4000), "ref": {"banner": i}})
    for i, c in enumerate(edit.get("capitulos", [])):
        beats.append({"tipo": "capitulo", "que": f"Capítulo: {c['texto']}", "desdeMs": c["desdeMs"], "hastaMs": c["desdeMs"] + 2800, "ref": {"capitulo": i}})
    if edit.get("cierre"):
        d = round(edit["cierre"]["desdeFrame"] / fps * 1000)
        beats.append({"tipo": "cierre", "que": f"Cierre: {edit['cierre'].get('titulo', '')}", "desdeMs": d, "hastaMs": total, "ref": {"extra": "cierre"}})
    # huecos sin nada (persona hablando): tramos de hasta 6 s, para revisar cortes, subtítulos y ritmo
    ocupado = sorted((b["desdeMs"], b["hastaMs"]) for b in beats)
    t = 0
    huecos = []
    for a, b in ocupado + [(total, total)]:
        if a - t > 1500:
            huecos.append((t, a))
        t = max(t, b)
    for a, b in huecos:
        while b - a > 1500:
            fin = min(b, a + 6000)
            beats.append({"tipo": "hablando", "que": "Hablando (cortes, subtítulos, ritmo)", "desdeMs": a, "hastaMs": fin, "ref": {}})
            a = fin
    beats.sort(key=lambda b: b["desdeMs"])
    for n, b in enumerate(beats, 1):
        b["id"] = f"beat_{n:02d}"
        b["dice"] = texto_dicho(edit, b["desdeMs"], b["hastaMs"])
    return beats


def armar(nombre: str, video: str, plan: str) -> str:
    """Corta un clip por beat del video preview y escribe storyboard.json + index.html. Devuelve la carpeta."""
    with open(plan, encoding="utf-8") as f:
        edit = json.load(f)
    dest = carpeta(nombre)
    os.makedirs(os.path.join(dest, "clips"), exist_ok=True)
    previo = {}
    if os.path.exists(os.path.join(dest, "storyboard.json")):
        with open(os.path.join(dest, "storyboard.json"), encoding="utf-8") as f:
            previo = json.load(f)
    beats = beats_de(edit)
    for b in beats:
        clip = os.path.join(dest, "clips", f"{b['id']}.mp4")
        ini = max(0, b["desdeMs"] - 300) / 1000
        dur = (b["hastaMs"] - b["desdeMs"] + 600) / 1000
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ini:.3f}", "-i", video, "-t", f"{dur:.3f}",
                        "-vf", "scale=-2:540", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-c:a", "aac", "-b:a", "96k",
                        "-movflags", "+faststart", clip], check=True)
        b["clip"] = f"clips/{b['id']}.mp4"
    datos = {"nombre": nombre, "ronda": previo.get("ronda", 0) + 1, "tipo": "storyboard", "beats": beats, "respuestasClaude": {}}
    escribir(dest, datos)
    return dest


def escribir(dest: str, datos: Dict) -> None:
    with open(os.path.join(dest, "storyboard.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    with open(os.path.join(dest, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina(datos))


def pagina(datos: Dict) -> str:
    titulo = "Brand Lab" if datos.get("tipo") == "lab" else "Storyboard"
    tarjetas = []
    for b in datos["beats"]:
        resp = datos.get("respuestasClaude", {}).get(b["id"])
        media = (f'<video src="{html.escape(b["clip"])}" controls muted loop playsinline preload="metadata"></video>'
                 if b.get("clip", "").endswith(".mp4") else f'<img src="{html.escape(b.get("clip", ""))}" alt="">')
        tarjetas.append(f"""
<article class="beat" data-id="{b['id']}">
  {media}
  <div class="info">
    <div class="meta">{b['id'].replace('_', ' ').upper()} · {b['desdeMs'] / 1000:.1f}–{b['hastaMs'] / 1000:.1f} s</div>
    <h3>{html.escape(b['que'])}</h3>
    {f'<p class="dice">“{html.escape(b["dice"])}”</p>' if b.get('dice') else ''}
    {f'<p class="claude"><b>Claude:</b> {html.escape(resp)}</p>' if resp else ''}
    <div class="botones">
      <button type="button" data-v="keep">Keep</button><button type="button" data-v="maybe">Maybe</button><button type="button" data-v="drop">Drop</button>
    </div>
    <textarea placeholder="¿Qué cambiarías? (p. ej. “que aparezca cuando digo ‘oxígeno’”)"></textarea>
  </div>
</article>""")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo} · {html.escape(datos['nombre'])}</title>
<style>
:root{{--bg:#f6f4ef;--card:#fff;--tinta:#111;--suave:#6b6b6b;--keep:#16a34a;--maybe:#d97706;--drop:#dc2626}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111214;--card:#1c1d21;--tinta:#f2f2f2;--suave:#9a9a9a}}}}
body{{margin:0;background:var(--bg);color:var(--tinta);font:16px/1.4 -apple-system,Inter,system-ui,sans-serif}}
header{{position:sticky;top:0;background:var(--bg);padding:16px 20px;border-bottom:1px solid #8883;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:2}}
h1{{font-size:20px;margin:0}} .ronda{{color:var(--suave)}} .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;padding:20px}}
.beat{{background:var(--card);border-radius:14px;overflow:hidden;box-shadow:0 2px 10px #0001;border:3px solid transparent}}
.beat video,.beat img{{width:100%;max-height:420px;background:#000;display:block;object-fit:contain}} .info{{padding:12px 14px}}
.meta{{font-size:12px;color:var(--suave);letter-spacing:.06em}} h3{{margin:4px 0 6px;font-size:16px}} .dice{{color:var(--suave);font-size:14px;margin:0 0 8px}}
.claude{{background:#2563eb14;border-left:3px solid #2563eb;padding:6px 8px;font-size:14px}}
.botones{{display:flex;gap:6px;margin:8px 0}} .botones button{{flex:1;padding:8px;border-radius:8px;border:1px solid #8885;background:transparent;color:inherit;font-weight:700;cursor:pointer}}
.beat[data-v=keep]{{border-color:var(--keep)}} .beat[data-v=maybe]{{border-color:var(--maybe)}} .beat[data-v=drop]{{border-color:var(--drop)}}
.beat[data-v=keep] [data-v=keep]{{background:var(--keep);color:#fff}} .beat[data-v=maybe] [data-v=maybe]{{background:var(--maybe);color:#fff}} .beat[data-v=drop] [data-v=drop]{{background:var(--drop);color:#fff}}
textarea{{width:100%;box-sizing:border-box;min-height:56px;border-radius:8px;border:1px solid #8885;background:transparent;color:inherit;padding:8px;font:inherit}}
#enviar{{margin-left:auto;padding:10px 18px;border-radius:10px;border:0;background:#2563eb;color:#fff;font-weight:800;cursor:pointer}} #estado{{color:var(--suave)}}
</style></head><body>
<header><h1>{titulo} · {html.escape(datos['nombre'])}</h1><span class="ronda">Ronda {datos.get('ronda', 1)} · {len(datos['beats'])} tramos</span>
<span id="estado"></span><button id="enviar">Enviar revisión</button></header>
<main class="grid">{''.join(tarjetas)}</main>
<script>
document.querySelectorAll('.beat').forEach(b=>b.querySelectorAll('.botones button').forEach(x=>x.onclick=()=>{{b.dataset.v=x.dataset.v;}}));
document.getElementById('enviar').onclick=async()=>{{
  const r={{ronda:{datos.get('ronda', 1)},beats:{{}}}};
  document.querySelectorAll('.beat').forEach(b=>r.beats[b.dataset.id]={{voto:b.dataset.v||'sin calificar',nota:b.querySelector('textarea').value}});
  const est=document.getElementById('estado');
  try{{const x=await fetch('/respuestas',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(r)}});
    est.textContent=x.ok?'✓ Enviado. Dile a Claude “listo”.':'No se pudo guardar';}}
  catch(e){{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(r,null,1)],{{type:'application/json'}}));
    a.download='respuestas.json';a.click();est.textContent='Guardado como archivo: muévelo a la carpeta del storyboard.';}}
}};
</script></body></html>"""


def servir(nombre: str, puerto: int = 8765, abrir: bool = True) -> None:
    dest = carpeta(nombre)
    if not os.path.exists(os.path.join(dest, "index.html")):
        sys.exit(f"No hay storyboard de '{nombre}'. Primero: bash scripts/editar.sh … --storyboard")

    class Manejador(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=dest, **k)

        def do_POST(self):
            if self.path != "/respuestas":
                self.send_error(404)
                return
            datos = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            with open(os.path.join(dest, "respuestas.json"), "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=1)
            self.send_response(200)
            self.end_headers()
            print(f"Respuestas guardadas: {os.path.relpath(os.path.join(dest, 'respuestas.json'), RAIZ)}", flush=True)

        def log_message(self, *a):
            pass

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", puerto), Manejador) as srv:
        url = f"http://127.0.0.1:{puerto}/"
        print(f"Storyboard en {url}  (Ctrl+C para cerrar)", flush=True)
        if abrir:
            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        srv.serve_forever()


def responder(nombre: str, archivo: str) -> None:
    """Claude contesta cada nota en la página (se ven en la próxima ronda)."""
    dest = carpeta(nombre)
    with open(os.path.join(dest, "storyboard.json"), encoding="utf-8") as f:
        datos = json.load(f)
    with open(archivo, encoding="utf-8") as f:
        datos.setdefault("respuestasClaude", {}).update(json.load(f))
    escribir(dest, datos)
    print(f"OK: {len(datos['respuestasClaude'])} respuestas en la página.")


def lab(nombre: str, muestras: str) -> str:
    """Brand Lab: muestras (videos o imágenes en public/ o trabajo/) para calificar Keep/Maybe/Drop."""
    with open(muestras, encoding="utf-8") as f:
        lista = json.load(f)
    dest = carpeta(nombre)
    os.makedirs(os.path.join(dest, "clips"), exist_ok=True)
    beats = []
    for n, m in enumerate(lista, 1):
        origen = os.path.join(RAIZ, m["archivo"])
        ext = os.path.splitext(origen)[1]
        destino = os.path.join(dest, "clips", f"muestra_{n:02d}{ext}")
        subprocess.run(["cp", origen, destino], check=True)
        beats.append({"id": f"beat_{n:02d}", "tipo": "muestra", "que": m["que"], "desdeMs": 0, "hastaMs": 0,
                      "clip": f"clips/muestra_{n:02d}{ext}", "dice": m.get("detalle", ""), "ref": m.get("ref", {})})
    escribir(dest, {"nombre": nombre, "ronda": 1, "tipo": "lab", "beats": beats, "respuestasClaude": {}})
    return dest


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    orden, nombre = sys.argv[1], sys.argv[2]
    if orden == "servir":
        servir(nombre, abrir="--sin-abrir" not in sys.argv)
    elif orden == "responder":
        responder(nombre, sys.argv[3])
    elif orden == "armar":
        print(armar(nombre, sys.argv[3], sys.argv[4]))
    elif orden == "lab":
        print(lab(nombre, sys.argv[3]))
    else:
        print(__doc__)
