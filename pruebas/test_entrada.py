"""Entrada de videos: HDR del iPhone a color normal, y varios clips unidos en orden."""
from ayuda import RAIZ, carpeta_temporal, video_sintetico  # noqa: F401  (primero: deja importar los scripts)
import json
import os
import subprocess
import unittest

import editor
import medios

CFG = json.load(open(os.path.join(RAIZ, "editor.config.json"), encoding="utf-8"))


def video_hlg(ruta):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=1",
                    "-f", "lavfi", "-i", "sine=duration=1", "-c:v", "libx264", "-pix_fmt", "yuv420p10le",
                    "-bsf:v", "h264_metadata=transfer_characteristics=18:colour_primaries=9:matrix_coefficients=9",
                    "-c:a", "aac", "-shortest", ruta], check=True)
    return ruta


class PruebaEntrada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = carpeta_temporal()

    def test_detecta_hdr_y_lo_convierte(self):
        v = video_hlg(os.path.join(self.dir, "hlg.mp4"))
        d = medios.info(v)
        self.assertTrue(d["hdr"])
        self.assertEqual(d["transferencia"], "arib-std-b67")
        filtro = editor.filtro_video("tv", "completo", CFG, 30, "", 0.5, d["transferencia"])
        self.assertIn("tonemap", filtro)
        salida = os.path.join(self.dir, "sdr.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", v, "-filter_complex", filtro, "-map", "[v]",
                        "-c:v", "libx264", "-preset", "ultrafast", salida], check=True)
        s = medios.info(salida)
        self.assertFalse(s["hdr"])
        self.assertEqual((s["ancho"], s["alto"]), (1920, 1080))

    def test_video_normal_no_es_hdr(self):
        v = video_sintetico(os.path.join(self.dir, "sdr_in.mp4"), 320, 240, segundos=1)
        self.assertFalse(medios.info(v)["hdr"])
        self.assertNotIn("tonemap", editor.filtro_video("tv", "completo", CFG, 30, "", 0.5, None))

    def test_varios_clips_se_unen_en_orden(self):
        a = video_sintetico(os.path.join(self.dir, "a.mp4"), 640, 360, segundos=1.0)
        b = video_sintetico(os.path.join(self.dir, "b.mp4"), 360, 640, segundos=1.5)  # otra orientación
        unido = editor.unir_clips([a, b], CFG, editor.Pasos(1))
        try:
            d = medios.info(unido)
            self.assertEqual((d["ancho"], d["alto"]), (640, 360))
            self.assertAlmostEqual(d["duracion"], 2.5, delta=0.15)
            self.assertTrue(d["tiene_audio"])
        finally:
            os.remove(unido)

    def test_varios_videos_en_la_linea_de_comandos(self):
        o = editor.leer_opciones(["v1.mov", "v2.mov", "--preset", "tiktok"], CFG)
        self.assertEqual(o.videos, ["v1.mov", "v2.mov"])
        self.assertEqual(o.video, "v1.mov")


if __name__ == "__main__":
    unittest.main()
