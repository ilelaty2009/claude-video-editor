// Animaciones explicativas: tiempos de cada paso, proyección isométrica y eje de la gráfica.
import { describe, expect, it } from "vitest";
import { iso, pasoActual } from "../src/animaciones/comun";
import { techoBonito } from "../src/animaciones/GraficaLimpia";

const data = {
  tipo: "minimal" as const,
  width: 1080,
  height: 1920,
  fps: 60,
  durationInFrames: 600,
  pasos: [
    { texto: "uno", desdeMs: 0, hastaMs: 4000 },
    { texto: "dos", desdeMs: 4000, hastaMs: 10000 },
  ],
};

describe("animaciones", () => {
  it("sabe qué paso va y cuánto lleva (en cuadros de diseño a 30 fps)", () => {
    expect(pasoActual(data, 0).i).toBe(0);
    const p = pasoActual(data, 300); // segundo 5 a 60 fps
    expect(p.i).toBe(1);
    expect(p.local).toBeCloseTo(30, 5); // 1 s dentro del paso = 30 cuadros de diseño
    expect(p.dur).toBeCloseTo(180, 5);
    expect(pasoActual(data, 9999).i).toBe(1); // después del final se queda en el último
  });

  it("isométrico: subir (z) mueve hacia arriba y x e y se van en diagonal", () => {
    expect(iso(0, 0, 10).y).toBeLessThan(iso(0, 0, 0).y);
    expect(iso(10, 0, 0).x).toBeGreaterThan(0);
    expect(iso(0, 10, 0).x).toBeLessThan(0);
    expect(iso(10, 10, 0).x).toBeCloseTo(0, 6); // avanzar en x e y a la vez = bajar recto (ruta vertical del mapa)
  });

  it("el eje de la gráfica usa números redondos", () => {
    expect(techoBonito(63)).toBe(80);
    expect(techoBonito(940)).toBe(1000);
    expect(techoBonito(99385)).toBe(100000);
    expect(techoBonito(12)).toBe(12);
    expect(techoBonito(0)).toBe(1);
  });
});
