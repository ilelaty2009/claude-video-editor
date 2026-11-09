"""Los 4 formatos salen del tamaño exacto, al fps de trabajo y sin deformar, venga el video horizontal o vertical."""
from ayuda import RAIZ, carpeta_temporal, video_sintetico  # (primero: deja importar los scripts)
import json
import os
import subprocess
import unittest

import editor
import medios

CFG = json.load(open(os.path.join(RAIZ, "editor.config.json"), encoding="utf-8"))


class PruebaFormatos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = carpeta_temporal()
        cls.horizontal = video_sintetico(os.path.join(cls.dir, "h.mp4"), 1620, 1080, fps=30, segundos=1)
        cls.vertical = video_sintetico(os.path.join(cls.dir, "v.mp4"), 1080, 1920, fps=30, segundos=1)

    def preparar(self, origen, formato, encuadre_pedido=""):
        d = medios.info(origen)
        enc = editor.plan_encuadre(formato, encuadre_pedido, d, CFG)
        filtro = editor.filtro_video(formato, enc, CFG, 30, "", 0.55)
        salida = os.path.join(self.dir, f"{formato}_{enc}_{os.path.basename(origen)}")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", origen, "-filter_complex", filtro, "-map", "[v]",
                        "-c:v", "libx264", "-preset", "ultrafast", salida], check=True)
        return enc, medios.info(salida)

    def test_cada_formato_y_encuadre(self):
        for formato, f in CFG["formatos"].items():
            for origen in (self.horizontal, self.vertical):
                for pedido in ("", "completo", "relleno", "recorte"):
                    with self.subTest(formato=formato, origen=os.path.basename(origen), encuadre=pedido):
                        enc, d = self.preparar(origen, formato, pedido)
                        self.assertEqual((d["ancho"], d["alto"]), (f["ancho"], f["alto"]))
                        self.assertAlmostEqual(d["fps"], 30, places=2)

    def test_tv_nunca_recorta(self):
        d = medios.info(self.vertical)
        self.assertEqual(editor.plan_encuadre("tv", "recorte", d, CFG), "completo")

    def test_auto_en_reel(self):
        self.assertEqual(editor.plan_encuadre("reel", "", medios.info(self.horizontal), CFG), "relleno")
        self.assertEqual(editor.plan_encuadre("reel", "", medios.info(self.vertical), CFG), "recorte")

    def test_alias_de_formatos(self):
        a = editor.leer_opciones(["x.mov", "--formato", "9:16"], CFG)
        self.assertEqual(a.formato, "reel")
        a = editor.leer_opciones(["x.mov", "--formato", "4:5"], CFG)
        self.assertEqual(a.formato, "retrato")
        a = editor.leer_opciones(["x.mov", "--preset", "colegio-tv"], CFG)
        self.assertEqual((a.formato, a.estilo, a.calidad), ("tv", "clase", "final"))
        a = editor.leer_opciones(["x.mov", "--preset", "tiktok", "--formato", "cuadrado"], CFG)
        self.assertEqual((a.formato, a.estilo), ("cuadrado", "tiktok"))  # la línea de comandos manda

    def test_formato_desconocido_da_error_en_espanol(self):
        with self.assertRaises(editor.ErrorEditor) as e:
            editor.leer_opciones(["x.mov", "--formato", "cine"], CFG)
        self.assertIn("No conozco el formato", e.exception.que)


if __name__ == "__main__":
    unittest.main()
