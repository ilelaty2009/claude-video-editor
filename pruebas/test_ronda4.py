"""Ronda 4: sincronía de subtítulos, niveles de música/efectos contra la voz, cuadros con fallas, editar borrando
texto, clips de un video largo, EDL, grabaciones de pantalla, storyboard, sonidos generados, marca y memoria."""
from ayuda import RAIZ, carpeta_temporal  # noqa: F401  (primero: deja importar los scripts)
import json
import os
import subprocess
import sys
import unittest
import wave

import numpy as np

import clips
import control_calidad
import editor
import exportar_edl
import generar_sonido
import guion
import marca
import mezcla
import pantalla
import recorte_persona
import sincronia
import sonidos
import storyboard

PY = sys.executable


def palabras_de(texto, inicio=0.5, paso=0.4, largo=0.3):
    return [{"text": w, "start": round(inicio + i * paso, 3), "end": round(inicio + i * paso + largo, 3), "prob": 0.95}
            for i, w in enumerate(texto.split())]


class PruebaSincronia(unittest.TestCase):
    def setUp(self):
        # "voz" sintética: ráfagas de ruido exactamente donde están las palabras
        self.palabras = [{"text": "x", "start": s, "end": s + 0.5} for s in (0.6, 1.5, 2.9, 3.6, 5.2, 6.4, 7.1, 8.8)]
        sr = 16000
        x = np.zeros(sr * 10, np.float32)
        rng = np.random.default_rng(1)
        for w in self.palabras:
            x[int(w["start"] * sr) : int(w["end"] * sr)] = rng.standard_normal(int(0.5 * sr)) * 0.3
        self.wav = os.path.join(carpeta_temporal(), "voz.wav")
        with wave.open(self.wav, "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sr)
            f.writeframes((x * 32767).astype("<i2").tobytes())

    def test_en_sincronia_mide_cero(self):
        self.assertAlmostEqual(sincronia.desfase_ms(sincronia.envolvente(self.wav), self.palabras), 0, delta=15)

    def test_detecta_cuanto_estan_corridas(self):
        env = sincronia.envolvente(self.wav)
        for corrimiento in (-250, 180, 320):
            corridas = sincronia.correr_palabras([dict(w) for w in self.palabras], -corrimiento)
            self.assertAlmostEqual(sincronia.desfase_ms(env, corridas), corrimiento, delta=20)

    def test_corrige_solo_si_pasa_de_120_ms(self):
        d = carpeta_temporal()
        for corrimiento, debe_corregir in ((60, False), (250, True)):
            ruta = os.path.join(d, f"t{corrimiento}.json")
            with open(ruta, "w") as f:
                json.dump({"words": sincronia.correr_palabras([dict(w) for w in self.palabras], -corrimiento)}, f)
            r = sincronia.revisar(self.wav, ruta)
            self.assertEqual(bool(r["corregido"]), debe_corregir)
            with open(ruta) as f:
                t = json.load(f)
            self.assertAlmostEqual(t["words"][0]["start"], 0.6 if debe_corregir else 0.6 - corrimiento / 1000, delta=0.03)
            self.assertFalse(sincronia.revisar(self.wav, ruta)["nuevo"])  # no se corrige dos veces


class PruebaNiveles(unittest.TestCase):
    def capas(self, musica_db, efecto_db):
        n = mezcla.SR * 4
        rng = np.random.default_rng(2)
        ruido = lambda db: (rng.standard_normal((n, 2)) * 10 ** (db / 20)).astype(np.float32)  # noqa: E731
        return {"voz": ruido(-20), "musica": ruido(musica_db), "n": n, "hayMusica": True,
                "efectos": [{"cue": {}, "dest": 1000, "audio": ruido(efecto_db)[:4800]}]}

    def test_musica_que_tapa_la_voz_se_baja(self):
        c = self.capas(musica_db=-24, efecto_db=-40)  # solo 4 dB debajo de la voz
        antes = mezcla._db(c["musica"])
        i = mezcla.nivelar(c, [{"startMs": 0, "endMs": 4000}])
        self.assertGreater(i["musicaBajadaDb"], 0)
        self.assertAlmostEqual(i["musicaBajoVozDb"], 15, delta=0.5)
        self.assertAlmostEqual(antes - mezcla._db(c["musica"]), i["musicaBajadaDb"], delta=0.3)

    def test_musica_bien_mezclada_no_se_toca(self):
        c = self.capas(musica_db=-45, efecto_db=-40)
        i = mezcla.nivelar(c, [{"startMs": 0, "endMs": 4000}])
        self.assertEqual(i["musicaBajadaDb"], 0)
        self.assertGreater(i["musicaBajoVozDb"], 12)
        self.assertEqual(i["efectosBajados"], 0)

    def test_efecto_mas_fuerte_que_la_voz_se_baja(self):
        c = self.capas(musica_db=-45, efecto_db=-8)  # 12 dB más fuerte que la voz
        i = mezcla.nivelar(c, [{"startMs": 0, "endMs": 4000}])
        self.assertEqual(i["efectosBajados"], 1)
        self.assertLessEqual(i["efectoMasFuerteDb"], 3)

    def test_informe_en_espanol(self):
        t = mezcla.texto_informe({"musicaBajoVozDb": 15, "musicaBajadaDb": 6, "efectos": 3, "efectosBajados": 1})
        self.assertIn("tapaba la voz", t)
        self.assertIn("3 efectos", t)


class PruebaCuadrosConFallas(unittest.TestCase):
    def test_encuentra_un_parpadeo_y_no_inventa(self):
        d = carpeta_temporal()
        limpio, malo = os.path.join(d, "ok.mp4"), os.path.join(d, "malo.mp4")
        base = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x336699:s=320x180:r=30:d=2"]
        subprocess.run(base + ["-pix_fmt", "yuv420p", limpio], check=True)
        subprocess.run(base + ["-vf", "drawbox=c=white:t=fill:enable='eq(n,30)'", "-pix_fmt", "yuv420p", malo], check=True)
        self.assertEqual(control_calidad.cuadros_con_fallas(limpio), [])
        fallas = control_calidad.cuadros_con_fallas(malo)
        self.assertEqual(len(fallas), 1)
        self.assertAlmostEqual(fallas[0], 1.0, delta=0.05)


class PruebaGuion(unittest.TestCase):
    def setUp(self):
        self.dir = carpeta_temporal()
        self.trans = os.path.join(self.dir, "v_transcripcion.json")
        self.palabras = palabras_de("Hola a todos. Hoy vamos a hablar de historia. Eh, este, bueno. Empecemos ya.")
        with open(self.trans, "w") as f:
            json.dump({"words": self.palabras}, f)
        self.extras = os.path.join(self.dir, "v_extras.json")

    def test_sin_borrar_nada_no_quita_nada(self):
        guion.exportar(self.trans)
        r = guion.aplicar(self.trans, self.extras)
        self.assertEqual(r["tramos"], [])

    def test_borrar_una_frase_la_quita_del_video(self):
        g = guion.exportar(self.trans)
        with open(g, encoding="utf-8") as f:
            lineas = [linea for linea in f.read().splitlines() if "Eh, este" not in linea]
        with open(g, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))
        with open(self.extras, "w") as f:
            json.dump({"titulo": "X", "quitar": [{"desde": 50, "hasta": 51}]}, f)  # un corte puesto a mano
        r = guion.aplicar(self.trans, self.extras)
        self.assertEqual(len(r["tramos"]), 1)
        self.assertEqual(r["tramos"][0]["texto"], "Eh, este, bueno.")
        with open(self.extras) as f:
            e = json.load(f)
        self.assertEqual(e["titulo"], "X")  # no toca lo demás
        self.assertEqual(len(e["quitar"]), 2)  # el manual se respeta
        guion.aplicar(self.trans, self.extras)  # aplicar dos veces no duplica
        with open(self.extras) as f:
            self.assertEqual(len(json.load(f)["quitar"]), 2)

    def test_palabras_nuevas_se_ignoran_y_se_avisan(self):
        tramos, nuevas = guion.tramos_borrados(self.palabras, "Hola a todos. Hoy vamos a hablar de matemáticas avanzadas.".split())
        self.assertIn("matemáticas", nuevas)
        self.assertTrue(any("historia" in t["texto"] for t in tramos))


