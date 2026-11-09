// Piezas compartidas por todas las escenas: colores, fondo con transiciones, titular, destello de luz e íconos.
import React from "react";
import { AbsoluteFill, Easing, interpolate, spring } from "remotion";
import { clamp, curvas, salida, salidaEscalonada, useConfigDiseno, useCuadro } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { anchoTexto } from "../subtitulos/disposicion";
import type { Escena } from "./tipos";

export const colores = {
  fondo: "radial-gradient(ellipse at 50% 35%, #1d2447 0%, #0d1024 60%, #07080f 100%)",
  azul: "#5CC8FF",
  amarillo: "#FFC94D",
  rojo: "#FF3B5C",
  verde: "#2ED47A",
  blanco: "#FFFFFF",
};

export const ms2f = (ms: number, fps: number) => Math.round((ms / 1000) * fps);

// Escala de diseño: todo está pensado para 1920x1080 (TV). En reel se achica.
export const useK = () => {
  const { width, height } = useConfigDiseno();
  return width >= height ? width / 1920 : width / 1150;
};

// Entrada/salida de una escena de pantalla completa (fundido + leve zoom).
const useEntradaSalida = () => {
  const frame = useCuadro();
  const { durationInFrames } = useConfigDiseno();
  const entra = interpolate(frame, [0, 7], [0, 1], { ...clamp, easing: curvas.entra });
  const sale = salida(frame, durationInFrames, 7);
  return { opacidad: Math.min(entra, sale), escala: interpolate(entra, [0, 1], [1.05, 1]), entra, sale };
};

// Destello de luz cálida (tipo "light leak") hecho con degradados: no necesita WebGL.
export const DestelloLuz: React.FC<{ duracion?: number }> = ({ duracion = 20 }) => {
  const frame = useCuadro();
  const { width } = useConfigDiseno();
  const t = interpolate(frame, [0, duracion], [0, 1], clamp);
  const fuerza = Math.sin(t * Math.PI); // sube y baja
  if (fuerza <= 0.001) return null;
  const x = interpolate(t, [0, 1], [-0.3, 1.2]) * width;
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", opacity: fuerza * 0.9, pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: x - width * 0.45,
          top: "-20%",
          width: width * 0.9,
          height: "140%",
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(255,190,110,0.95) 0%, rgba(255,110,80,0.55) 30%, rgba(255,60,120,0.25) 55%, transparent 72%)",
          filter: "blur(30px)",
          transform: "rotate(18deg)",
        }}
      />
      <AbsoluteFill style={{ background: `rgba(255,236,210,${0.25 * fuerza})` }} />
    </AbsoluteFill>
  );
};

type Entrada = Escena["entrada"];

export const Fondo: React.FC<{ children?: React.ReactNode; entrada?: Entrada }> = ({ children, entrada }) => {
  const frame = useCuadro();
  const { width } = useConfigDiseno();
  const { opacidad, escala, entra, sale } = useEntradaSalida();
  let transform = `scale(${escala})`;
  let filtro = "";
  let op = opacidad;
  if (entrada === "barrido") {
    // entra deslizándose desde la derecha con desenfoque de movimiento
    const s = interpolate(frame, [0, 9], [1, 0], { ...clamp, easing: Easing.out(Easing.cubic) });
    transform = `translateX(${s * width}px)`;
    filtro = `blur(${s * 18}px)`;
    op = sale;
  } else if (entrada === "zoom") {
    // zoom con desenfoque (como acercarse muy rápido)
    const s = interpolate(frame, [0, 10], [1, 0], { ...clamp, easing: Easing.out(Easing.cubic) });
    transform = `scale(${1 + s * 0.6})`;
    filtro = `blur(${s * 22}px)`;
    op = Math.min(sale, interpolate(entra, [0, 0.4], [0, 1], clamp));
  }
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <AbsoluteFill style={{ transform, filter: filtro || undefined }}>
        <AbsoluteFill style={{ background: colores.fondo }} />
        <AbsoluteFill style={entrada === "barrido" || entrada === "zoom" ? undefined : { transform: `scale(${escala})` }}>
          {children}
        </AbsoluteFill>
      </AbsoluteFill>
      {entrada === "luz" ? <DestelloLuz /> : null}
    </AbsoluteFill>
  );
};

