"""Plan de edición: 60 fps, duración correcta, cortes sin solaparse, subtítulos dentro del video, seguimiento de cara."""
from ayuda import RAIZ, carpeta_temporal  # (primero: deja importar los scripts)
import json
import os
import subprocess
import sys
import unittest

import sonidos

PY = sys.executable


def transcripcion(ruta):
    # dos frases separadas por una pausa larga (1.5 s) que se debe cortar
    palabras = []
    t = 0.5
    for w in "Hola a todos hoy vamos a hablar de historia.".split():
        palabras.append({"text": w, "start": round(t, 3), "end": round(t + 0.3, 3), "prob": 0.95})
        t += 0.35
    t += 1.5
    for w in "La Revolución Francesa empezó en 1789 y cambió Europa.".split():
        palabras.append({"text": w, "start": round(t, 3), "end": round(t + 0.3, 3), "prob": 0.95})
        t += 0.35
    with open(ruta, "w") as f:
        json.dump({"language": "es", "duration": t + 0.5, "words": palabras}, f)
    return t + 0.5


def caras(ruta):
    muestras = [{"t": float(s), "caras": [{"x": 0.4 + 0.02 * s, "y": 0.45, "alto": 0.3}]} for s in range(9)]
    with open(ruta, "w") as f:
        json.dump({"foco": {"x": 0.48, "y": 0.4}, "recorte_x": 0.48, "muestras": muestras}, f)


class PruebaPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = carpeta_temporal()
        cls.trans = os.path.join(cls.dir, "x_transcripcion.json")
        cls.total = transcripcion(cls.trans)
        cls.caras = os.path.join(cls.dir, "x_caras.json")
        caras(cls.caras)

    def plan(self, *extra, extras=None):
        out = os.path.join(self.dir, "public", "edit.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        cmd = [PY, os.path.join(RAIZ, "scripts", "plan_edit.py"), self.trans, out, "--caras", self.caras] + list(extra)
        if extras is not None:
            ruta = os.path.join(self.dir, "extras.json")
            with open(ruta, "w") as f:
                json.dump(extras, f)
            cmd += ["--extras", ruta]
        subprocess.run(cmd, check=True, capture_output=True)
        with open(out) as f:
            return json.load(f)

    def test_60_fps_por_defecto(self):
        self.assertEqual(self.plan()["fps"], 60)

    def test_cortes_y_duracion(self):
        d = self.plan("--formato", "tv", "--ancho", "1920", "--alto", "1080", "--encuadre", "completo")
        segs = d["segments"]
        self.assertGreaterEqual(len(segs), 2)  # la pausa larga se cortó
        fin = 0
        for s in segs:
            self.assertEqual(s["from"], fin)  # pegados uno tras otro, sin huecos ni solapes
            self.assertGreater(s["durationInFrames"], 0)
            fin += s["durationInFrames"]
        self.assertEqual(d["durationInFrames"], fin)
        self.assertLess(fin / 60, self.total)  # el video editado es más corto que el original
        for c in d["captions"]:
            self.assertGreaterEqual(c["startMs"], 0)
            self.assertLessEqual(c["endMs"], fin / 60 * 1000 + 1)
        ms = [c["startMs"] for c in d["captions"]]
        self.assertEqual(ms, sorted(ms))

    def test_cierre_suma_su_duracion(self):
        sin = self.plan()["durationInFrames"]
        con = self.plan(extras={"cierre": {"titulo": "Gracias", "segundos": 3}})
        self.assertEqual(con["durationInFrames"], sin + 180)  # 3 s a 60 fps

    def test_formato_y_zona_segura(self):
        d = self.plan("--formato", "reel", "--ancho", "1080", "--alto", "1920", "--encuadre", "recorte")
        self.assertEqual((d["width"], d["height"], d["formato"]), (1080, 1920, "reel"))
        self.assertGreater(d["zonaSegura"]["abajo"], 0.15)  # descripción y botones de TikTok

    def test_estilo_de_subtitulos(self):
        self.assertEqual(self.plan("--estilo", "clase")["subtitulos"], "cine")
        self.assertEqual(self.plan("--estilo", "tiktok")["subtitulos"], "tiktok")
        self.assertEqual(self.plan("--estilo", "clase", "--subtitulos", "caja")["subtitulos"], "caja")

    def test_seguimiento_de_cara(self):
        d = self.plan("--encuadre", "completo", "--ancho", "1920", "--alto", "1080")
        ruta = d["focoRuta"]
        self.assertGreater(len(ruta), 4)
        fs = [p["f"] for p in ruta]
        self.assertEqual(fs, sorted(fs))
        self.assertLess(fs[-1], d["durationInFrames"])
        self.assertGreater(ruta[-1]["x"], ruta[0]["x"])  # la cara se movió a la derecha y la ruta la siguió


class PruebaSonidos(unittest.TestCase):
    def test_efectos_caen_en_el_mismo_segundo_a_30_y_60_fps(self):
        escena = {"tipo": "lista", "desdeMs": 2000, "hastaMs": 6000, "items": [{"texto": "A"}, {"texto": "B", "enMs": 3500}]}
        c30 = sonidos.cues_de_escena(escena, 30)
        c60 = sonidos.cues_de_escena(escena, 60)
        self.assertEqual(len(c30), len(c60))
        for a, b in zip(c30, c60):
            self.assertAlmostEqual(a[0] / 30, b[0] / 60, delta=1 / 30)


if __name__ == "__main__":
    unittest.main()