class PruebaClips(unittest.TestCase):
    def test_empiezan_y_terminan_en_frases_completas(self):
        texto = ("¿Sabías que las plantas hacen su comida? Usan luz, agua y aire para lograrlo todos los días. "
                 "Eso se llama fotosíntesis y pasa en las hojas. Sin ella no habría oxígeno para respirar. "
                 "Por eso cuidar los árboles es cuidarnos a nosotros mismos. ¡Gracias por ver!")
        palabras = palabras_de(texto, paso=0.5, largo=0.42)
        lista = clips.candidatos(palabras, 8, 20)
        self.assertTrue(lista)
        inicios = {palabras[g[0]]["start"] for g in guion.frases(palabras)}
        finales = {palabras[g[-1]]["end"] for g in guion.frases(palabras)}
        for c in lista:
            self.assertTrue(8 <= c["segundos"] <= 20)
            self.assertTrue(any(abs(c["desde"] + 0.1 - i) < 0.02 or c["desde"] == 0 for i in inicios))
            self.assertTrue(any(abs(c["hasta"] - 0.2 - f) < 0.02 for f in finales))
        mejores = clips.escoger(lista, 3)
        self.assertEqual(mejores, sorted(mejores, key=lambda c: c["desde"]))
        con_pregunta = max(lista, key=lambda c: c["puntaje"])
        self.assertIn("pregunta", " ".join(con_pregunta["razones"]))  # el gancho con pregunta gana


