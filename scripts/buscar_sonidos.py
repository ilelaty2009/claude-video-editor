"""Busca efectos de sonido REALES (grabados, no sintetizados) en Openverse y escoge el mejor con el oído.

Openverse (openverse.org) es el buscador de medios libres de WordPress: más de 5 millones de audios de Freesound,
Wikimedia Commons y Jamendo. No necesita cuenta ni llave. Límite: ~20 búsquedas por minuto y 200 por día.

Qué hace, para cada tipo de sonido (whoosh, impacto, ding, pop, tecla, tick, riser, brillo, whoosh_corto):
  1. Busca con varias palabras en inglés, SOLO licencia CC0 (dominio público: no hay que dar crédito, se puede usar en
     TikTok/YouTube aunque sea para negocio). Con --licencias cc0,by también acepta CC BY (pide dar crédito).
  2. Descarga los candidatos cortos (trabajo/sonidos_candidatos/<tipo>/).
  3. Los "escucha" con scripts/oido.py y escoge el de mejor puntaje.
  4. Lo deja listo en public/sfx/real/<tipo>.wav (un solo golpe, sin silencio, volumen parejo).
  5. Anota de dónde salió en public/sfx/real/creditos.json y creditos.txt.
Desde ahí, el editor usa ese sonido real en vez del sintetizado (si no hay real, usa el nuestro).

Uso: python scripts/buscar_sonidos.py                      (todos los tipos)
     python scripts/buscar_sonidos.py --tipos whoosh,impacto --candidatos 10
     python scripts/buscar_sonidos.py --tipos whoosh --buscar "paper swipe"   (palabras propias)
     python scripts/buscar_sonidos.py --nombre aplausos --buscar "applause crowd" --como libre
        (sonido especial para un momento del video; queda en public/sfx/real/aplausos.wav y se usa con "sonidos" en los extras)
"""
import argparse
import json
import os
import shutil
import sys
import time
import urllib.parse
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oido  # noqa: E402

API = "https://api.openverse.org/v1/audio/"
AGENTE = "claude-video-editor/1.0 (editor de video personal)"
BUSQUEDAS = {
    "whoosh": ["whoosh transition", "swoosh", "whoosh"],
    "whoosh_corto": ["swish fast", "quick whoosh", "swipe"],
    "impacto": ["cinematic impact", "boom hit", "impact hit"],
    "riser": ["riser", "swell rise", "uplifter"],
    "ding": ["ding notification", "bell ding", "chime ding"],
    "pop": ["pop", "bubble pop", "mouth pop"],
    "tecla": ["keyboard key press", "typing single key", "key click"],
    "tick": ["clock tick", "tick", "ticking single"],
    "brillo": ["sparkle shimmer", "magic chime", "glitter sparkle"],
}
DUR_MAX_MS = {"whoosh": 4000, "whoosh_corto": 3000, "impacto": 6000, "riser": 8000, "ding": 5000, "pop": 3000,
              "tecla": 3000, "tick": 3000, "brillo": 6000}
NO_COMERCIAL = ("nc", "nd")  # nunca: no comercial / sin derivados


def pedir(url, intentos=3):
    """Descarga con paciencia: si el servidor dice "muchas solicitudes" (429), espera y reintenta."""
    for i in range(intentos):
        req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and i < intentos - 1:
                time.sleep(6 * (i + 1))
                continue
            raise


