"""Lo nuevo del reel de referencia: geometría de la cámara por formato, banners fijos, censura con pitido."""
from ayuda import RAIZ, carpeta_temporal  # noqa: F401  (primero: deja importar los scripts)
import json
import os
import subprocess
import sys
import unittest

import numpy as np

import mezcla
import plan_edit


class PruebaGeometria(unittest.TestCase):
    def test_completo_con_barras(self):
        g = plan_edit.geometria_video(1920, 1080, 9 / 16, "completo", "tv")
        self.assertAlmostEqual(g["area"]["w"], (9 / 16) / (16 / 9), places=3)
        x, y = g["punto"](0.5, 0.5)
        self.assertAlmostEqual(x, 0.5, places=3)

    def test_relleno_vertical_es_la_franja_de_camara(self):
        g = plan_edit.geometria_video(1080, 1920, 1620 / 1080, "relleno", "reel", rx=0.5)
        self.assertAlmostEqual(g["area"]["h"], 880 / 1920, places=3)
        self.assertAlmostEqual(g["area"]["y"], (1920 * 0.41 - 440) / 1920, places=3)
        x, y = g["punto"](0.5, 0.5)  # el centro del video queda al centro de la franja
        self.assertAlmostEqual(x, 0.5, places=3)
        self.assertAlmostEqual(y, g["area"]["y"] + g["area"]["h"] / 2, places=3)

    def test_recorte_centrado_en_la_cara(self):
        g = plan_edit.geometria_video(1080, 1920, 16 / 9, "recorte", "reel", rx=0.3)
        x, _ = g["punto"](0.3, 0.5)  # la cara en x=0.3 del original queda dentro del cuadro
        self.assertTrue(0 <= x <= 1)


class PruebaCensura(unittest.TestCase):
    def test_tapa_la_palabra_y_marca_el_pitido(self):
        caps = [{"text": " qué", "startMs": 0, "endMs": 200}, {"text": " mierda,", "startMs": 300, "endMs": 600}]
        pitidos = plan_edit.censurar(caps, {"mierda"})
        self.assertEqual(caps[1]["text"].strip(), "m*****,")
        self.assertEqual(caps[0]["text"], " qué")
        self.assertEqual(len(pitidos), 1)
        self.assertLess(pitidos[0]["desdeMs"], 300)

    def test_el_pitido_reemplaza_la_voz(self):
        sr = mezcla.SR
        t = np.arange(sr) / sr
        voz = np.stack([np.sin(2 * np.pi * 220 * t)] * 2, axis=1).astype(np.float32) * 0.5
        mezcla.tapar_con_pitido(voz, [{"desdeMs": 300, "hastaMs": 700}])
        tramo = voz[int(0.35 * sr) : int(0.65 * sr), 0]
        espectro = np.abs(np.fft.rfft(tramo))
        frec = np.fft.rfftfreq(len(tramo), 1 / sr)
        self.assertAlmostEqual(frec[np.argmax(espectro)], 1000, delta=10)  # se oye el pitido, no la voz (220 Hz)
        self.assertAlmostEqual(float(np.abs(voz[: int(0.25 * sr), 0]).max()), 0.5, delta=0.01)  # antes, la voz intacta


class PruebaGanchoYCapitulos(unittest.TestCase):
    def test_avisa_si_no_hay_gancho(self):
        base = {"fps": 60, "captions": [], "escenas": []}
        self.assertIn("AVISO", plan_edit.revisar_gancho(base))
        self.assertNotIn("AVISO", plan_edit.revisar_gancho({**base, "titulo": "Hola"}))
        self.assertNotIn("AVISO", plan_edit.revisar_gancho({**base, "banners": [{"desdeMs": 0}]}))
        # una escena automática (zoom del ritmo) no cuenta como gancho
        self.assertIn("AVISO", plan_edit.revisar_gancho({**base, "escenas": [{"desdeMs": 500, "auto": True}]}))

    def test_capitulos_para_youtube(self):
        import control_calidad

        d = carpeta_temporal()
        edit = {"fps": 60, "durationInFrames": 60 * 90,
                "capitulos": [{"desdeMs": 12000, "texto": "Qué es"}, {"desdeMs": 40000, "texto": "Ejemplos"}]}
        ruta = os.path.join(d, "c.txt")
        self.assertTrue(control_calidad.escribir_capitulos(edit, ruta))
        lineas = open(ruta, encoding="utf-8").read().splitlines()
        self.assertEqual(lineas[:3], ["0:00 Intro", "0:12 Qué es", "0:40 Ejemplos"])  # YouTube exige empezar en 0:00
        self.assertFalse(control_calidad.escribir_capitulos({"fps": 60, "durationInFrames": 60}, ruta))


class PruebaPlanNuevo(unittest.TestCase):
    def test_banners_y_censura_en_el_plan(self):
        d = carpeta_temporal()
        palabras = [{"text": w, "start": 0.5 + i * 0.4, "end": 0.8 + i * 0.4, "prob": 0.9}
                    for i, w in enumerate("esto es una mierda de prueba.".split())]
        trans = os.path.join(d, "t.json")
        json.dump({"language": "es", "duration": 4.0, "words": palabras}, open(trans, "w"))
        extras = os.path.join(d, "e.json")
        json.dump({"censurar": True, "banners": [{"texto": "Gancho 🤯", "hasta": 2.0}],
                   "escenas": [{"tipo": "dividida", "desde": 0.5, "hasta": 2.5, "modo": "apilada"}]}, open(extras, "w"))
        out = os.path.join(d, "public", "edit.json")
        os.makedirs(os.path.dirname(out))
        subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "plan_edit.py"), trans, out, "--extras", extras,
                        "--ancho", "1080", "--alto", "1920", "--formato", "reel", "--encuadre", "recorte"], check=True,
                       capture_output=True)
        with open(out) as f:
            e = json.load(f)
        self.assertEqual(len(e["pitidos"]), 1)
        self.assertIn("m*****", " ".join(c["text"] for c in e["captions"]))
        self.assertEqual(e["banners"][0]["desdeMs"], 0)
        self.assertGreater(e["banners"][0]["hastaMs"], 0)
        self.assertIn("areaVideo", e)
        self.assertEqual(e["escenas"][0]["tipo"], "dividida")


if __name__ == "__main__":
    unittest.main()