class PruebaEdl(unittest.TestCase):
    def test_codigo_de_tiempo_y_cortes_pegados(self):
        self.assertEqual(exportar_edl.tc(0, 30), "00:00:00:00")
        self.assertEqual(exportar_edl.tc(30 * 3661 + 7, 30), "01:01:01:07")
        edit = {"fps": 60, "segments": [{"trimBefore": 60, "durationInFrames": 120, "from": 0}, {"trimBefore": 300, "durationInFrames": 60, "from": 120}]}
        edl = exportar_edl.a_edl(edit, "videos/mi video.mov", 30)
        eventos = [linea.split() for linea in edl.splitlines() if linea[:3].isdigit()]
        self.assertEqual(len(eventos), 2)
        self.assertEqual(eventos[0][4:], ["00:00:01:00", "00:00:03:00", "00:00:00:00", "00:00:02:00"])
        self.assertEqual(eventos[1][6], eventos[0][7])  # el segundo empieza donde termina el primero
        self.assertIn("mi video.mov", edl)


class PruebaPantalla(unittest.TestCase):
    def test_se_acerca_a_donde_pasa_algo_y_vuelve(self):
        fps = pantalla.FPS
        cajas = [None] * fps + [(0.1, 0.1, 0.3, 0.2)] * (2 * fps) + [None] * (4 * fps) + [(0.0, 0.0, 1.0, 1.0)] * fps
        r = pantalla.recorrido(cajas, 9 / 16)
        self.assertEqual(r[0], {"t": 0.0, "x": 0.5, "y": 0.5, "z": 1.0})
        cerca = r[1]
        self.assertGreater(cerca["z"], 1.5)
        self.assertAlmostEqual(cerca["x"], 0.2, delta=0.02)
        self.assertTrue(any(p["z"] == 1.0 and p["t"] > cerca["t"] for p in r[2:]))  # vuelve a la vista completa
        tiempos = [p["t"] for p in r]
        self.assertEqual(tiempos, sorted(tiempos))
        self.assertTrue(all(b - a >= 1.2 - 1e-6 for a, b in zip(tiempos[1:], tiempos[2:])))  # sin saltos nerviosos

    def test_grabacion_real_sintetica(self):
        d = carpeta_temporal()
        v = os.path.join(d, "p.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=white:s=640x360:r=30:d=4",
                        "-vf", "drawbox=x=40:y=40:w='min(200,(t-1)*200)':h=20:color=black:t=fill:enable='gte(t,1)'",
                        "-pix_fmt", "yuv420p", v], check=True)
        r = pantalla.analizar(v)
        self.assertGreaterEqual(len(r), 2)
        self.assertLess(r[1]["x"], 0.5)  # la acción está arriba a la izquierda
        self.assertLess(r[1]["y"], 0.5)


