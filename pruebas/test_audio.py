"""Masterización: el audio final queda en -14 LUFS (±0,5) y con pico real <= -1 dBTP, venga bajito o saturado."""
from ayuda import audio_sintetico, carpeta_temporal  # (primero: deja importar los scripts)
import os
import unittest

import audio


class PruebaAudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = carpeta_temporal()

    def revisar(self, db_entrada):
        entrada = audio_sintetico(os.path.join(self.dir, f"in_{db_entrada}.wav"), db=db_entrada)
        salida = os.path.join(self.dir, f"out_{db_entrada}.m4a")
        m = audio.masterizar(entrada, salida, lufs=-14, pico_max=-1.0, kbps=192)
        final = audio.medir(salida)  # se mide de nuevo el archivo, no se confía en lo que devolvió
        self.assertAlmostEqual(final["lufs"], -14, delta=0.5)
        self.assertLessEqual(final["pico_dbtp"], -1.0)
        self.assertAlmostEqual(m["lufs"], final["lufs"], delta=0.05)

    def test_audio_bajito(self):
        self.revisar(-35)

    def test_audio_normal(self):
        self.revisar(-18)

    def test_audio_muy_fuerte(self):
        self.revisar(-4)

    def test_silencio_total_da_error_claro(self):
        import subprocess

        ruta = os.path.join(self.dir, "silencio.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "2", ruta], check=True)
        with self.assertRaises(RuntimeError):
            audio.masterizar(ruta, os.path.join(self.dir, "x.m4a"))


if __name__ == "__main__":
    unittest.main()
