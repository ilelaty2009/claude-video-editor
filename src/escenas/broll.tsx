// B-roll: fotos o videos de apoyo con movimiento Ken Burns y crédito de licencia.
import React from "react";
import { AbsoluteFill, Img, interpolate, OffthreadVideo, staticFile } from "remotion";
import { clamp, curvas, useConfigDiseno, useCuadro } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { Fondo, Titular, useK } from "./base";
import type { Escena } from "./tipos";

// ---------- B-ROLL (fotos o videos de apoyo, como los editores pro) ----------
const esVideo = (a: string) => /\.(mp4|mov|webm|m4v)$/i.test(a);
export const EscenaBroll: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { durationInFrames, fpsReal } = useConfigDiseno();
  const k = useK();
  if (!e.archivo) return null;
  const t = interpolate(frame, [0, durationInFrames], [0, 1], { ...clamp, easing: curvas.camara });
  // "Ken Burns": la foto nunca se queda quieta
  const efecto = e.efecto ?? "acercar";
  const escala = efecto === "alejar" ? interpolate(t, [0, 1], [1.18, 1.04]) : efecto === "paneo" ? 1.15 : interpolate(t, [0, 1], [1.04, 1.18]);
  const x = efecto === "paneo" ? interpolate(t, [0, 1], [-4, 4]) : 0;
  const src = staticFile(e.archivo);
  const medio = (estilo: React.CSSProperties) =>
    esVideo(e.archivo!) ? (
      <OffthreadVideo src={src} muted trimBefore={Math.round((e.desdeSeg ?? 0) * fpsReal)} style={estilo} />
    ) : (
      <Img src={src} style={estilo} />
    );
  const cubrir: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover" };
  const tieneTexto = (e.lineas && e.lineas.length) || e.arriba;
  return (
    <Fondo entrada={e.entrada}>
      <AbsoluteFill style={{ transform: `scale(${escala}) translateX(${x}%)` }}>
        {e.completo ? (
          <>
            <AbsoluteFill style={{ filter: "blur(40px) brightness(0.55)", transform: "scale(1.2)" }}>{medio(cubrir)}</AbsoluteFill>
            <AbsoluteFill>{medio({ width: "100%", height: "100%", objectFit: "contain" })}</AbsoluteFill>
          </>
        ) : (
          medio(cubrir)
        )}
      </AbsoluteFill>
      {tieneTexto ? (
        <>
          <AbsoluteFill style={{ background: "linear-gradient(to top, rgba(5,7,16,0.75) 0%, rgba(5,7,16,0.15) 45%, transparent 65%)" }} />
          <Titular e={{ ...e, lado: e.lado ?? "izq", vertical: e.vertical ?? "abajo" }} ancho={1100} />
        </>
      ) : null}
      {e.credito ? (
        <div
          style={{
            position: "absolute",
            right: 24 * k,
            top: 20 * k,
            fontFamily: fuenteEscenas,
            fontWeight: 600,
            fontSize: 18 * k,
            color: "rgba(255,255,255,0.75)",
            background: "rgba(0,0,0,0.35)",
            padding: `${4 * k}px ${10 * k}px`,
            borderRadius: 6 * k,
          }}
        >
          {e.credito}
        </div>
      ) : null}
    </Fondo>
  );
};
