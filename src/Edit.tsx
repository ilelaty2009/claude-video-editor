import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Palabra, Subtitulos, useArribaSubtitulos } from "./Subtitulos";
import { Cierre, colores, DestelloLuz, Escena, Escenas, estadoVideo, focoEn } from "./escenas";
import { Titulo } from "./Titulo";
import { BarraProgreso, Capitulos, EmojiPops, FlashCortes, escalaPunch } from "./Efectos";
import { estilo } from "./estilo";
import { aReal, curvas, FPS_DISENO, useCuadro } from "./tiempo";
import { rectSeguro, Zona } from "./formatos";
import type { NombreEstiloSub } from "./subtitulos/estilos";

export type Segmento = { trimBefore: number; durationInFrames: number; from: number };

export type EditData = {
  video: string;
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  segments: Segmento[];
  captions: Palabra[];
  titulo?: string;
  encuadre?: "recorte" | "relleno" | "completo";
  formato?: "tv" | "reel" | "cuadrado" | "retrato";
  zonaSegura?: Zona; // márgenes donde el texto no queda tapado (editor.config.json)
  subtitulos?: NombreEstiloSub; // tiktok | cine | caja | resaltado
  capitulos?: { desdeMs: number; texto: string }[];
  sfx?: boolean;
  barraProgreso?: boolean;
  look?: "tiktok" | "cine";
  escenas?: Escena[];
  foco?: { x: number; y: number }; // punto al que apuntan los zooms (la cara), 0–1
  focoRuta?: { f: number; x: number; y: number }[]; // la cara a lo largo del video (seguimiento de cara)
  gancho?: { hastaFrame: number }; // "cold open": adelanto al inicio; aquí empieza el video normal
  cierre?: { desdeFrame: number; titulo: string; subtitulo?: string; linea?: string }; // tarjeta final
  // efectos de sonido al cuadro exacto (los arma scripts/sonidos.py)
  cues?: { f: number; archivo: string; recorte: number; vol: number }[];
  musica?: { archivo: string; volumen?: number; volumenHablando?: number };
};

