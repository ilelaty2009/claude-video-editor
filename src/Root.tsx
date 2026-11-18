import React from "react";
import { CalculateMetadataFunction, Composition, staticFile } from "remotion";
import { Edit, EditData } from "./Edit";
import { Portada, PortadaData, portadaVacia } from "./Portada";
import { Animacion, AnimacionData, animacionVacia } from "./animaciones";

const vacio: EditData = {
  video: "input.mp4",
  fps: 30,
  width: 1080,
  height: 1920,
  durationInFrames: 90,
  segments: [],
  captions: [],
};

// Lee public/edit.json (lo crea scripts/plan_edit.py) y ajusta duración y tamaño.
const calcular: CalculateMetadataFunction<{ data: EditData }> = async ({ props }) => {
  // Un plan pasado con --props (lo usa el Brand Lab para hacer muchas muestras con un solo bundle) manda.
  if (props.data && props.data.segments.length) {
    const d = props.data;
    return { durationInFrames: Math.max(1, d.durationInFrames), fps: d.fps, width: d.width, height: d.height, props: { data: d } };
  }
  // Si todavía no se ha editado ningún video, no hay edit.json: usamos valores vacíos.
  let data = vacio;
  try {
    const res = await fetch(staticFile("edit.json"));
    if (res.ok) data = (await res.json()) as EditData;
  } catch {
    data = vacio;
  }
  return {
    durationInFrames: Math.max(1, data.durationInFrames),
    fps: data.fps,
    width: data.width,
    height: data.height,
    props: { data },
  };
};

// Lee public/portada.json (lo crea scripts/portada.py).
const calcularPortada: CalculateMetadataFunction<{ data: PortadaData }> = async () => {
  let data = portadaVacia;
  try {
    const res = await fetch(staticFile("portada.json"));
    if (res.ok) data = (await res.json()) as PortadaData;
  } catch {
    data = portadaVacia;
  }
  return { width: data.ancho, height: data.alto, props: { data } };
};

// Lee public/animacion.json (lo crea scripts/animar.py).
const calcularAnimacion: CalculateMetadataFunction<{ data: AnimacionData }> = async () => {
  let data = animacionVacia;
  try {
    const res = await fetch(staticFile("animacion.json"));
    if (res.ok) data = (await res.json()) as AnimacionData;
  } catch {
    data = animacionVacia;
  }
  return { durationInFrames: Math.max(1, data.durationInFrames), fps: data.fps, width: data.width, height: data.height, props: { data } };
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
    <Composition
      id="Portada"
      component={Portada}
      durationInFrames={1}
      fps={30}
      width={1280}
      height={720}
      defaultProps={{ data: portadaVacia }}
      calculateMetadata={calcularPortada}
    />
    <Composition
      id="Animacion"
      component={Animacion}
      durationInFrames={animacionVacia.durationInFrames}
      fps={animacionVacia.fps}
      width={animacionVacia.width}
      height={animacionVacia.height}
      defaultProps={{ data: animacionVacia }}
      calculateMetadata={calcularAnimacion}
    />
    <Composition
      id="Edit"
      component={Edit}
      durationInFrames={vacio.durationInFrames}
      fps={vacio.fps}
      width={vacio.width}
      height={vacio.height}
      defaultProps={{ data: vacio }}
      calculateMetadata={calcular}
    />
    </>
  );
};
