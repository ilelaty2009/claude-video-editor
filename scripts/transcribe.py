"""Transcribe un video palabra por palabra con faster-whisper (corre gratis en tu Mac).

Uso: python scripts/transcribe.py <video> <salida.json> [--modelo small] [--idioma es]
Salida: {"language": "es", "duration": 20.4, "words": [{"text", "start", "end", "prob"}]}
"""
import argparse
import json
import subprocess
import sys

import numpy as np

from faster_whisper import WhisperModel


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--modelo", default="small", help="tiny, base, small, medium, large-v3")
    ap.add_argument("--idioma", default="es", help="es, en, o 'auto'")
    ap.add_argument("--pistas", default="", help="nombres propios o palabras difíciles, ej: 'Dar al-Islam, Ibn Khaldun'")
    args = ap.parse_args()

    # Sacamos el audio con ffmpeg (16 kHz mono) para no depender de PyAV.
    pcm = subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", args.video, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
        check=True,
        capture_output=True,
    ).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0

    model = WhisperModel(args.modelo, device="cpu", compute_type="int8")
    lang = None if args.idioma == "auto" else args.idioma
    segments, info = model.transcribe(
        audio,
        language=lang,
        word_timestamps=True,
        beam_size=5,
        condition_on_previous_text=False,
        initial_prompt=args.pistas or None,
        hotwords=args.pistas or None,
    )

    words = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if not text:
                continue
            words.append(
                {"text": text, "start": round(w.start, 3), "end": round(w.end, 3), "prob": round(w.probability, 3)}
            )
        print(f"  [{seg.start:6.1f}s] {seg.text.strip()}", file=sys.stderr)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"language": info.language, "duration": info.duration, "words": words}, f, ensure_ascii=False, indent=1)
    print(f"OK: {len(words)} palabras -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