// Música de fondo que baja sola cuando alguien habla ("ducking").
const Musica: React.FC<{ m: NonNullable<EditData["musica"]>; captions: Palabra[]; total: number; fps: number }> = ({ m, captions, total, fps }) => {
  const hablando = React.useMemo(() => {
    const a = new Float32Array(total + 1);
    for (const c of captions) {
      const i0 = Math.max(0, Math.floor(((c.startMs - 150) / 1000) * fps));
      const i1 = Math.min(total, Math.ceil(((c.endMs + 250) / 1000) * fps));
      for (let i = i0; i <= i1; i++) a[i] = 1;
    }
    // suavizado (~0.3 s) para que el volumen no salte
    const r = Math.round(fps * 0.3);
    const b = new Float32Array(total + 1);
    let suma = 0;
    for (let i = 0; i <= total + r; i++) {
      if (i <= total) suma += a[i];
      if (i - 2 * r - 1 >= 0) suma -= a[i - 2 * r - 1];
      const j = i - r;
      if (j >= 0 && j <= total) b[j] = suma / (2 * r + 1);
    }
    return b;
  }, [captions, total, fps]);
  const alto = m.volumen ?? 0.22;
  const bajo = m.volumenHablando ?? 0.07;
  return (
    <Audio
      src={staticFile(m.archivo)}
      loop
      volume={(f) => {
        const h = hablando[Math.min(f, total)] ?? 0;
        const v = alto + (bajo - alto) * h;
        const fade = interpolate(f, [0, fps, total - fps * 1.5, total], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return v * fade;
      }}
    />
  );
};

const Clip: React.FC<{ seg: Segmento; index: number; video: string; origen: string }> = ({ seg, index, video, origen }) => {
  const frame = useCuadro(); // tiempo dentro de este clip, en cuadros de diseño
  const { fps } = useVideoConfig();
  const zoomBase = estilo.zoomEnCortes && index % 2 === 1 ? estilo.zoomMaximo : 1;
  // pequeño empuje al empezar cada clip
  const empuje = interpolate(frame, [0, 6], [1.02, 1], {
    extrapolateRight: "clamp",
    easing: curvas.entra,
  });
  const f = aReal(estilo.fundidoAudioFrames, fps); // el volumen se calcula en cuadros reales
  const d = seg.durationInFrames;

  return (
    <AbsoluteFill style={{ transform: `scale(${zoomBase * empuje})`, transformOrigin: origen }}>
      <OffthreadVideo
        src={staticFile(video)}
        trimBefore={seg.trimBefore}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
        volume={(fr) =>
          f > 0
            ? interpolate(fr, [0, f, d - f, d], [0, 1, 1, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })
            : 1
        }
      />
    </AbsoluteFill>
  );
};

export const Edit: React.FC<{ data: EditData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const cuadro = (frame * FPS_DISENO) / fps; // tiempo en cuadros de diseño (ver src/tiempo.ts)
  const cine = data.look === "cine";
  const escenas = data.escenas ?? [];
  const foco = focoEn(frame, data);
  const origen = `${foco.x * 100}% ${foco.y * 100}%`;
  const ev = estadoVideo(
    cuadro,
    FPS_DISENO,
    escenas.map((e) => (e.tipo === "zoom" ? { ...e, x: e.x ?? foco.x, y: e.y ?? foco.y } : e)),
    width,
    height,
  );
  const relleno = data.encuadre === "relleno";
  const tv = data.width > data.height; // formato TV / proyector (16:9)
  const seguro = rectSeguro(width, height, data.zonaSegura);
  const estiloSub: NombreEstiloSub = data.subtitulos ?? (cine ? "cine" : "tiktok");
  const arribaSub = useArribaSubtitulos(estiloSub, data.zonaSegura, data.encuadre);
  const topCapitulo = seguro.y + (relleno && !tv ? 20 : 0);
  const topTitulo = tv ? seguro.y + 5 : seguro.y - 10;
  const punch = escalaPunch(cuadro, FPS_DISENO, data.captions);
  const sfx = Boolean(data.sfx);

  return (
    <AbsoluteFill style={{ background: escenas.length ? colores.fondo : "black" }}>
      {/* Video con corrección de color, zoom de golpe, y (con escenas) miniatura o acercamiento de cámara */}
      <AbsoluteFill
        style={{
          transform: `translate(${ev.x}px, ${ev.y}px) scale(${ev.escala})`,
          borderRadius: ev.radio / Math.max(ev.escala, 0.01),
          overflow: "hidden",
          boxShadow: ev.mini > 0 ? `0 40px 90px rgba(0,0,0,${0.6 * ev.mini})` : undefined,
        }}
      >
        <AbsoluteFill style={{ transform: `scale(${punch})`, transformOrigin: origen, filter: cine ? estilo.cine.filtroColor : estilo.filtroColor }}>
          {data.segments.map((seg, i) => (
            <Sequence key={i} from={seg.from} durationInFrames={seg.durationInFrames}>
              <Clip seg={seg} index={i} video={data.video} origen={origen} />
            </Sequence>
          ))}
        </AbsoluteFill>
        {estilo.vineta ? (
          <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.45) 100%)" }} />
        ) : null}
      </AbsoluteFill>
      {cine ? null : <FlashCortes inicios={data.segments.map((s) => s.from)} />}

      <Escenas escenas={escenas} sfx={sfx} />

      {cine ? null : <EmojiPops captions={data.captions} posicion={arribaSub} sfx={sfx} />}
      <Subtitulos captions={data.captions} estilo={estiloSub} zona={data.zonaSegura} encuadre={data.encuadre} />
      <Capitulos capitulos={data.capitulos ?? []} top={topCapitulo} izquierda={seguro.x} sfx={sfx} />

      {data.gancho ? (
        // transición del adelanto al inicio real: destello de luz + whoosh
        <Sequence from={Math.max(0, data.gancho.hastaFrame - aReal(10, fps))} durationInFrames={aReal(22, fps)}>
          <DestelloLuz duracion={22} />
        </Sequence>
      ) : null}
      {data.titulo ? (
        <Sequence from={data.gancho?.hastaFrame ?? 0} durationInFrames={Math.round(estilo.duracionTituloSeg * fps)}>
          <Titulo texto={data.titulo} top={topTitulo} />
        </Sequence>
      ) : null}
      {data.cierre ? (
        <Sequence from={data.cierre.desdeFrame}>
          <Cierre titulo={data.cierre.titulo} subtitulo={data.cierre.subtitulo} linea={data.cierre.linea} sfx={sfx} />
        </Sequence>
      ) : null}
      {data.barraProgreso !== false ? <BarraProgreso /> : null}
      {sfx
        ? (data.cues ?? []).map((c, i) => (
            <Sequence key={`cue-${i}`} from={c.f} durationInFrames={Math.round(data.fps * 3.2)} layout="none">
              <Audio src={staticFile(c.archivo)} volume={c.vol} trimBefore={c.recorte || undefined} />
            </Sequence>
          ))
        : null}
      {data.musica ? <Musica m={data.musica} captions={data.captions} total={data.durationInFrames} fps={data.fps} /> : null}
    </AbsoluteFill>
  );
};
