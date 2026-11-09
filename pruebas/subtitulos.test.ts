// Subtítulos: máximo 2 líneas, nunca se corta una palabra, todo dentro de la zona segura de cada formato,
// legibles desde el fondo del salón y con contraste alto.
import { describe, expect, it } from "vitest";
import config from "../editor.config.json";
import { rectSeguro } from "../src/formatos";
import { anchoTexto, contraste, paginar, textoVisible } from "../src/subtitulos/disposicion";
import { claveFuente, estilosSub, NombreEstiloSub } from "../src/subtitulos/estilos";
import { altoBloque, arribaBloque, ubicar } from "../src/subtitulos/ubicacion";

const frases = [
  "Hola a todos, hoy les voy a contar cómo funciona la fotosíntesis en las plantas.",
  "La Revolución Francesa empezó en 1789 y cambió para siempre la política de Europa.",
  "Electroencefalografista otorrinolaringólogo desoxirribonucleico anticonstitucionalmente.",
  "¿Sabían que el 70 % de la superficie de la Tierra está cubierta de agua? ¡Increíble!",
  "Ibn Khaldun fue historiador, sociólogo, filósofo y economista: un verdadero polímata.",
  "Sí. No. Tal vez. Bueno, a ver, eh, este, o sea, ¿sí me entienden lo que les digo?",
];

const palabrasDe = (texto: string) => {
  let t = 0;
  return texto.split(" ").map((w, i) => {
    const p = { text: w, startMs: t, endMs: t + 280, destacada: i === 3 };
    t += 320;
    return p;
  });
};

const estilos = Object.keys(estilosSub) as NombreEstiloSub[];
const formatos = Object.keys(config.formatos) as (keyof typeof config.formatos)[];

describe("subtítulos en cada estilo y formato", () => {
  for (const nombre of estilos) {
    for (const f of formatos) {
      const { ancho, alto, zonaSegura } = config.formatos[f];
      for (const encuadre of ["completo", "relleno", "recorte"]) {
        it(`${nombre} en ${f} (${encuadre})`, () => {
          const e = estilosSub[nombre];
          const u = ubicar(e, ancho, alto, zonaSegura, encuadre);
          const r = rectSeguro(ancho, alto, zonaSegura);
          for (const frase of frases) {
            const palabras = palabrasDe(frase);
            const paginas = paginar(palabras, {
              anchoMax: u.anchoMax,
              tam: u.tam,
              fuente: claveFuente(e),
              mayusculas: e.mayusculas,
              separacion: u.separacion,
              extraPorPalabra: u.extraPorPalabra,
              maxLineas: e.maxLineas,
              maxPalabras: e.maxPalabras,
              escalaDestacada: e.escalaDestacada,
            });
            // todas las palabras, en orden, una sola vez y enteras (ninguna se corta)
            const usadas = paginas.flatMap((p) => p.lineas.flat());
            expect(usadas).toEqual(palabras.map((_, i) => i));
            for (const p of paginas) {
              expect(p.lineas.length).toBeLessThanOrEqual(e.maxLineas); // máximo 2 líneas
              for (const w of p.anchos) expect(w * p.escala).toBeLessThanOrEqual(u.anchoMax + 0.5); // no se sale a los lados
              if (frase.startsWith("Electro")) {
                // caso extremo (palabras de 20+ letras): no se cortan; la página se achica lo justo
                expect(p.escala).toBeGreaterThanOrEqual(0.45);
              } else {
                expect(p.escala).toBe(1); // con palabras normales la letra nunca se achica
              }
              // el bloque completo queda dentro de la zona segura (arriba y abajo)
              const arriba = arribaBloque(u, p.lineas.length, p.escala);
              expect(arriba).toBeGreaterThanOrEqual(r.y - 0.5);
              expect(arriba + altoBloque(u, p.lineas.length, p.escala)).toBeLessThanOrEqual(r.y + r.alto + 0.5);
            }
          }
          // el área de subtítulos queda dentro de la zona segura a los lados
          expect(u.izquierda).toBeGreaterThanOrEqual(r.x - 0.5);
          expect(u.izquierda + u.ancho).toBeLessThanOrEqual(r.x + r.ancho + 0.5);
        });
      }
    }
  }
});

describe("legibilidad", () => {
  it("en TV la letra mide al menos 5,5 % del alto (se lee desde el fondo del salón)", () => {
    for (const nombre of estilos) {
      const u = ubicar(estilosSub[nombre], 1920, 1080);
      expect(u.tam / 1080, nombre).toBeGreaterThanOrEqual(0.055);
    }
  });

  it("en vertical la letra mide al menos 5,5 % del ancho", () => {
    for (const nombre of estilos) {
      const u = ubicar(estilosSub[nombre], 1080, 1920);
      expect(u.tam / 1080, nombre).toBeGreaterThanOrEqual(0.055);
    }
  });

  it("contraste de texto y palabra activa contra su borde o caja ≥ 4,5:1 (WCAG AA)", () => {
    for (const nombre of estilos) {
      const e = estilosSub[nombre];
      const fondo = e.caja?.color ?? e.borde?.color;
      expect(fondo, `${nombre} necesita borde o caja`).toBeTruthy();
      expect(contraste(e.colorTexto, fondo!), nombre).toBeGreaterThanOrEqual(4.5);
      if (e.pastilla) expect(contraste(e.pastilla.texto, e.pastilla.color), nombre).toBeGreaterThanOrEqual(4.5);
      else expect(contraste(e.colorActiva, fondo!), nombre).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("contraste: blanco sobre negro = 21, igual = 1", () => {
    expect(contraste("#FFFFFF", "#000000")).toBeCloseTo(21, 0);
    expect(contraste("#777777", "#777777")).toBeCloseTo(1, 5);
  });
});

describe("medidas de texto", () => {
  it("una palabra más larga mide más", () => {
    expect(anchoTexto("HOLA MUNDO", "Inter-900", 60)).toBeGreaterThan(anchoTexto("HOLA", "Inter-900", 60));
  });
  it("mayúsculas en español (con tildes y ñ)", () => {
    expect(textoVisible(" mañana, acción ", true)).toBe("MAÑANA, ACCIÓN");
  });
  it("las dos líneas quedan equilibradas", () => {
    const palabras = palabrasDe("uno dos tres cuatro cinco seis siete ocho").map((p) => ({ ...p, destacada: false }));
    const [p] = paginar(palabras, { anchoMax: 700, tam: 60, fuente: "Inter-900", mayusculas: true, separacion: 15, maxLineas: 2, maxPalabras: 8 });
    expect(p.lineas.length).toBe(2);
    expect(Math.abs(p.anchos[0] - p.anchos[1])).toBeLessThan(Math.max(...p.anchos) * 0.45);
  });
  it("una pausa larga o el fin de una frase cambian de página", () => {
    const palabras = [
      { text: "Hola.", startMs: 0, endMs: 300 },
      { text: "Bienvenidos", startMs: 400, endMs: 800 },
      { text: "todos", startMs: 2000, endMs: 2300 },
    ];
    const ps = paginar(palabras, { anchoMax: 2000, tam: 60, fuente: "Inter-900", mayusculas: true, separacion: 15, maxLineas: 2, maxPalabras: 9 });
    expect(ps.map((p) => p.lineas.flat())).toEqual([[0], [1], [2]]);
  });
});
