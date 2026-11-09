// Animación: todo dura lo mismo en segundos a 30 o 60 fps, nada es lineal, las salidas van escalonadas,
// y la cámara sigue la cara suavemente.
import { describe, expect, it } from "vitest";
import { aReal, entrada, FPS_DISENO, salida, salidaEscalonada } from "../src/tiempo";
import { estadoVideo, focoEn } from "../src/escenas/camara";

describe("tiempo", () => {
  it("los cuadros de diseño son a 30 fps y se pasan bien a 60", () => {
    expect(FPS_DISENO).toBe(30);
    expect(aReal(7, 60)).toBe(14);
    expect(aReal(7, 30)).toBe(7);
  });

  it("las entradas no son lineales: frenan al llegar (a mitad de camino ya van más de la mitad)", () => {
    expect(entrada(4, 8)).toBeGreaterThan(0.75);
    expect(entrada(0, 8)).toBe(0);
    expect(entrada(8, 8)).toBe(1);
  });

  it("las salidas arrancan suave y terminan justo al final", () => {
    expect(salida(100, 100)).toBe(0);
    expect(salida(93, 100, 7)).toBe(1);
    expect(salida(96.5, 100, 7)).toBeGreaterThan(0.5); // a mitad de la salida todavía se ve más de la mitad
  });

  it("salida escalonada: se van en el mismo orden en que entraron y el último termina justo al final", () => {
    const n = 3;
    const vals = [0, 1, 2].map((i) => salidaEscalonada(96, 100, i, n, 2, 7));
    expect(vals[0]).toBeLessThan(vals[1]);
    expect(vals[1]).toBeLessThan(vals[2]);
    expect(salidaEscalonada(100, 100, 2, n)).toBe(0);
    expect(salidaEscalonada(96, 100, 0, n)).toBe(0); // el primero ya se fue
  });
});

describe("cámara", () => {
  it("un zoom lento dura lo mismo en segundos sin importar el fps", () => {
    const zoom = [{ tipo: "zoom" as const, desdeMs: 1000, hastaMs: 4000, escala: 1.3 }];
    // estadoVideo recibe cuadros de diseño: el segundo 2.5 es el cuadro 75 a 30 fps
    const a = estadoVideo(75, 30, zoom, 1920, 1080).escala;
    expect(a).toBeGreaterThan(1.1);
    expect(a).toBeLessThan(1.3);
    expect(estadoVideo(20, 30, zoom, 1920, 1080).escala).toBe(1); // antes del zoom
  });

  it("el seguimiento de cara interpola entre puntos y no se sale del recorrido", () => {
    const data = { foco: { x: 0.5, y: 0.4 }, focoRuta: [{ f: 0, x: 0.4, y: 0.4 }, { f: 60, x: 0.6, y: 0.5 }] };
    const medio = focoEn(30, data);
    expect(medio.x).toBeCloseTo(0.5, 5);
    expect(focoEn(-5, data).x).toBe(0.4);
    expect(focoEn(500, data).x).toBe(0.6);
    expect(focoEn(10, data).x).toBeLessThan(0.4 + (0.2 * 10) / 60); // con curva: arranca suave
  });

  it("sin recorrido usa el foco fijo", () => {
    expect(focoEn(10, { foco: { x: 0.3, y: 0.2 } })).toEqual({ x: 0.3, y: 0.2 });
  });
});