// ---------- TITULAR ----------
export const Titular: React.FC<{ e: Escena; ancho?: number }> = ({ e, ancho }) => {
  const frame = useCuadro();
  const { fps, durationInFrames } = useConfigDiseno();
  const k = useK();
  const lado = e.lado ?? "izq";
  const lineas = e.lineas ?? [];
  const sale = salida(frame, durationInFrames, 7);
  const align = lado === "der" ? "flex-end" : lado === "centro" ? "center" : "flex-start";
  const vert = e.vertical ?? "arriba";
  const justify = vert === "centro" ? "center" : vert === "abajo" ? "flex-end" : "flex-start";
  const kick = spring({ frame, fps, config: { damping: 18, stiffness: 170 } });
  // las líneas grandes se achican si el texto es largo
  // (medido con el ancho real de cada letra de Inter Black, para que nunca se salga)
  const largo = Math.max(1, ...lineas.map((l) => anchoTexto(l.texto.toLocaleUpperCase("es"), "Inter-900", 1)));
  const tam = Math.min(120, ((ancho ?? 820) * 0.96) / largo) * k;
  return (
    <AbsoluteFill
      style={{
        padding: `${130 * k}px ${110 * k}px ${210 * k}px`,
        justifyContent: justify,
        alignItems: align,
        pointerEvents: "none",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: align, maxWidth: (ancho ?? 900) * k }}>
        {e.arriba ? (
          <div
            style={{
              fontFamily: fuenteEscenas,
              fontWeight: 700,
              fontSize: 40 * k,
              color: "rgba(255,255,255,0.88)",
              textTransform: "uppercase",
              letterSpacing: 1,
              marginBottom: 6 * k,
              opacity: Math.min(kick, sale),
              transform: `translateY(${(1 - kick) * 20 * k}px)`,
              textShadow: "0 4px 18px rgba(0,0,0,0.55)",
            }}
          >
            {e.arriba}
          </div>
        ) : null}
        {lineas.map((l, i) => {
          const inicio = l.enMs !== undefined ? ms2f(l.enMs - e.desdeMs, fps) : 4 + i * 8;
          const s = spring({ frame: frame - inicio, fps, config: { damping: 13, stiffness: 190, mass: 0.7 } });
          // salida escalonada: las líneas se van en el orden en que entraron y cada una baja un poco al irse
          const fuera = salidaEscalonada(frame, durationInFrames, i, lineas.length, 2, 7);
          return (
            <div
              key={i}
              style={{
                fontFamily: fuenteEscenas,
                fontWeight: 900,
                fontSize: tam,
                lineHeight: 0.98,
                letterSpacing: -1.5 * k,
                color: l.color ?? colores.blanco,
                textTransform: "uppercase",
                textAlign: lado === "der" ? "right" : lado === "centro" ? "center" : "left",
                opacity: Math.min(interpolate(s, [0, 0.4], [0, 1], clamp), fuera),
                transform: `translateY(${((1 - s) * 40 + (1 - fuera) * 24) * k}px) scale(${interpolate(s, [0, 1], [0.85, 1])})`,
                transformOrigin: lado === "der" ? "right center" : "left center",
                textShadow: "0 6px 26px rgba(0,0,0,0.55)",
              }}
            >
              {l.texto}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Sombra a un lado para que el titular se lea encima del video.
const SombraLado: React.FC<{ lado: "izq" | "der" | "centro" }> = ({ lado }) => {
  const { opacidad } = useEntradaSalida();
  const dir = lado === "der" ? "to left" : lado === "izq" ? "to right" : "to bottom";
  return (
    <AbsoluteFill
      style={{ opacity: opacidad, background: `linear-gradient(${dir}, rgba(5,7,16,0.78) 0%, rgba(5,7,16,0.35) 45%, transparent 70%)` }}
    />
  );
};

export const EscenaTitular: React.FC<{ e: Escena }> = ({ e }) =>
  e.fondo ? (
    <Fondo entrada={e.entrada}>
      <Titular e={{ ...e, vertical: e.vertical ?? "centro" }} ancho={1500} />
    </Fondo>
  ) : (
    <>
      <SombraLado lado={e.lado ?? "izq"} />
      <Titular e={e} />
    </>
  );

export const Icono: React.FC<{ tipo: "si" | "no" | "neutro"; tam: number }> = ({ tipo, tam }) => {
  const fondo = tipo === "si" ? colores.verde : tipo === "no" ? colores.rojo : "#8C93A8";
  return (
    <div
      style={{
        width: tam,
        height: tam,
        borderRadius: 999,
        background: fondo,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: `0 0 ${tam * 0.4}px ${fondo}88`,
      }}
    >
      <svg width={tam * 0.55} height={tam * 0.55} viewBox="0 0 24 24">
        {tipo === "si" ? (
          <path d="M4 12.5l5 5L20 6.5" stroke="white" strokeWidth={3.6} fill="none" strokeLinecap="round" strokeLinejoin="round" />
        ) : tipo === "no" ? (
          <path d="M6 6l12 12M18 6L6 18" stroke="white" strokeWidth={3.6} fill="none" strokeLinecap="round" />
        ) : (
          <text x="12" y="18" textAnchor="middle" fontSize="18" fontWeight="900" fill="white" fontFamily="sans-serif">
            ?
          </text>
        )}
      </svg>
    </div>
  );
};
