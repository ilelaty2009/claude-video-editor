"""EDITAR EL VIDEO BORRANDO TEXTO (como Descript) + guion compacto para leer rápido (como video-use).

    .venv/bin/python scripts/guion.py exportar trabajo/X_transcripcion.json        -> trabajo/X_guion.md
    (abre trabajo/X_guion.md y BORRA las frases o palabras que no quieres en el video)
    .venv/bin/python scripts/guion.py aplicar trabajo/X_transcripcion.json trabajo/X_extras.json

`exportar` escribe una frase por línea con su tiempo: `[012.40-015.10] Hola a todos, hoy vamos a…`
`aplicar` compara el guion editado con la transcripción: todo lo que borraste se vuelve tramos "quitar" en los extras
(los tiempos entre corchetes son solo para ubicarse: no hace falta tocarlos; lo que cuenta es el texto).
No se puede AGREGAR ni cambiar palabras (no hay voz para eso): si escribes algo nuevo, se ignora y se avisa.
"""
import difflib
import json
import os
import re
import sys


def norm(t: str) -> str:
    return re.sub(r"[^\wáéíóúñü]", "", t.lower())


def frases(palabras, pausa: float = 0.6, max_palabras: int = 22):
    """Agrupa palabras en frases: corta en punto, signo de pregunta/exclamación, pausa larga o si ya es muy larga."""
    grupos, actual = [], []
    for i, w in enumerate(palabras):
        actual.append(i)
        sig = palabras[i + 1] if i + 1 < len(palabras) else None
        fin = re.search(r"[.?!…][\"”»)]?$", w["text"].strip()) is not None
        if sig is None or fin or sig["start"] - w["end"] > pausa or len(actual) >= max_palabras:
            grupos.append(actual)
            actual = []
    return grupos


def exportar(ruta_trans: str, destino: str = "") -> str:
    with open(ruta_trans, encoding="utf-8") as f:
        t = json.load(f)
    palabras = t["words"]
    destino = destino or ruta_trans.replace("_transcripcion.json", "_guion.md")
    lineas = [
        "<!-- GUION: borra las frases o palabras que NO quieres en el video y guarda. Luego:",
        f"     .venv/bin/python scripts/guion.py aplicar {os.path.relpath(ruta_trans)} trabajo/TUS_extras.json",
        "     No cambies ni agregues palabras (solo se puede borrar). Los tiempos [inicio-fin] son en segundos. -->",
        "",
    ]
    for g in frases(palabras):
        a, b = palabras[g[0]]["start"], palabras[g[-1]]["end"]
        lineas.append(f"[{a:06.2f}-{b:06.2f}] " + " ".join(palabras[i]["text"].strip() for i in g))
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    return destino


def palabras_del_guion(texto: str):
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    texto = re.sub(r"~~.*?~~", "", texto, flags=re.S)  # ~~tachado~~ también cuenta como borrado
    fuera = []
    for linea in texto.splitlines():
        linea = re.sub(r"^\s*\[[\d.\-\s]+\]\s*", "", linea)
        fuera += [w for w in linea.split() if norm(w)]
    return fuera


def tramos_borrados(palabras, guion_palabras, margen: float = 0.04):
    """Compara palabra por palabra: devuelve (tramos a quitar en segundos, palabras nuevas que se ignoran)."""
    a = [norm(w["text"]) for w in palabras]
    b = [norm(w) for w in guion_palabras]
    borradas, nuevas = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op in ("delete", "replace"):
            borradas += list(range(i1, i2))
        if op in ("insert", "replace"):
            nuevas += guion_palabras[j1:j2]
    tramos = []
    for i in borradas:
        ini, fin = palabras[i]["start"] - margen, palabras[i]["end"] + margen
        if tramos and i - tramos[-1]["ultimo"] == 1:  # palabras seguidas: un solo tramo
            tramos[-1]["hasta"], tramos[-1]["ultimo"] = round(fin, 2), i
            tramos[-1]["texto"] += " " + palabras[i]["text"].strip()
        else:
            tramos.append({"desde": round(max(0, ini), 2), "hasta": round(fin, 2), "ultimo": i, "texto": palabras[i]["text"].strip()})
    return [{"desde": t["desde"], "hasta": t["hasta"], "texto": t["texto"]} for t in tramos], nuevas


def aplicar(ruta_trans: str, ruta_extras: str, ruta_guion: str = "") -> dict:
    with open(ruta_trans, encoding="utf-8") as f:
        palabras = json.load(f)["words"]
    ruta_guion = ruta_guion or ruta_trans.replace("_transcripcion.json", "_guion.md")
    with open(ruta_guion, encoding="utf-8") as f:
        guion = palabras_del_guion(f.read())
    tramos, nuevas = tramos_borrados(palabras, guion)
    extras = {}
    if os.path.exists(ruta_extras):
        with open(ruta_extras, encoding="utf-8") as f:
            extras = json.load(f)
    # se reemplazan los cortes que vinieron del guion la vez pasada; los puestos a mano se respetan
    manuales = [q for q in extras.get("quitar", []) if not q.get("guion")]
    extras["quitar"] = manuales + [{"desde": t["desde"], "hasta": t["hasta"], "guion": True, "texto": t["texto"]} for t in tramos]
    with open(ruta_extras, "w", encoding="utf-8") as f:
        json.dump(extras, f, ensure_ascii=False, indent=1)
    return {"tramos": tramos, "nuevas": nuevas, "segundos": round(sum(t["hasta"] - t["desde"] for t in tramos), 1)}


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "exportar":
        print("OK: guion en", exportar(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
    elif len(sys.argv) >= 4 and sys.argv[1] == "aplicar":
        r = aplicar(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
        print(f"OK: {len(r['tramos'])} tramo(s) borrados del video ({r['segundos']} s).")
        for t in r["tramos"][:12]:
            print(f"   - {t['desde']:.2f}–{t['hasta']:.2f} s: “{t['texto'][:70]}”")
        if r["nuevas"]:
            print("AVISO: estas palabras no están en el video y se ignoran (solo se puede borrar): " + " ".join(r["nuevas"][:15]))
    else:
        print(__doc__)
