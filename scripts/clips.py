"""DE UN VIDEO LARGO A VARIOS CLIPS CORTOS (como OpusClip, pero gratis y con criterio de editor).

    .venv/bin/python scripts/clips.py trabajo/X_transcripcion.json [--min 15] [--max 60] [--cuantos 8]

Propone los mejores tramos para TikTok/Reels/Shorts y escribe trabajo/X_clips.md con cada candidato, su puntaje y el
`"recortar"` listo para pegar en los extras. Reglas (las que fallan en las herramientas automáticas, según sus reseñas):
  - Cada clip EMPIEZA al comienzo de una frase y TERMINA al final de una frase (nunca corta una idea a la mitad).
  - Prefiere empezar con un gancho: pregunta, número, "nunca/siempre/secreto/error", "te voy a…".
  - Prefiere tramos con mucha voz y pocas pausas, y con un remate claro al final (frase corta, pregunta o exclamación).
El puntaje es una GUÍA para saber cuál mirar primero, no una predicción de viralidad: Claude lee cada candidato y
decide (que tenga planteamiento Y remate, que se entienda solo, sin contexto). Luego, por cada clip escogido:
    bash scripts/editar.sh videos/X.mov --preset tiktok --extras trabajo/X_clipN_extras.json --salida salida/X_clipN.mp4
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guion  # noqa: E402

GANCHOS = re.compile(
    r"\b(por qué|porque nadie|cómo|sabías|secreto|error|nunca|siempre|nadie|la verdad|te voy a|les voy a|imagina|"
    r"el problema|lo que nadie|truco|increíble|why|how|secret|mistake|never|nobody|truth|imagine|did you know)\b", re.I)


def candidatos(palabras, minimo: float, maximo: float):
    fr = guion.frases(palabras)
    lista = []
    for i in range(len(fr)):
        for j in range(i, len(fr)):
            ini, fin = palabras[fr[i][0]]["start"], palabras[fr[j][-1]]["end"]
            dur = fin - ini
            if dur > maximo:
                break
            if dur < minimo:
                continue
            idx = [k for g in fr[i : j + 1] for k in g]
            texto = " ".join(palabras[k]["text"].strip() for k in idx)
            primera = " ".join(palabras[k]["text"].strip() for k in fr[i])
            ultima = " ".join(palabras[k]["text"].strip() for k in fr[j])
            hablado = sum(palabras[k]["end"] - palabras[k]["start"] for k in idx)
            razones, puntos = [], 0.0
            if "?" in primera or "¿" in primera:
                puntos += 25
                razones.append("empieza con una pregunta")
            if GANCHOS.search(primera):
                puntos += 20
                razones.append("empieza con una frase gancho")
            if re.search(r"\d", primera):
                puntos += 10
                razones.append("empieza con un número")
            if re.search(r"[!?]", ultima) or len(fr[j]) <= 8:
                puntos += 15
                razones.append("termina con un remate corto")
            densidad = hablado / max(dur, 0.1)
            puntos += 20 * min(1.0, densidad / 0.75)  # mucha voz, pocas pausas
            ideal = 28.0  # los clips de ~20–35 s son los que más se ven completos
            puntos += 20 * max(0.0, 1 - abs(dur - ideal) / ideal)
            confianza = sum(palabras[k].get("prob", 1) for k in idx) / len(idx)
            if confianza < 0.6:
                puntos -= 15
                razones.append("ojo: Whisper no entendió bien esta parte")
            lista.append({"desde": round(max(0, ini - 0.1), 2), "hasta": round(fin + 0.2, 2), "segundos": round(dur, 1),
                          "puntaje": round(puntos), "razones": razones, "texto": texto, "primera": primera, "ultima": ultima})
    return lista


def escoger(lista, cuantos: int):
    """Los mejores sin repetirse (dos candidatos que comparten más de la mitad cuentan como el mismo)."""
    elegidos = []
    for c in sorted(lista, key=lambda c: -c["puntaje"]):
        def cruce(e):
            return max(0.0, min(c["hasta"], e["hasta"]) - max(c["desde"], e["desde"]))
        if all(cruce(e) < 0.5 * min(c["segundos"], e["segundos"]) for e in elegidos):
            elegidos.append(c)
        if len(elegidos) == cuantos:
            break
    return sorted(elegidos, key=lambda c: c["desde"])


def principal(argv) -> int:
    ap = argparse.ArgumentParser(description="Propone clips cortos a partir de la transcripción de un video largo.")
    ap.add_argument("transcripcion")
    ap.add_argument("--min", type=float, default=15)
    ap.add_argument("--max", type=float, default=60)
    ap.add_argument("--cuantos", type=int, default=8)
    a = ap.parse_args(argv)
    with open(a.transcripcion, encoding="utf-8") as f:
        t = json.load(f)
    elegidos = escoger(candidatos(t["words"], a.min, a.max), a.cuantos)
    base = a.transcripcion.replace("_transcripcion.json", "")
    lineas = ["# Clips propuestos", "",
              "El puntaje es una guía para saber cuál mirar primero, **no** una predicción de viralidad.",
              "Lee cada uno: que se entienda solo, que tenga planteamiento y remate.", ""]
    for n, c in enumerate(elegidos, 1):
        lineas += [f"## Clip {n} — {c['desde']:.1f}–{c['hasta']:.1f} s ({c['segundos']:.0f} s) · puntaje {c['puntaje']}",
                   "", f"**Empieza:** “{c['primera']}”", f"**Termina:** “{c['ultima']}”",
                   f"**Por qué:** {', '.join(c['razones']) or 'buena duración y mucha voz'}", "",
                   f"> {c['texto']}", "", "Para editarlo, pon esto en sus extras:", "```json",
                   json.dumps({"recortar": {"desde": c["desde"], "hasta": c["hasta"]}}), "```", ""]
    destino = base + "_clips.md"
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    if not elegidos:
        print(f"No encontré tramos de {a.min:.0f}–{a.max:.0f} s que empiecen y terminen en una frase completa (¿el video es muy corto?).")
        return 0
    print(f"OK: {len(elegidos)} clips propuestos -> {destino}")
    for n, c in enumerate(elegidos, 1):
        print(f"  {n}. {c['desde']:.1f}–{c['hasta']:.1f} s ({c['segundos']:.0f} s, puntaje {c['puntaje']}): “{c['primera'][:60]}”")
    return 0


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
