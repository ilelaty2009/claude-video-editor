"""HOJA DE MARCA: tus colores y fuentes, para que todos los videos se vean como el mismo canal.

    .venv/bin/python scripts/marca.py desde-web https://tu-pagina.com   -> saca colores y fuentes de tu web
    .venv/bin/python scripts/marca.py mostrar                           -> muestra la marca actual

Escribe brand/marca.json (lo usa todo el editor) y actualiza brand/BRAND.md. Antes de usarla en un video, Claude
muestra cuadros de ejemplo (o arma un Brand Lab) y espera tu sí.
"""
import colorsys
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
RUTA = os.path.join(RAIZ, "brand", "marca.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
GENERICAS = {"sans-serif", "serif", "monospace", "system-ui", "inherit", "initial", "cursive", "-apple-system",
             "blinkmacsystemfont", "segoe ui", "helvetica", "arial", "helvetica neue", "ui-sans-serif", "var"}


def pedir(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "ignore")


def a_rgb(c: str):
    c = c.strip().lower()
    if c.startswith("#"):
        h = c[1:]
        if len(h) == 3:
            h = "".join(x * 2 for x in h)
        if len(h) >= 6:
            return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"rgba?\((\d+)[ ,]+(\d+)[ ,]+(\d+)", c)
    return tuple(int(x) for x in m.groups()) if m else None


def hexa(rgb) -> str:
    return "#%02X%02X%02X" % tuple(int(max(0, min(255, v))) for v in rgb)


def colores_de(textos) -> list:
    """Colores con personalidad (ni grises, ni casi blancos, ni casi negros), del más usado al menos usado."""
    conteo = Counter()
    for t in textos:
        for c in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgba?\([^)]*\)", t):
            rgb = a_rgb(c)
            if not rgb:
                continue
            h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in rgb))
            if s < 0.35 or l < 0.15 or l > 0.9:
                continue
            conteo[hexa(rgb)] += 1
    elegidos = []
    for c, _ in conteo.most_common(40):
        h = colorsys.rgb_to_hls(*(v / 255 for v in a_rgb(c)))[0]
        if all(min(abs(h - colorsys.rgb_to_hls(*(v / 255 for v in a_rgb(e)))[0]), 1 - abs(h - colorsys.rgb_to_hls(*(v / 255 for v in a_rgb(e)))[0])) > 0.06 for e in elegidos):
            elegidos.append(c)
        if len(elegidos) == 4:
            break
    return elegidos


def fuentes_de(html: str, css: list) -> list:
    familias = []
    for m in re.findall(r"fonts\.googleapis\.com/css2?\?([^\"'\s>]+)", html):
        for fam in urllib.parse.parse_qs(urllib.parse.unquote(m)).get("family", []):
            familias.append(fam.split(":")[0].replace("+", " "))
    for t in css + [html]:
        for decl in re.findall(r"font-family\s*:\s*([^;}\"]+)", t):
            for f in decl.split(","):
                f = f.strip().strip("'\"")
                if f and f.lower() not in GENERICAS and not f.startswith("var(") and not f.startswith("--"):
                    familias.append(f)
    vistos = []
    for f in familias:
        if f not in vistos and "italic" not in f.lower():
            vistos.append(f)
    return vistos[:3]


def oscuro(c: str, l_obj: float) -> str:
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in a_rgb(c)))
    return hexa(tuple(v * 255 for v in colorsys.hls_to_rgb(h, l_obj, min(s, 0.6))))


def desde_web(url: str) -> dict:
    html = pedir(url)
    css = re.findall(r"<style[^>]*>(.*?)</style>", html, re.S)
    for href in re.findall(r"<link[^>]+rel=[\"']?stylesheet[\"']?[^>]*href=[\"']([^\"']+)", html)[:6]:
        try:
            css.append(pedir(urllib.parse.urljoin(url, href)))
        except Exception:
            pass
    colores = colores_de(css + [html])
    familias = fuentes_de(html, css)
    with open(RUTA, encoding="utf-8") as f:
        marca = json.load(f)
    if colores:
        marca["colores"]["amarillo"] = colores[0]  # el color principal: palabras clave y destacados
        if len(colores) > 1:
            marca["colores"]["azul"] = colores[1]
        if len(colores) > 2:
            marca["colores"]["rojo"] = colores[2]
        marca["colores"]["fondo"] = [oscuro(colores[0], 0.2), oscuro(colores[0], 0.1), oscuro(colores[0], 0.04)]
    import fuente_google

    for fam in familias:
        try:
            fuente_google.bajar(fam)
            marca["fuentes"]["escenas"] = fam
            break
        except SystemExit:
            continue  # no está en Google Fonts: se queda la anterior
    marca["origen"] = url
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(marca, f, ensure_ascii=False, indent=1)
    return {"colores": colores, "fuentes": familias, "marca": marca}


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "desde-web":
        r = desde_web(sys.argv[2])
        print("Colores encontrados:", ", ".join(r["colores"]) or "(ninguno con personalidad)")
        print("Fuentes encontradas:", ", ".join(r["fuentes"]) or "(ninguna)")
        print("Marca guardada en brand/marca.json. Revísala con un Brand Lab antes de usarla.")
    else:
        with open(RUTA, encoding="utf-8") as f:
            print(json.dumps(json.load(f), ensure_ascii=False, indent=1))
