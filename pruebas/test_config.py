"""La configuración (editor.config.json) es coherente: formatos, presets, calidades y 60 fps."""
import json
import os
import unittest

from ayuda import RAIZ

CFG = json.load(open(os.path.join(RAIZ, "editor.config.json"), encoding="utf-8"))


class PruebaConfig(unittest.TestCase):
    def test_siempre_60_fps(self):
        self.assertEqual(CFG["fps"], 60)

    def test_formatos_pedidos(self):
        esperado = {"tv": (1920, 1080), "reel": (1080, 1920), "cuadrado": (1080, 1080), "retrato": (1080, 1350)}
        for nombre, (w, h) in esperado.items():
            f = CFG["formatos"][nombre]
            self.assertEqual((f["ancho"], f["alto"]), (w, h), nombre)
            z = f["zonaSegura"]
            self.assertLess(z["izquierda"] + z["derecha"], 0.5)
            self.assertLess(z["arriba"] + z["abajo"], 0.5)

    def test_presets_apuntan_a_cosas_que_existen(self):
        for nombre, p in CFG["presets"].items():
            self.assertIn(p["formato"], CFG["formatos"], nombre)
            self.assertIn(p["estilo"], CFG["estilos"], nombre)
            self.assertIn(p["calidad"], CFG["calidades"], nombre)
        self.assertEqual(CFG["presets"]["colegio-tv"]["formato"], "tv")
        self.assertEqual(CFG["presets"]["tiktok"]["formato"], "reel")

    def test_calidades(self):
        for nombre in ("preview", "final", "maxima"):
            q = CFG["calidades"][nombre]
            self.assertTrue(0 <= q["crf"] <= 51)
        self.assertLess(CFG["calidades"]["preview"]["escala"], 1)
        self.assertLess(CFG["calidades"]["maxima"]["crf"], CFG["calidades"]["final"]["crf"])

    def test_audio(self):
        self.assertEqual(CFG["audio"]["lufs"], -14)
        self.assertLessEqual(CFG["audio"]["picoMaximoDbtp"], -1.0)


if __name__ == "__main__":
    unittest.main()