def buscar(q, licencias, fuente, n):
    params = {"q": q, "license": licencias, "length": "shortest", "page_size": str(n), "mature": "false"}
    if fuente:
        params["source"] = fuente
    datos = json.loads(pedir(API + "?" + urllib.parse.urlencode(params)))
    return datos.get("results", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tipos", default=",".join(BUSQUEDAS))
    ap.add_argument("--licencias", default="cc0", help="cc0 (por defecto) o cc0,by")
    ap.add_argument("--candidatos", type=int, default=8, help="cuántos descargar y escuchar por tipo")
    ap.add_argument("--buscar", default="", help="palabras propias (en inglés) en vez de las de siempre")
    ap.add_argument("--fuente", default="", help="limitar a una fuente: freesound, wikimedia_audio, jamendo")
    ap.add_argument("--raiz", default=".", help="carpeta del editor")
    ap.add_argument("--nombre", default="", help="sonido especial con nombre propio (ej. aplausos); requiere --buscar")
    ap.add_argument("--como", default="libre", help="perfil para escucharlo: libre o un tipo (whoosh, impacto, ding...)")
    a = ap.parse_args()

    licencias = ",".join(x for x in a.licencias.lower().split(",") if not any(nc in x for nc in NO_COMERCIAL))
    destino = os.path.join(a.raiz, "public", "sfx", "real")
    os.makedirs(destino, exist_ok=True)
    ruta_cred = os.path.join(destino, "creditos.json")
    creditos = json.load(open(ruta_cred, encoding="utf-8")) if os.path.exists(ruta_cred) else {}
    resumen = []

    if a.nombre:
        if not a.buscar:
            sys.exit("Con --nombre hay que decir qué buscar: --buscar \"applause crowd\"")
        BUSQUEDAS[a.nombre] = [a.buscar]
        DUR_MAX_MS[a.nombre] = 15000
        perfil = a.como if a.como in oido.PERFILES else "libre"
        tipos = [a.nombre]
    else:
        perfil = None
        tipos = [t.strip() for t in a.tipos.split(",") if t.strip()]
    for tipo in tipos:
        if tipo not in BUSQUEDAS:
            print(f"  (tipo desconocido: {tipo})")
            continue
        print(f"== {tipo}")
        carpeta = os.path.join(a.raiz, "trabajo", "sonidos_candidatos", tipo)
        shutil.rmtree(carpeta, ignore_errors=True)
        os.makedirs(carpeta)
        vistos, candidatos = set(), []
        for q in ([a.buscar] if a.buscar else BUSQUEDAS[tipo]):
            try:
                resultados = buscar(q, licencias, a.fuente, 20)
            except Exception as e:  # sin internet, límite de búsquedas, etc.
                print(f"   búsqueda '{q}' falló: {e}")
                resultados = []
            time.sleep(3.2)  # respeta el límite de Openverse (20 por minuto)
            for r in resultados:
                lic = (r.get("license") or "").lower()
                if r["id"] in vistos or any(nc in lic for nc in NO_COMERCIAL):
                    continue
                if r.get("duration") and r["duration"] > DUR_MAX_MS[tipo]:
                    continue
                vistos.add(r["id"])
                candidatos.append(r)
            if len(candidatos) >= a.candidatos * 2:
                break

        puntajes = []
        for r in candidatos:
            if len(puntajes) >= a.candidatos:
                break
            ext = (r.get("filetype") or "mp3").split("/")[-1][:4]
            archivo = os.path.join(carpeta, f"{r['id'][:8]}.{ext}")
            time.sleep(1.0)  # una descarga por segundo: sin saturar a nadie
            try:
                with open(archivo, "wb") as f:
                    f.write(pedir(r["url"]))
                m = oido.medir(oido.mejor_evento(oido.cargar(archivo)))
            except Exception as e:
                print(f"   no se pudo bajar/escuchar '{r.get('title', '')[:40]}': {e}")
                continue
            s = oido.puntaje(m, perfil or tipo)
            puntajes.append((s, archivo, r, m))
            print(f"   {s:5.1f}  {r.get('title', '')[:45]:45}  {oido.describir(m)}")

        if not puntajes:
            print("   ✗ sin candidatos: se queda el sonido sintetizado")
            resumen.append(f"{tipo}: sin candidatos (queda el sintetizado)")
            continue
        s, archivo, r, _ = max(puntajes, key=lambda p: p[0])
        if s < 55:
            print(f"   ✗ el mejor solo saca {s}: no se parece lo suficiente, se queda el sintetizado")
            resumen.append(f"{tipo}: el mejor real sacó {s} (queda el sintetizado)")
            continue
        final = os.path.join(destino, f"{tipo}.wav")
        m = oido.preparar(archivo, final, perfil or tipo)
        creditos[tipo] = {
            "titulo": r.get("title"),
            "autor": r.get("creator"),
            "licencia": f"{r.get('license', '').upper()} {r.get('license_version', '')}".strip(),
            "fuente": r.get("source"),
            "pagina": r.get("foreign_landing_url"),
            "puntaje": s,
            "descripcion": oido.describir(m),
        }
        print(f"   ✓ escogido: '{r.get('title')}' de {r.get('creator')} ({creditos[tipo]['licencia']}) -> {final}")
        resumen.append(f"{tipo}: '{r.get('title')}' ({s:.0f}/100)")

    json.dump(creditos, open(ruta_cred, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(destino, "creditos.txt"), "w", encoding="utf-8") as f:
        f.write("Efectos de sonido reales usados (vía Openverse):\n")
        for tipo, c in sorted(creditos.items()):
            pide = "" if c["licencia"].startswith("CC0") else "  <- PIDE CRÉDITO en la descripción"
            f.write(f"- {tipo}: \"{c['titulo']}\" de {c['autor']} — {c['licencia']} — {c['pagina']}{pide}\n")
    # el editor alinea cada sonido por su golpe: recalcula los picos
    oido.picos(os.path.join(a.raiz, "public", "sfx"))
    print("\nRESUMEN")
    for x in resumen:
        print("  " + x)


if __name__ == "__main__":
    main()