class PruebaStoryboard(unittest.TestCase):
    def setUp(self):
        self.edit = {"fps": 60, "durationInFrames": 1200, "titulo": "Hola",
                     "captions": [{"text": " uno", "startMs": 500, "endMs": 800}, {"text": " dos", "startMs": 6200, "endMs": 6500}],
                     "escenas": [{"tipo": "lista", "desdeMs": 6000, "hastaMs": 9000, "titulo": "Cosas", "idExtra": 0},
                                 {"tipo": "zoom", "desdeMs": 10000, "hastaMs": 12000, "auto": True}],
                     "banners": [{"texto": "Gancho", "desdeMs": 0, "hastaMs": 20000}],
                     "cierre": {"desdeFrame": 1020, "titulo": "Gracias"}}

    def test_un_tramo_por_cada_cosa_y_sin_las_automaticas(self):
        beats = storyboard.beats_de(self.edit)
        tipos = [b["tipo"] for b in beats]
        for esperado in ("titulo", "lista", "banner", "cierre", "hablando"):
            self.assertIn(esperado, tipos)
        self.assertNotIn("zoom", tipos)  # los acercamientos automáticos no se califican
        self.assertEqual(len({b["id"] for b in beats}), len(beats))
        self.assertEqual([b["desdeMs"] for b in beats], sorted(b["desdeMs"] for b in beats))
        lista = next(b for b in beats if b["tipo"] == "lista")
        self.assertEqual(lista["ref"], {"escena": 0})  # la nota vuelve a la escena correcta de los extras
        self.assertIn("dos", lista["dice"])

    def test_pagina_con_botones_notas_y_respuestas(self):
        beats = storyboard.beats_de(self.edit)
        for b in beats:
            b["clip"] = f"clips/{b['id']}.mp4"
        html = storyboard.pagina({"nombre": "x", "ronda": 2, "tipo": "storyboard", "beats": beats, "respuestasClaude": {beats[0]["id"]: "Listo <ok>"}})
        for texto in ("Keep", "Maybe", "Drop", "Enviar revisión", "Ronda 2", "textarea", "Listo &lt;ok&gt;"):
            self.assertIn(texto, html)


class PruebaSonidos(unittest.TestCase):
    def test_los_7_sonidos_se_generan_bien(self):
        d = carpeta_temporal()
        for tipo in generar_sonido.TIPOS:
            ruta = generar_sonido.generar(tipo, os.path.join(d, tipo + ".wav"))
            with wave.open(ruta) as w:
                x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            self.assertGreater(len(x), generar_sonido.SR * 0.04, tipo)
            self.assertTrue(np.isfinite(x).all(), tipo)
            self.assertGreater(np.abs(x).max(), 0.2, tipo)
            self.assertLessEqual(np.abs(x).max(), 0.96, tipo)
            self.assertLess(abs(x[0]), 0.05, tipo)  # sin clic al empezar
        a = generar_sonido.sintetizar("glitch", 1)
        self.assertTrue(np.array_equal(a, generar_sonido.sintetizar("glitch", 1)))  # misma semilla = mismo sonido
        self.assertFalse(np.array_equal(a, generar_sonido.sintetizar("glitch", 2)))

    def test_tus_sonidos_mandan_sobre_los_de_fabrica(self):
        d = carpeta_temporal()
        os.makedirs(os.path.join(d, "sfx", "propios"))
        for nombre in ("whoosh.wav", "glitch.wav", "propios/whoosh.wav"):
            generar_sonido.generar("swipe", os.path.join(d, "sfx", nombre))
        edit = {"fps": 60, "durationInFrames": 600, "sfx": True, "look": "cine", "captions": [], "capitulos": [],
                "escenas": [{"tipo": "lista", "desdeMs": 1000, "hastaMs": 4000, "items": []},
                            {"tipo": "cinetica", "desdeMs": 5000, "hastaMs": 8000, "entrada": "glitch", "palabras": []}]}
        sonidos.poner_cues(edit, d)
        archivos = {c["archivo"] for c in edit["cues"]}
        self.assertIn("sfx/propios/whoosh.wav", archivos)  # el de Pablo, no el de fábrica
        self.assertNotIn("sfx/whoosh.wav", archivos)
        self.assertIn("sfx/glitch.wav", archivos)  # la transición glitch suena a glitch


