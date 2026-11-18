"""Baja una fuente de Google Fonts (gratis, licencia libre: OFL o Apache) y la deja lista para el editor.

    .venv/bin/python scripts/fuente_google.py "Space Grotesk"
    .venv/bin/python scripts/fuente_google.py "Bebas Neue" --pesos 400

Guarda public/fuentes/<nombre>-latin-<peso>-normal.woff2, la mide (para que los subtítulos sepan su ancho real)
y la deja disponible: luego ponla en brand/marca.json ("fuentes": {"escenas": "Space Grotesk"}).
Regla anti "AI slop": no baja versiones itálicas (las serif itálicas son lo que más delata un video hecho con IA).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(RAIZ, "public", "fuentes")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def pedir(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def bajar(familia: str, pesos=(700, 900)) -> list:
    slug = re.sub(r"[^a-z0-9]", "", familia.lower())
    guardados = []
    for peso in pesos:
        url = "https://fonts.googleapis.com/css2?" + urllib.parse.urlencode({"family": f"{familia}:wght@{peso}"})
        try:
            css = pedir(url).decode()
        except Exception:
            continue  # ese peso no existe en esa fuente
        # bloque /* latin */ (letras del español incluidas)
        bloques = re.findall(r"/\* latin \*/\s*@font-face\s*{([^}]*)}", css)
        m = re.search(r"url\((https://[^)]+\.woff2)\)", bloques[0] if bloques else css)
        if not m:
            continue
        destino = os.path.join(CARPETA, f"{slug}-latin-{peso}-normal.woff2")
        with open(destino, "wb") as f:
            f.write(pedir(m.group(1)))
        guardados.append(destino)
    if not guardados:
        raise SystemExit(f"No encontré '{familia}' en Google Fonts (revisa el nombre exacto en fonts.google.com).")
    ruta_nombres = os.path.join(CARPETA, "nombres.json")
    nombres = json.load(open(ruta_nombres, encoding="utf-8")) if os.path.exists(ruta_nombres) else {}
    nombres[slug] = familia
    with open(ruta_nombres, "w", encoding="utf-8") as f:
        json.dump(nombres, f, ensure_ascii=False, indent=1)
    # medir (ancho real de cada letra) y actualizar la lista de fuentes
    subprocess.run(["node", os.path.join(RAIZ, "scripts", "medir_fuentes.mjs")], check=True, cwd=RAIZ)
    return guardados


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("familia")
    ap.add_argument("--pesos", default="400,700,900", help="pesos separados por coma (los que no existan se saltan)")
    a = ap.parse_args()
    if "italic" in a.familia.lower():
        sys.exit("No: las fuentes itálicas (sobre todo serif) son lo que más delata un video hecho con IA.")
    hechos = bajar(a.familia, [int(p) for p in a.pesos.split(",")])
    print(f"OK: {a.familia} ({len(hechos)} pesos) en public/fuentes. Úsala en brand/marca.json.")
