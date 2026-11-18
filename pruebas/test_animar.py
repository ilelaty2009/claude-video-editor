"""Animaciones desde una receta: tiempos de cada paso, campos que pasan al video y errores claros."""
from ayuda import RAIZ, carpeta_temporal  # noqa: F401  (primero: deja importar los scripts)
import json
import os
import shutil
import unittest

import animar
import editor


class PruebaAnimar(unittest.TestCase):
    def setUp(self):
        self.dir = carpeta_temporal()
        self.json_publico = os.path.join(RAIZ, "public", "animacion.json")
        self.respaldo = self.json_publico + ".respaldo_prueba"
        if os.path.exists(self.json_publico):
            shutil.copy2(self.json_publico, self.respaldo)

    def tearDown(self):
        if os.path.exists(self.respaldo):
            shutil.move(self.respaldo, self.json_publico)

    def receta(self, datos):
        p = os.path.join(self.dir, "r.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(datos, f)
        return p

    def test_sin_voz_cada_paso_dura_lo_que_se_tarda_en_leer(self):
        r = self.receta({"tipo": "grafica", "voz": False, "musica": False, "valores": [1, 5], "etiqueta": "X",
                         "pasos": [{"texto": "uno dos tres"}, {"texto": "cuatro", "segundos": 4}]})
        self.assertEqual(animar.principal([r, "--formato", "cuadrado", "--solo-preparar"]), 0)
        with open(self.json_publico, encoding="utf-8") as f:
            d = json.load(f)
        self.assertEqual((d["width"], d["height"], d["fps"]), (1080, 1080, 60))
        p0, p1 = d["pasos"]
        self.assertEqual(p0["desdeMs"], 0)
        self.assertEqual(p1["desdeMs"], p0["hastaMs"])  # pegados, sin huecos
        self.assertAlmostEqual((p1["hastaMs"] - p1["desdeMs"]) / 1000, 4 + 0.6, delta=0.05)  # 4 s + cierre
        self.assertEqual(d["valores"], [1, 5])
        self.assertEqual(d["durationInFrames"], round(p1["hastaMs"] / 1000 * 60))

    def test_capas_del_despiece(self):
        r = self.receta({"tipo": "despiece", "voz": False, "capas": [{"nombre": "A"}, {"nombre": "B"}], "pasos": [{"texto": "x"}]})
        animar.principal([r, "--solo-preparar"])
        with open(self.json_publico, encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)["capasDespiece"]), 2)

    def test_errores_claros(self):
        with self.assertRaises(editor.ErrorEditor) as e:
            animar.principal([self.receta({"tipo": "pelicula3d", "pasos": [{"texto": "x"}]}), "--solo-preparar"])
        self.assertIn("Tipo de animación desconocido", e.exception.que)
        with self.assertRaises(editor.ErrorEditor):
            animar.principal([self.receta({"tipo": "minimal", "pasos": []}), "--solo-preparar"])
        with self.assertRaises(editor.ErrorEditor):
            animar.principal(["/no/existe.json", "--solo-preparar"])

    @unittest.skipUnless(shutil.which("say"), "solo en macOS (voz narrada)")
    def test_con_voz_el_paso_dura_lo_que_dura_la_voz(self):
        r = self.receta({"tipo": "minimal", "musica": False, "pasos": [{"texto": "Hola, esto es una prueba de la voz narrada."}]})
        animar.principal([r, "--solo-preparar"])
        with open(self.json_publico, encoding="utf-8") as f:
            p = json.load(f)["pasos"][0]
        self.assertGreater((p["hastaMs"] - p["desdeMs"]) / 1000, 2.0)


if __name__ == "__main__":
    unittest.main()
