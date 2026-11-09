import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Palabra } from "./Subtitulos";
import { estilo } from "./estilo";
import { fontFamily } from "./fuentes";
import { aReal, curvas, salida, useConfigDiseno, useCuadro } from "./tiempo";

const ms2f = (ms: number, fps: number) => Math.round((ms / 1000) * fps);

// Zoom de golpe: devuelve la escala extra en este momento según las palabras con zoom.
// `frame` y `fps` en cuadros de diseño (ver src/tiempo.ts).
export const escalaPunch = (frame: number, fps: number, captions: Palabra[]): number => {
  let s = 1;
  for (const c of captions) {
    if (!c.zoom) continue;
    const ini = ms2f(c.startMs, fps);
    const fin = Math.max(ms2f(c.endMs, fps), ini + 8);
    if (frame < ini - 1 || frame > fin + 14) continue;
    const sube = interpolate(frame, [ini - 1, ini + 3], [1, estilo.zoomGolpe], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });
    const baja = interpolate(frame, [fin, fin + 14], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    });
    s = Math.max(s, 1 + (sube - 1) * baja);
  }
  return s;
};

// Emoji grande que rebota encima de los subtítulos.
const EmojiPop: React.FC<{ emoji: string; posicion: number }> = ({ emoji, posicion }) => {
  const frame = useCuadro();
  const { fps, durationInFrames } = useConfigDiseno();
  const s = spring({ frame, fps, config: { damping: 9, stiffness: 180, mass: 0.6 } });
  const sale = salida(frame, durationInFrames, 6);
  const flota = Math.sin(frame / 4) * 6;
  return (
    <AbsoluteFill style={{ alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: `${posicion * 100}%`,
          transform: `translateY(-100%) translateY(${-90 + flota}px) scale(${s * sale}) rotate(${(1 - s) * -25}deg)`,
          fontSize: 150,
          filter: "drop-shadow(0 10px 18px rgba(0,0,0,0.45))",
        }}
      >
        {emoji}
      </div>
    </AbsoluteFill>
  );
};

export const EmojiPops: React.FC<{ captions: Palabra[]; posicion: number; sfx: boolean }> = ({ captions, posicion, sfx }) => {
  const { fps } = useVideoConfig();
  return (
    <>
      {captions
        .filter((c) => c.emoji)
        .map((c, i, todos) => {
          const desde = ms2f(c.startMs, fps) - aReal(2, fps);
          const sig = todos[i + 1];
          // si el siguiente emoji llega pronto, este se va antes para que no se encimen
          const dur = Math.max(aReal(8, fps), Math.min(Math.round(fps * 1.1), sig ? ms2f(sig.startMs, fps) - aReal(2, fps) - desde : 99999));
          return (
          <Sequence key={i} from={desde} durationInFrames={dur} layout="none">
            <EmojiPop emoji={c.emoji as string} posicion={posicion} />
          </Sequence>
          );
        })}
    </>
  );
};

// Etiqueta de sección que entra desde la izquierda.
const Capitulo: React.FC<{ texto: string; top: number; izquierda: number }> = ({ texto, top, izquierda }) => {
  const frame = useCuadro();
  const { fps, durationInFrames } = useConfigDiseno();
  const entra = spring({ frame, fps, config: { damping: 14, stiffness: 160 } });
  const sale = interpolate(frame, [durationInFrames - 8, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: curvas.sale,
  });
  const x = interpolate(entra, [0, 1], [-700, 0]) - sale * 900;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top,
          left: izquierda,
          transform: `translateX(${x}px)`,
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "16px 30px 16px 22px",
          borderRadius: 999,
          background: "rgba(10,10,14,0.82)",
          border: `4px solid ${estilo.colorPalabraActiva}`,
          boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
          color: "white",
          fontFamily,
          fontWeight: 900,
          fontSize: 50,
          textTransform: "uppercase",
          letterSpacing: 1,
        }}
      >
        <span style={{ width: 18, height: 18, borderRadius: 9, background: estilo.colorPalabraActiva }} />
        {texto}
      </div>
    </AbsoluteFill>
  );
};

export const Capitulos: React.FC<{ capitulos: { desdeMs: number; texto: string }[]; top: number; izquierda: number; sfx: boolean }> = ({
  capitulos,
  top,
  izquierda,
}) => {
  const { fps } = useVideoConfig();
  return (
    <>
      {capitulos.map((c, i) => (
        <Sequence key={i} from={ms2f(c.desdeMs, fps)} durationInFrames={Math.round(fps * 2.8)} layout="none">
          <Capitulo texto={c.texto} top={top} izquierda={izquierda} />
        </Sequence>
      ))}
    </>
  );
};

export const BarraProgreso: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 12, background: "rgba(255,255,255,0.18)" }} />
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          height: 12,
          width: `${(frame / Math.max(1, durationInFrames - 1)) * 100}%`,
          background: estilo.colorPalabraActiva,
          boxShadow: `0 0 16px ${estilo.colorPalabraActiva}`,
        }}
      />
    </AbsoluteFill>
  );
};

// Destello blanco muy corto en cada corte (transición tipo "flash").
export const FlashCortes: React.FC<{ inicios: number[] }> = ({ inicios }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const largo = aReal(4, fps); // dura lo mismo en segundos a 30 o a 60 fps
  let o = 0;
  for (const f of inicios) {
    if (f === 0) continue;
    if (frame >= f && frame < f + largo) o = Math.max(o, interpolate(frame, [f, f + largo], [0.22, 0], { easing: curvas.entra }));
  }
  return o > 0 ? <AbsoluteFill style={{ background: "white", opacity: o }} /> : null;
};
