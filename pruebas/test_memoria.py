"""En un Mac con poca memoria, el render usa menos hilos y un caché de video chico (si no, se traba)."""
from ayuda import RAIZ  # noqa: F401  (primero: deja importar los scripts)
import unittest

import editor


class PruebaMemoria(unittest.TestCase):
    def test_mac_de_8_gb(self):
        f = editor.flags_memoria({"total": 8.59, "disponible": 3.0})
        self.assertEqual(f[f.index("--concurrency") + 1], "2")
        self.assertLessEqual(int(f[f.index("--offthreadvideo-cache-size-in-bytes") + 1]), 300 * 1024 * 1024)

    def test_poca_memoria_libre_aunque_haya_mucha_ram(self):
        f = editor.flags_memoria({"total": 32, "disponible": 1.0})
        self.assertEqual(f[f.index("--concurrency") + 1], "2")

    def test_mac_grande_usa_lo_de_remotion(self):
        self.assertEqual(editor.flags_memoria({"total": 32, "disponible": 20}), [])

    def test_sin_datos_no_cambia_nada(self):
        self.assertEqual(editor.flags_memoria({"total": 0.0, "disponible": 0.0}), [])

    def test_medir_memoria(self):
        m = editor.memoria_gb()
        self.assertGreaterEqual(m["total"], 0)
        self.assertGreaterEqual(m["disponible"], 0)


if __name__ == "__main__":
    unittest.main()
