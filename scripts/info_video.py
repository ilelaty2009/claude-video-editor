"""Datos básicos de un video (atajo de scripts/medios.py, que es donde está la lógica).

Uso: python scripts/info_video.py video.mov            -> ancho alto duracion fps
     python scripts/info_video.py video.mov --encuadre -> 'relleno' si es horizontal, 'recorte' si es vertical
"""
import sys

from medios import info

if __name__ == "__main__":
    d = info(sys.argv[1])
    if "--encuadre" in sys.argv:
        print("relleno" if d["ancho"] > d["alto"] * 1.05 else "recorte")
    else:
        print(d["ancho"], d["alto"], round(d["duracion"], 2), d["fps"])