class PruebaMarcaYMemoria(unittest.TestCase):
    def test_saca_colores_con_personalidad(self):
        css = "a{color:#ffffff;background:#111111} .b{color:#E63946} .c{color:#e63946;border:1px solid #cccccc} .d{background:rgb(29, 53, 87)} .e{color:#2A9D8F}"
        colores = marca.colores_de([css])
        self.assertEqual(colores[0], "#E63946")  # el más usado
        self.assertNotIn("#FFFFFF", colores)
        self.assertNotIn("#CCCCCC", colores)
        self.assertIn("#2A9D8F", colores)

    def test_saca_fuentes_de_google_y_no_italicas(self):
        html = '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&family=Playfair+Display+Italic&display=swap" rel="stylesheet">'
        fuentes = marca.fuentes_de(html, ["body{font-family: 'Space Grotesk', sans-serif}"])
        self.assertEqual(fuentes, ["Space Grotesk"])

    def test_con_poca_memoria_un_solo_hilo(self):
        f = editor.flags_memoria({"total": 8.59, "disponible": 0.6})
        self.assertEqual(f[f.index("--concurrency") + 1], "1")

    def test_tamano_para_el_modelo_de_recorte(self):
        for w, h in ((1920, 1080), (1080, 1920), (1080, 1080), (1620, 1080)):
            mw, mh = recorte_persona.tam_modelo(w, h)
            self.assertEqual((mw % 32, mh % 32), (0, 0))
            self.assertAlmostEqual(mw / mh, w / h, delta=0.08)
            self.assertEqual(min(mw, mh), 384)


class PruebaPlanRonda4(unittest.TestCase):
    def plan(self, extras, transcripcion_extra=None):
        d = carpeta_temporal()
        trans = os.path.join(d, "x_transcripcion.json")
        datos = {"language": "es", "duration": 8.0, "words": palabras_de("Con eso fabrican su propio alimento. Y eso es todo por hoy.")}
        datos.update(transcripcion_extra or {})
        with open(trans, "w") as f:
            json.dump(datos, f)
        ex = os.path.join(d, "e.json")
        with open(ex, "w") as f:
            json.dump(extras, f)
        out = os.path.join(d, "public", "edit.json")
        os.makedirs(os.path.dirname(out))
        subprocess.run([PY, os.path.join(RAIZ, "scripts", "plan_edit.py"), trans, out, "--extras", ex, "--formato", "reel",
                        "--ancho", "1080", "--alto", "1920", "--encuadre", "recorte"], check=True, capture_output=True)
        with open(out) as f:
            return json.load(f)

    def test_frase_cinetica_usa_lo_que_se_dice_en_su_instante(self):
        e = self.plan({"escenas": [{"tipo": "cinetica", "desde": 0.4, "hasta": 3.0}]})
        esc = e["escenas"][0]
        self.assertEqual(esc["idExtra"], 0)
        self.assertEqual([p["texto"] for p in esc["palabras"]][:3], ["Con", "eso", "fabrican"])
        tiempos = [p["enMs"] for p in esc["palabras"]]
        self.assertEqual(tiempos, sorted(tiempos))

    def test_banner_con_estilo_y_palabra_en_caja(self):
        e = self.plan({"banners": [{"texto": "Hola", "estilo": "vidrio"}], "destacadas": [{"palabra": "alimento", "caja": True}]})
        self.assertEqual(e["banners"][0]["estilo"], "vidrio")
        self.assertTrue(next(c for c in e["captions"] if "alimento" in c["text"])["caja"])

    def test_desfase_a_mano_mueve_subtitulos_pero_no_cortes(self):
        a = self.plan({})
        b = self.plan({"desfaseSubtitulos": 200})
        self.assertEqual(a["segments"], b["segments"])
        self.assertEqual(b["captions"][0]["startMs"] - a["captions"][0]["startMs"], 200)

    def test_los_subtitulos_nunca_se_adelantan_a_la_voz(self):
        a = self.plan({})
        b = self.plan({}, {"desfaseMedidoMs": 45.0, "sincroniaMs": 0.0})
        c = self.plan({}, {"desfaseMedidoMs": -60.0, "sincroniaMs": 0.0})
        d = self.plan({}, {"desfaseMedidoMs": 400.0, "sincroniaMs": 0.0})
        self.assertEqual(b["captions"][0]["startMs"] - a["captions"][0]["startMs"], 45)
        self.assertEqual(c["captions"][0]["startMs"], a["captions"][0]["startMs"])  # nunca se adelantan
        self.assertEqual(d["captions"][0]["startMs"] - a["captions"][0]["startMs"], 100)  # tope de 100 ms


if __name__ == "__main__":
    unittest.main()
