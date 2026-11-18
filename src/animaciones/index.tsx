// Composición "Animacion": un video explicativo completo, hecho desde cero (sin grabar nada).
// La receta la escribe Claude (ver los comandos /minimalista, /palitos, /despiece, /mapa-ruta, /grafica)
// y scripts/animar.py la vuelve video con voz, música y audio masterizado.
import React from "react";
import { AbsoluteFill } from "remotion";
import { AnimacionData } from "./comun";
import { Despiece } from "./Despiece";
import { GraficaLimpia } from "./GraficaLimpia";
import { Mapa3D } from "./Mapa3D";
import { Minimal } from "./Minimal";
import { Palitos } from "./Palitos";

export type { AnimacionData } from "./comun";

export const animacionVacia: AnimacionData = {
  tipo: "minimal",
  width: 1080,
  height: 1920,
  fps: 60,
  durationInFrames: 120,
  pasos: [{ texto: "Escribe una receta en demo/animaciones/", desdeMs: 0, hastaMs: 2000, visual: "barras" }],
};

export const Animacion: React.FC<{ data: AnimacionData }> = ({ data }) => {
  switch (data.tipo) {
    case "palitos":
      return <Palitos data={data} />;
    case "despiece":
      return <Despiece data={data} />;
    case "mapa":
      return <Mapa3D data={data} />;
    case "grafica":
      return <GraficaLimpia data={data} />;
    case "minimal":
      return <Minimal data={data} />;
    default:
      return <AbsoluteFill style={{ background: "black" }} />;
  }
};
