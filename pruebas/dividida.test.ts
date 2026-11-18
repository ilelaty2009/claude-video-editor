// Pantalla dividida: la persona llena su mitad SIN bordes vacíos, con la cara lo más centrada posible,
// y el panel de contenido y la persona no se tapan entre sí.
import { describe, expect, it } from "vitest";
import { encuadrarEn, estadoDividida, rectsDividida } from "../src/escenas/camara";

const cubre = (R: { w: number; h: number }, A: { x: number; y: number; w: number; h: number }, enc: { escala: number; x: number; y: number }) => {
  // el área de la cámara, ya escalada y movida, debe tapar toda la región (0,0)-(R.w,R.h)
  const izq = A.x * enc.escala + enc.x;
  const arriba = A.y * enc.escala + enc.y;
  return izq <= 0.5 && arriba <= 0.5 && izq + A.w * enc.escala >= R.w - 0.5 && arriba + A.h * enc.escala >= R.h - 0.5;
};

describe("pantalla dividida", () => {
  const casos = [
    { nombre: "vertical con relleno (franja de cámara)", W: 1080, H: 1920, A: { x: 0, y: 347, w: 1080, h: 880 }, modo: "apilada" as const },
    { nombre: "vertical con recorte", W: 1080, H: 1920, A: { x: 0, y: 0, w: 1080, h: 1920 }, modo: "apilada" as const },
    { nombre: "TV lado a lado", W: 1920, H: 1080, A: { x: 0, y: 0, w: 1920, h: 1080 }, modo: "lado" as const },
    { nombre: "TV con video vertical (barras)", W: 1920, H: 1080, A: { x: 656, y: 0, w: 608, h: 1080 }, modo: "lado" as const },
    { nombre: "cara en círculo", W: 1080, H: 1920, A: { x: 0, y: 0, w: 1080, h: 1920 }, modo: "pip" as const },
  ];
  for (const c of casos) {
    for (const cara of [{ x: 0.5, y: 0.4 }, { x: 0.15, y: 0.2 }, { x: 0.9, y: 0.85 }]) {
      it(`${c.nombre}, cara en (${cara.x}, ${cara.y})`, () => {
        const { persona, panel } = rectsDividida(c.modo, c.W, c.H);
        const F = { x: c.A.x + cara.x * c.A.w, y: c.A.y + cara.y * c.A.h };
        const enc = encuadrarEn(persona, c.A, F);
        expect(cubre(persona, c.A, enc)).toBe(true); // sin bordes negros
        // dentro del cuadro
        for (const r of [persona, panel]) {
          expect(r.x).toBeGreaterThanOrEqual(0);
          expect(r.y).toBeGreaterThanOrEqual(0);
          expect(r.x + r.w).toBeLessThanOrEqual(c.W);
          expect(r.y + r.h).toBeLessThanOrEqual(c.H);
        }
        if (c.modo !== "pip") {
          // no se tapan: o uno está arriba del otro, o al lado
          const separados = panel.y + panel.h <= persona.y || persona.y + persona.h <= panel.y || panel.x + panel.w <= persona.x || persona.x + persona.w <= panel.x;
          expect(separados).toBe(true);
        }
      });
    }
  }

  it("con la cara al centro, queda centrada en su mitad", () => {
    const { persona } = rectsDividida("apilada", 1080, 1920);
    const A = { x: 0, y: 0, w: 1080, h: 1920 };
    const enc = encuadrarEn(persona, A, { x: 540, y: 900 });
    expect(540 * enc.escala + enc.x).toBeCloseTo(persona.w / 2, 0);
    expect(900 * enc.escala + enc.y).toBeCloseTo(persona.h / 2, 0);
  });

  it("solo está activa durante su escena", () => {
    const escenas = [{ tipo: "dividida" as const, desdeMs: 1000, hastaMs: 5000 }];
    expect(estadoDividida(10, 30, escenas).t).toBe(0);
    expect(estadoDividida(90, 30, escenas).t).toBeGreaterThan(0.9);
    expect(estadoDividida(200, 30, escenas).t).toBe(0);
  });
});
