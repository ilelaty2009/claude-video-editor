"""Busca en la transcripción lo que un editor profesional quitaría a mano.

Encuentra:
  1. Falsos comienzos / repeticiones: la persona empieza una frase, se equivoca y la vuelve a decir.
     (se queda la ÚLTIMA versión, que suele ser la buena)
  2. Palabras repetidas seguidas ("the the", "que que").
  3. Muletillas (eh, em, este, um, uh, mmm...).
  4. Pausas largas.
  5. Palabras que Whisper no entendió bien (baja confianza): revisa nombres propios.

No borra nada: escribe un reporte (trabajo/X_revision.md) con tramos sugeridos para "quitar" en los extras.
Claude lee el reporte, decide y copia los tramos que tengan sentido.

Uso: python scripts/detectar_repeticiones.py trabajo/X_transcripcion.json [--salida trabajo/X_revision.md]
"""
import argparse
import json
import re

MULETILLAS = {"eh", "ehh", "em", "emm", "um", "umm", "uh", "uhh", "mmm", "mm", "hmm", "este", "pues", "osea", "ah", "ahh"}


def norm(t):
    return re.sub(r"[^\wáéíóúñü]", "", t.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("--salida", default="")
    ap.add_argument("--ventana", type=float, default=6.0, help="segundos máximos entre el intento fallido y el bueno")
    ap.add_argument("--n", type=int, default=3, help="palabras iguales seguidas para contar como repetición")
    args = ap.parse_args()

    data = json.load(open(args.transcript, encoding="utf-8"))
    w = data["words"]
    toks = [norm(x["text"]) for x in w]
    quitar = []
    lineas = []

    # 1) falsos comienzos: un trozo de n+ palabras que se repite poco después
    usados = set()
    for i in range(len(w) - args.n):
        if i in usados:
            continue
        clave = toks[i : i + args.n]
        if not all(clave):
            continue
        for j in range(i + 1, len(w) - args.n + 1):
            if w[j]["start"] - w[i]["start"] > args.ventana:
                break
            # un falso comienzo no termina una frase antes de repetirla (si hay punto en medio, es otra frase)
            if toks[j : j + args.n] == clave and not any(re.search(r"[.?!]$", x["text"].strip()) for x in w[i : j - 1]):
                # alarga la coincidencia
                m = args.n
                while j + m < len(w) and i + m < j and toks[i + m] == toks[j + m]:
                    m += 1
                ini, fin = w[i]["start"], w[j]["start"] - 0.05
                texto = " ".join(x["text"] for x in w[i:j])
                quitar.append({"desde": round(ini, 2), "hasta": round(fin, 2), "motivo": "falso comienzo / repetición"})
                lineas.append(f"- **{ini:.1f}–{fin:.1f} s** falso comienzo: \"{texto.strip()}\" → luego lo repite en {w[j]['start']:.1f} s")
                usados.update(range(i, j))
                break

    # 2) palabra repetida seguida
    for i in range(1, len(w)):
        if toks[i] and toks[i] == toks[i - 1] and w[i]["start"] - w[i - 1]["end"] < 0.6 and len(toks[i]) > 1:
            quitar.append({"desde": round(w[i - 1]["start"], 2), "hasta": round(w[i]["start"] - 0.03, 2), "motivo": "palabra repetida"})
            lineas.append(f"- **{w[i-1]['start']:.1f} s** palabra repetida: \"{w[i-1]['text'].strip()} {w[i]['text'].strip()}\"")

    # 3) muletillas
    mul = [x for x, t in zip(w, toks) if t in MULETILLAS]
    for x in mul:
        lineas.append(f"- **{x['start']:.1f} s** muletilla: \"{x['text'].strip()}\" (se quita con --quitar \"{norm(x['text'])}\")")

    # 4) pausas largas (las de >0.3 s ya se cortan solas; aquí solo las muy largas, por si hay algo raro)
    for i in range(1, len(w)):
        p = w[i]["start"] - w[i - 1]["end"]
        if p > 2.5:
            lineas.append(f"- **{w[i-1]['end']:.1f}–{w[i]['start']:.1f} s** pausa de {p:.1f} s (se corta sola; revisa si alguien habló sin micrófono)")

    # 5) baja confianza
    dudosas = [x for x in w if x.get("prob", 1) < 0.35 and len(norm(x["text"])) > 3]
    for x in dudosas[:15]:
        lineas.append(f"- **{x['start']:.1f} s** Whisper no está seguro de \"{x['text'].strip()}\" ({x.get('prob', 0):.0%}): ¿nombre propio? → usa `correcciones`")

    reporte = ["# Revisión automática de la transcripción", "", f"Duración: {data.get('duration', 0):.1f} s, {len(w)} palabras.", ""]
    reporte += lineas or ["- No encontré repeticiones, muletillas ni palabras dudosas."]
    reporte += ["", "## Tramos sugeridos para `\"quitar\"` en los extras (revisa antes de copiarlos)", "", "```json", json.dumps(quitar, ensure_ascii=False, indent=1), "```"]
    texto = "\n".join(reporte)
    if args.salida:
        open(args.salida, "w", encoding="utf-8").write(texto)
    print(texto)


if __name__ == "__main__":
    main()
