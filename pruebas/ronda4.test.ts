// Ronda 4: persona recortada (títulos detrás de la cabeza), cámara de grabaciones de pantalla, marca y estilos nuevos.
import { describe, expect, it } from "vitest";
import config from "../editor.config.json";
import marcaJson from "../brand/marca.json";
import { camaraPantalla, rectsDividida, tramosPersona } from "../src/escenas/camara";
import { familiaSegura, fuentesDisponibles } from "../src/marca";
import { estilosSub } from "../src/subtitulos/estilos";
import { ubicar } from "../src/subtitulos/ubicacion";

describe("persona recortada", () => {
  const personas = [{ archivo: "persona/a.webm", desde: 3.0, hasta: 8.0 }];
  it("muestra la persona solo donde la ventana y el segmento se cruzan, con el recorte correcto", () => {
    // segmento que empieza en el segundo 4 del video (cuadro 240) y va al cuadro 100 del video editado
    const seg = { trimBefore: 240, durationInFrames: 120, from: 100 };
    const t = tramosPersona(seg, [{ a: 130, b: 400 }], personas, 60);
    expect(t).toHaveLength(1);
    expect(t[0].desde).toBe(30); // 130 - 100
    expect(t[0].hasta).toBe(120); // hasta el final del segmento
    // el cuadro 130 del editado = segundo 4.5 del video; la pieza empieza en 3.0 -> recorte 1.5 s = 90 cuadros
    expect(t[0].trim).toBe(90);
  });
  it("no muestra nada si no hay pieza recortada para ese momento o no hay cruce", () => {
    const seg = { trimBefore: 600, durationInFrames: 60, from: 0 }; // segundo 10: fuera de la pieza
    expect(tramosPersona(seg, [{ a: 0, b: 60 }], personas, 60)).toHaveLength(0);
    expect(tramosPersona({ trimBefore: 240, durationInFrames: 60, from: 0 }, [{ a: 500, b: 600 }], personas, 60)).toHaveLength(0);
  });
});

describe("grabación de pantalla", () => {
  const zooms = [
    { t: 0, x: 0.5, y: 0.5, z: 1 },
    { t: 2, x: 0.3, y: 0.2, z: 2 },
  ];
  it("antes del cambio muestra todo; después se acerca con una transición suave", () => {
    expect(camaraPantalla(zooms, 1).z).toBe(1);
    const medio = camaraPantalla(zooms, 2.4);
    expect(medio.z).toBeGreaterThan(1);
    expect(medio.z).toBeLessThan(2);
    const fin = camaraPantalla(zooms, 3.5);
    expect(fin).toEqual({ x: 0.3, y: 0.2, z: 2 });
  });
  it("sin recorrido se queda en vista completa", () => {
    expect(camaraPantalla([], 5)).toEqual({ x: 0.5, y: 0.5, z: 1 });
  });
});

describe("marca y estilos", () => {
  it("la marca tiene los colores y fuentes que usa el editor, y las fuentes existen", () => {
    for (const c of ["azul", "amarillo", "rojo", "verde"] as const) expect(marcaJson.colores[c]).toMatch(/^#[0-9A-Fa-f]{6}$/);
    expect(marcaJson.colores.fondo.length).toBeGreaterThanOrEqual(1);
    expect(fuentesDisponibles[marcaJson.fuentes.escenas]).toBeTruthy();
    expect(fuentesDisponibles[marcaJson.fuentes.subtitulos]).toBeTruthy();
  });
  it("una fuente que no existe cae a la de respaldo (el render nunca se rompe)", () => {
    expect(familiaSegura("Fuente Que No Existe", "Inter")).toBe("Inter");
    expect(familiaSegura("Inter", "Montserrat")).toBe("Inter");
  });
  it("ninguna fuente del editor es itálica (regla anti 'AI slop')", () => {
    for (const lista of Object.values(fuentesDisponibles)) for (const f of lista) expect(f.archivo).not.toMatch(/italic/i);
  });
  it("el estilo «etiqueta» muestra una sola palabra y hay 5 estilos", () => {
    expect(Object.keys(estilosSub).sort()).toEqual(["caja", "cine", "etiqueta", "resaltado", "tiktok"]);
    expect(estilosSub.etiqueta.maxPalabras).toBe(1);
  });
  it("en vertical ningún estilo pone los subtítulos sobre la cara: van abajo salvo con pantalla dividida", () => {
    for (const [nombre, e] of Object.entries(estilosSub)) {
      for (const encuadre of ["recorte", "relleno"]) {
        const u = ubicar(e, 1080, 1920, config.formatos.reel.zonaSegura, encuadre);
        expect(u.y / 1920, `${nombre} ${encuadre}`).toBeGreaterThanOrEqual(0.66);
      }
    }
    expect(estilosSub.etiqueta.centroDividida).toBeLessThan(0.5); // con pantalla dividida sí va a la unión
  });
  it("la cara en círculo queda arriba y dentro de la zona segura a los lados", () => {
    for (const f of Object.values(config.formatos)) {
      const { persona } = rectsDividida("pip", f.ancho, f.alto);
      expect(persona.x).toBeGreaterThanOrEqual(f.ancho * f.zonaSegura.izquierda);
      expect(persona.y + persona.h).toBeLessThan(f.alto * 0.5);
    }
  });
});
