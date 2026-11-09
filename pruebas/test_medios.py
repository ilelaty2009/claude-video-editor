"""Medición de videos (fps, tamaño, duración) con y sin ffprobe, y elección del fps de trabajo."""
from ayuda import carpeta_temporal, video_sintetico  # (primero: deja importar los scripts)
import os
import shutil
import unittest
from unittest import mock

import medios


class PruebaMedios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = carpeta_temporal()
        cls.v60 = video_sintetico(os.path.join(d, "a.mp4"), 640, 360, fps=60, segundos=2)
        cls.v30 = video_sintetico(os.path.join(d, "b.mp4"), 360, 640, fps=30, segundos=1.5)
        cls.mudo = video_sintetico(os.path.join(d, "c.mp4"), 320, 240, fps=30, segundos=1, con_audio=False)

    def test_info(self):
        d = medios.info(self.v60)
        self.assertEqual((d["ancho"], d["alto"]), (640, 360))
        self.assertAlmostEqual(d["fps"], 60, places=2)
        self.assertAlmostEqual(d["duracion"], 2.0, delta=0.1)
        self.assertTrue(d["tiene_audio"])
        self.assertFalse(medios.info(self.mudo)["tiene_audio"])

    def test_info_sin_ffprobe(self):
        with mock.patch.object(shutil, "which", return_value=None):
            d = medios.info(self.v30)
        self.assertEqual((d["ancho"], d["alto"]), (360, 640))
        self.assertAlmostEqual(d["fps"], 30, places=2)

    def test_contar_cuadros(self):
        self.assertEqual(medios.contar_cuadros(self.v60), 120)

    def test_archivo_que_no_existe(self):
        with self.assertRaises(medios.ErrorMedio):
            medios.info("/no/existe.mov")

    def test_fps_de_trabajo(self):
        self.assertEqual(medios.fps_de_trabajo(59.94), 60)
        self.assertEqual(medios.fps_de_trabajo(30.0), 30)
        self.assertEqual(medios.fps_de_trabajo(29.97), 30)
        self.assertEqual(medios.fps_de_trabajo(25), 25)
        self.assertEqual(medios.fps_de_trabajo(120), 60)


if __name__ == "__main__":
    unittest.main()
