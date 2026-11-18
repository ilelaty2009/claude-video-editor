// Escenas del reel "How to make your own AI video editor" y de la guía Claude × Remotion:
//  cinetica   frase a pantalla completa: cada palabra aparece EXACTO cuando se dice (las clave, de color)
//  diagrama   app → app → app: íconos con nombre unidos por flechas que se dibujan
//  ventana    ventana de una app con el texto que se escribe, checklist que se va marcando y barra de progreso
//  collage    2–4 fotos/videos en tarjetas que aparecen flotando encima del video
//  anotacion  círculo, flecha, subrayado o X dibujado "a mano" encima del video, con una etiqueta
import React from "react";
import { AbsoluteFill, Img, interpolate, OffthreadVideo, spring, staticFile } from "remotion";
import { clamp, curvas, salida, salidaEscalonada, useConfigDiseno, useCuadro } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { colores, Fondo, ms2f, useK } from "./base";
import type { Escena } from "./tipos";

const esVideo = (a: string) => /\.(mp4|mov|webm|m4v)$/i.test(a);

// ---------- FRASE CINÉTICA ----------
export const EscenaCinetica: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames, width, height } = useConfigDiseno();
  const k = useK();
  const palabras = e.palabras ?? [];
  const destacar = new Set((e.destacar ?? []).map((d) => d.toLocaleUpperCase("es")));
  const largo = palabras.reduce((s, p) => s + p.texto.length + 1, 0);
  const tam = Math.min(150, Math.max(70, (width * (height > width ? 2.6 : 1.9)) / Math.max(10, largo))) * k;
  return (
    <Fondo entrada={e.entrada}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: height > width ? "flex-start" : "center", padding: `${height > width ? height * 0.2 : 0}px ${110 * k}px 0` }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", columnGap: tam * 0.28, rowGap: tam * 0.05, maxWidth: width * 0.86 }}>
          {palabras.map((p, i) => {
            const inicio = p.enMs !== undefined ? ms2f(p.enMs - e.desdeMs, fps) : 4 + i * 5;
            const s = spring({ frame: frame - inicio, fps, config: { damping: 14, stiffness: 220, mass: 0.6 } });
            const fuera = salidaEscalonada(frame, durationInFrames, i, palabras.length, 1, 6);
            const clave = destacar.has(p.texto.replace(/[.,!?¿¡:;]/g, "").toLocaleUpperCase("es"));
            return (
              <span
                key={i}
                style={{
                  fontFamily: fuenteEscenas,
                  fontWeight: 900,
                  fontSize: tam,
                  lineHeight: 1.02,
                  letterSpacing: -1.5 * k,
                  textTransform: "uppercase",
                  color: clave ? e.lineas?.[0]?.color ?? colores.amarillo : "white",
                  opacity: Math.min(interpolate(s, [0, 0.35], [0, 1], clamp), fuera),
                  transform: `translateY(${(1 - s) * 30 * k}px) scale(${interpolate(s, [0, 1], [0.8, 1])})`,
                  display: "inline-block",
                  textShadow: "0 6px 26px rgba(0,0,0,0.5)",
                }}
              >
                {p.texto}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    </Fondo>
  );
};

// ---------- DIAGRAMA APP → APP ----------
export const EscenaDiagrama: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, width, height } = useConfigDiseno();
  const k = useK();
  const nodos = e.nodos ?? [];
  const n = Math.max(1, nodos.length);
  const vertical = height > width;
  const caja = (vertical ? 170 : 200) * k;
  const ancho = Math.min(0.72, 0.26 * (n - 1)); // con 2 elementos no quedan en las esquinas
  const pos = (i: number) =>
    vertical
      ? { x: width / 2, y: height * 0.2 + (i * (height * 0.36)) / Math.max(1, n - 1) } // arriba de los subtítulos
      : { x: width * (0.5 - ancho / 2) + (i * (width * ancho)) / Math.max(1, n - 1), y: height * 0.48 };
  const inicio = (i: number) => (nodos[i]?.enMs !== undefined ? ms2f(nodos[i].enMs! - e.desdeMs, fps) : 6 + i * 14);
  return (
    <Fondo entrada={e.entrada}>
      {e.titulo ? (
        <div style={{ position: "absolute", top: height * (vertical ? 0.1 : 0.12), width: "100%", textAlign: "center", fontFamily: fuenteEscenas, fontWeight: 900, fontSize: 56 * k, color: "white", textTransform: "uppercase" }}>{e.titulo}</div>
      ) : null}
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {nodos.slice(1).map((_, j) => {
          const a = pos(j);
          const b = pos(j + 1);
          const p = interpolate(frame, [inicio(j + 1) - 8, inicio(j + 1)], [0, 1], { ...clamp, easing: curvas.cambia });
          const d = vertical ? caja * 0.62 : caja * 0.62;
          const x1 = vertical ? a.x : a.x + d;
          const y1 = vertical ? a.y + d + 52 * k : a.y; // en vertical la flecha sale debajo del nombre
          const x2 = vertical ? b.x : b.x - d;
          const y2 = vertical ? b.y - d : b.y;
          const xp = x1 + (x2 - x1) * p;
          const yp = y1 + (y2 - y1) * p;
          const ang = Math.atan2(y2 - y1, x2 - x1);
          return (
            <g key={j} opacity={p > 0 ? 1 : 0}>
              <line x1={x1} y1={y1} x2={xp} y2={yp} stroke="rgba(255,255,255,0.85)" strokeWidth={6 * k} strokeLinecap="round" strokeDasharray={`${14 * k} ${12 * k}`} />
              {p > 0.95 ? <path d={`M${x2} ${y2} l${-22 * k * Math.cos(ang - 0.5)} ${-22 * k * Math.sin(ang - 0.5)} M${x2} ${y2} l${-22 * k * Math.cos(ang + 0.5)} ${-22 * k * Math.sin(ang + 0.5)}`} stroke="white" strokeWidth={6 * k} strokeLinecap="round" /> : null}
            </g>
          );
        })}
      </svg>
      {nodos.map((nd, i) => {
        const s = spring({ frame: frame - inicio(i), fps, config: { damping: 12, stiffness: 180 } });
        const q = pos(i);
        return (
          <div key={i} style={{ position: "absolute", left: q.x - caja / 2, top: q.y - caja / 2, width: caja, height: caja, opacity: interpolate(s, [0, 0.4], [0, 1], clamp), transform: `scale(${s})` }}>
            <div style={{ width: caja, height: caja, borderRadius: 30 * k, background: "rgba(255,255,255,0.1)", border: `${2 * k}px solid rgba(255,255,255,0.22)`, boxShadow: `0 ${18 * k}px ${40 * k}px rgba(0,0,0,0.4)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: caja * 0.48 }}>
              {nd.icono}
            </div>
            <div style={{ marginTop: 14 * k, width: caja * 1.6, marginLeft: -caja * 0.3, textAlign: "center", fontFamily: fuenteEscenas, fontWeight: 800, fontSize: 34 * k, color: "white" }}>{nd.texto}</div>
          </div>
        );
      })}
    </Fondo>
  );
};

// ---------- VENTANA DE APP CON CHECKLIST ----------
export const EscenaVentana: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames, width, height } = useConfigDiseno();
  const k = useK() * (height > width ? 1.3 : 1);
  const s = spring({ frame, fps, config: { damping: 16, stiffness: 160 } });
  const sale = salida(frame, durationInFrames, 7);
  const texto = e.texto ?? "";
  const finEscritura = Math.max(10, Math.min(durationInFrames * 0.45, texto.length * 0.9 + 6));
  const n = Math.round(interpolate(frame, [4, finEscritura], [0, texto.length], clamp));
  const items = e.items ?? [];
  const progreso = e.valor ? interpolate(frame, [finEscritura, durationInFrames * 0.92], [0, 1], { ...clamp, easing: curvas.cambia }) : 0;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: height > width ? "flex-start" : "center", paddingTop: height > width ? height * 0.14 : 0, opacity: sale }}>
      <div style={{ width: Math.min(width * 0.86, 860 * k), borderRadius: 18 * k, background: "#1E1F24", border: "1px solid rgba(255,255,255,0.08)", boxShadow: `0 ${30 * k}px ${80 * k}px rgba(0,0,0,0.55)`, overflow: "hidden", fontFamily: fuenteEscenas, transform: `translateY(${(1 - s) * 40 * k}px) scale(${0.94 + 0.06 * s})`, opacity: s }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9 * k, padding: `${14 * k}px ${18 * k}px`, background: "#2A2B31" }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => (
            <span key={c} style={{ width: 13 * k, height: 13 * k, borderRadius: 99, background: c }} />
          ))}
          <span style={{ marginLeft: 10 * k, color: "rgba(255,255,255,0.55)", fontWeight: 700, fontSize: 20 * k }}>{e.etiqueta ?? "Claude"}</span>
        </div>
        <div style={{ padding: `${22 * k}px ${26 * k}px` }}>
          {texto ? (
            <div style={{ background: "#2F3037", borderRadius: 12 * k, padding: `${14 * k}px ${18 * k}px`, color: "white", fontWeight: 600, fontSize: 28 * k, lineHeight: 1.35, whiteSpace: "pre-wrap", marginBottom: 18 * k }}>
              {texto.slice(0, n)}
              {n < texto.length ? <span style={{ color: colores.amarillo }}>|</span> : null}
            </div>
          ) : null}
          {items.map((it, i) => {
            const inicio = it.enMs !== undefined ? ms2f(it.enMs - e.desdeMs, fps) : finEscritura + 6 + i * 10;
            const c = spring({ frame: frame - inicio, fps, config: { damping: 11, stiffness: 220 } });
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12 * k, margin: `${8 * k}px 0`, opacity: interpolate(c, [0, 0.3], [0, 1], clamp), transform: `translateX(${(1 - c) * -20 * k}px)` }}>
                <span style={{ width: 28 * k, height: 28 * k, borderRadius: 99, background: colores.verde, color: "#08130c", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontSize: 18 * k, transform: `scale(${c})` }}>✓</span>
                <span style={{ color: "rgba(255,255,255,0.9)", fontWeight: 700, fontSize: 26 * k }}>{it.texto}</span>
              </div>
            );
          })}
          {e.valor ? (
            <div style={{ marginTop: 16 * k }}>
              <div style={{ color: "rgba(255,255,255,0.55)", fontWeight: 600, fontSize: 20 * k, marginBottom: 8 * k }}>
                {e.etiqueta2 ?? "Renderizando"} {Math.round(progreso * e.valor).toLocaleString("es-CO")} de {e.valor.toLocaleString("es-CO")}
              </div>
              <div style={{ height: 8 * k, borderRadius: 99, background: "rgba(255,255,255,0.12)" }}>
                <div style={{ height: "100%", width: `${progreso * 100}%`, borderRadius: 99, background: colores.rojo }} />
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- COLLAGE DE MINIATURAS ----------
export const EscenaCollage: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames, width, height, fpsReal } = useConfigDiseno();
  const k = useK();
  const archivos = (e.archivos ?? []).slice(0, 4);
  const n = archivos.length;
  const vertical = height > width;
  const w = (vertical ? width * 0.3 : width * 0.17) * (n <= 2 ? 1.3 : 1);
  const h = w * 1.35; // tarjetas 3:4 (caben bajo el banner y sobre los subtítulos)
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {archivos.map((a, i) => {
        const inicio = 4 + i * 6;
        const s = spring({ frame: frame - inicio, fps, config: { damping: 13, stiffness: 170 } });
        const fuera = salidaEscalonada(frame, durationInFrames, i, n, 2, 7);
        const x = width / 2 + (i - (n - 1) / 2) * w * 0.82;
        const y = height * (vertical ? 0.36 : 0.45) + Math.sin((frame + i * 20) / 25) * 6 * k;
        const giro = (i - (n - 1) / 2) * 5;
        return (
          <div key={i} style={{ position: "absolute", left: x - w / 2, top: y - h / 2, width: w, height: h, borderRadius: 16 * k, overflow: "hidden", border: `${5 * k}px solid white`, boxShadow: `0 ${20 * k}px ${50 * k}px rgba(0,0,0,0.5)`, opacity: Math.min(interpolate(s, [0, 0.3], [0, 1], clamp), fuera), transform: `translateY(${(1 - s) * 60 * k + (1 - fuera) * 30 * k}px) rotate(${giro * s}deg) scale(${0.85 + 0.15 * s})` }}>
            {esVideo(a) ? (
              <OffthreadVideo src={staticFile(a)} muted trimBefore={Math.round((e.desdeSeg ?? 0) * fpsReal)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : (
              <Img src={staticFile(a)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// ---------- ANOTACIÓN A MANO ----------
// Trazo "a mano": la línea tiembla un poquito (como un marcador) y se dibuja en 0,5 s.
const tembloroso = (pts: { x: number; y: number }[], semilla: number, fuerza: number) =>
  pts
    .map((p, i) => {
      const v = Math.sin((i + 1) * (semilla + 7.31) * 12.9898) * 43758.5;
      const r = (v - Math.floor(v) - 0.5) * fuerza;
      return `${i ? "L" : "M"}${(p.x + r).toFixed(1)} ${(p.y - r).toFixed(1)}`;
    })
    .join(" ");

export const EscenaAnotacion: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { durationInFrames, width, height } = useConfigDiseno();
  const k = useK();
  const forma = e.forma ?? "circulo";
  const cx = (e.x ?? 0.5) * width;
  const cy = (e.y ?? 0.5) * height;
  const rw = ((e.ancho ?? 0.22) * width) / 2;
  const rh = ((e.alto ?? 0.16) * height) / 2;
  const color = e.lineas?.[0]?.color ?? colores.amarillo;
  const p = interpolate(frame, [2, 16], [0, 1], { ...clamp, easing: curvas.cambia });
  const sale = salida(frame, durationInFrames, 7);
  let pts: { x: number; y: number }[] = [];
  if (forma === "circulo") {
    // un poco más de una vuelta, como cuando se encierra algo con marcador
    pts = Array.from({ length: 60 }, (_, i) => {
      const a = -Math.PI / 2 + (i / 59) * Math.PI * 2.15;
      return { x: cx + Math.cos(a) * rw * (1 + 0.04 * Math.sin(i / 3)), y: cy + Math.sin(a) * rh };
    });
  } else if (forma === "subrayado") {
    pts = Array.from({ length: 24 }, (_, i) => ({ x: cx - rw + (i / 23) * rw * 2, y: cy + rh + Math.sin(i / 2.5) * 3 * k }));
  } else if (forma === "x") {
    pts = [{ x: cx - rw, y: cy - rh }, { x: cx + rw, y: cy + rh }];
  } else {
    // flecha que apunta al punto (x, y) desde abajo a la izquierda
    pts = Array.from({ length: 20 }, (_, i) => {
      const t = i / 19;
      return { x: cx - rw * 2 + t * (rw * 2 - 20 * k), y: cy + rh * 2 - t * (rh * 2 - 20 * k) - Math.sin(t * Math.PI) * 40 * k };
    });
  }
  const d = tembloroso(pts, e.desdeMs, 4 * k);
  const largo = pts.reduce((s, q, i) => (i ? s + Math.hypot(q.x - pts[i - 1].x, q.y - pts[i - 1].y) : 0), 0);
  const punta = pts[pts.length - 1];
  const previo = pts[Math.max(0, pts.length - 3)];
  const ang = Math.atan2(punta.y - previo.y, punta.x - previo.x);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: sale }}>
      <svg width={width} height={height}>
        <path d={d} fill="none" stroke={color} strokeWidth={9 * k} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={largo * 1.1} strokeDashoffset={largo * 1.1 * (1 - p)} />
        {forma === "x" && p > 0.5 ? (
          <path d={tembloroso([{ x: cx + rw, y: cy - rh }, { x: cx - rw, y: cy + rh }], e.desdeMs + 3, 4 * k)} fill="none" stroke={color} strokeWidth={9 * k} strokeLinecap="round" opacity={interpolate(p, [0.5, 1], [0, 1])} />
        ) : null}
        {forma === "flecha" && p > 0.95 ? (
          <path d={`M${punta.x} ${punta.y} l${-30 * k * Math.cos(ang - 0.5)} ${-30 * k * Math.sin(ang - 0.5)} M${punta.x} ${punta.y} l${-30 * k * Math.cos(ang + 0.5)} ${-30 * k * Math.sin(ang + 0.5)}`} stroke={color} strokeWidth={9 * k} strokeLinecap="round" />
        ) : null}
      </svg>
      {e.texto ? (
        <div style={{ position: "absolute", left: forma === "flecha" ? cx - rw * 2 - 20 * k : cx - rw, top: forma === "flecha" ? cy + rh * 2 + 10 * k : cy - rh - 70 * k, fontFamily: fuenteEscenas, fontWeight: 800, fontSize: 40 * k, color, textShadow: "0 3px 12px rgba(0,0,0,0.7)", transform: "rotate(-3deg)", opacity: interpolate(p, [0.6, 1], [0, 1], clamp) }}>
          {e.texto}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
