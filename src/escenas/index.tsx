// ESCENAS ANIMADAS (estilo "motion graphics"). Se piden en trabajo/X_extras.json -> "escenas" (ver CLAUDE.md).
// plan_edit.py pasa los tiempos del video original al editado (desdeMs / hastaMs / enMs).
// Para agregar un tipo nuevo: crea el componente en el archivo que corresponda, agrégalo a `componentes` y a
// TipoEscena (tipos.ts), y documéntalo en la tabla de CLAUDE.md.
import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { EscenaTitular } from "./base";
import { EscenaBroll } from "./broll";
import { EscenaEngranajes, EscenaIconos, EscenaTarjetas } from "./graficos";
import { EscenaLineaTiempo, EscenaLista } from "./listas";
import { EscenaChat, EscenaCita, EscenaMiniatura, EscenaNombre, EscenaNumero } from "./texto";
import type { Escena, TipoEscena } from "./tipos";

export { Cierre } from "./cierre";
export { colores, DestelloLuz } from "./base";
export { estadoVideo, focoEn } from "./camara";
export type { Escena } from "./tipos";

const ms2fReal = (ms: number, fps: number) => Math.round((ms / 1000) * fps);


const componentes: Record<Exclude<TipoEscena, "zoom">, React.FC<{ e: Escena }>> = {
  titular: ({ e }) => <EscenaTitular e={e} />,
  chat: ({ e }) => <EscenaChat e={e} />,
  miniatura: ({ e }) => <EscenaMiniatura e={e} />,
  engranajes: ({ e }) => <EscenaEngranajes e={e} />,
  tarjetas: ({ e }) => <EscenaTarjetas e={e} />,
  iconos: ({ e }) => <EscenaIconos e={e} />,
  nombre: ({ e }) => <EscenaNombre e={e} />,
  cita: ({ e }) => <EscenaCita e={e} />,
  numero: ({ e }) => <EscenaNumero e={e} />,
  lista: ({ e }) => <EscenaLista e={e} />,
  linea_tiempo: ({ e }) => <EscenaLineaTiempo e={e} />,
  broll: ({ e }) => <EscenaBroll e={e} />,
};

// ---------- DISEÑO DE SONIDO ----------
// Los sonidos de las escenas ya NO se ponen aquí: scripts/sonidos.py arma la lista de "cues" (al cuadro exacto,
// alineados por su golpe, con sonidos reales de Openverse cuando hay) y Edit.tsx la toca con <Cues>.

// Todas las escenas que van ENCIMA del video (debajo de los subtítulos).
export const Escenas: React.FC<{ escenas: Escena[]; sfx: boolean }> = ({ escenas, sfx }) => {
  const { fps } = useVideoConfig(); // fps REAL: aquí se ubican las escenas en el video
  return (
    <>
      {escenas.map((e, i) => {
        if (e.tipo === "zoom") return null;
        const from = ms2fReal(e.desdeMs, fps);
        const dur = Math.max(Math.round(fps * 0.27), ms2fReal(e.hastaMs, fps) - from);
        const Comp = componentes[e.tipo as Exclude<TipoEscena, "zoom">];
        if (!Comp) return null; // tipo desconocido: se ignora en vez de romper el render
        return (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <AbsoluteFill>
              <Comp e={e} />
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </>
  );
};
