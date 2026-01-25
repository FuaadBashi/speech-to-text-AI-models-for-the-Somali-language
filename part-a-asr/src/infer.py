#!/usr/bin/env python3
"""
src/infer.py

Manifest-driven Whisper inference for Part A verification.

Key behaviours:
- If you pass --manifest: transcribes EACH segment listed in verification_manifest.json
  (one line per segment), so hypothesis line-count matches GT line-count.
- If you pass --audio: transcribes a single audio file into one line.

This version also:
- Avoids HF pipeline() so you don't hit torchcodec/ffmpeg dylib issues on macOS.
- Silences the urllib3 LibreSSL advisory *before imports* when --quiet is used.
"""

# ---- IMPORTANT: silence warnings BEFORE importing transformers/requests ----
import os
import sys
import warnings

# We look for --quiet in argv early so we can suppress warnings that fire during imports.
_EARLY_QUIET = "--quiet" in sys.argv

if _EARLY_QUIET:
    # Silence the specific urllib3 LibreSSL advisory emitted at import time.
    warnings.filterwarnings(
        "ignore",
        message=r"urllib3 v2 only supports OpenSSL.*LibreSSL.*",
    )
    # Optional: hide Hugging Face download progress bars
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    # Hide some HF advisory warnings
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

# --------------------------------------------------------------------------

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import soundfile as sf
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from transformers.utils import logging as hf_logging


def configure_quiet_logging(quiet: bool) -> None:
    """
    quiet=True:
      - hides Transformers WARNING logs (including attention-mask advisory)
    """
    if quiet:
        hf_logging.set_verbosity_error()
    else:
        hf_logging.set_verbosity_warning()


TARGET_SR = 16000


# ----------------------------
# Text normalisation (clean.txt)
# ----------------------------
def normalize_basic(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_text(text: str) -> str:
    """
    Prefer the project's normaliser if present (src/text_normalize.py),
    otherwise fall back to a conservative normaliser.
    """
    try:
        from text_normalize import normalize_text as _norm  # type: ignore
        return _norm(text)
    except Exception:
        return normalize_basic(text)


# ----------------------------
# Audio helpers
# ----------------------------
def load_audio(path: str) -> Tuple[np.ndarray, int]:
    """Load audio using soundfile; downmix to mono float32."""
    audio, sr = sf.read(path, always_2d=False)
    if isinstance(audio, np.ndarray) and audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    audio = np.asarray(audio, dtype=np.float32)
    return audio, int(sr)


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def probe_audio_sr_channels(path: str) -> Optional[Tuple[int, int]]:
    """Return (sample_rate, channels) using ffprobe if available."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate,channels",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    try:
        p = _run(cmd)
        if p.returncode != 0:
            return None
        lines = [x.strip() for x in p.stdout.splitlines() if x.strip()]
        if len(lines) < 2:
            return None
        return int(lines[0]), int(lines[1])
    except FileNotFoundError:
        return None


def ensure_16k_mono(path: str, tmp_dir: Path) -> str:
    """
    Ensure the file is 16kHz mono WAV for Whisper.
    Uses ffmpeg for conversion when needed.
    """
    info = probe_audio_sr_channels(path)
    needs = True
    if info is not None:
        sr, ch = info
        needs = (sr != TARGET_SR) or (ch != 1)

    if not needs:
        return path

    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_path = tmp_dir / (Path(path).stem + "_16k.wav")

    cmd = ["ffmpeg", "-y", "-i", path, "-ac", "1", "-ar", str(TARGET_SR), str(out_path)]
    try:
        p = _run(cmd)
    except FileNotFoundError:
        # ffmpeg not found; fall back to original (may reduce quality if SR != 16k)
        return path

    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed converting {path}:\n{p.stderr}")

    return str(out_path)


# ----------------------------
# Whisper decoding helpers
# ----------------------------
def pick_device(device_arg: Optional[str]) -> str:
    if device_arg:
        return device_arg
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def build_decoder_prompt(
    processor: WhisperProcessor,
    model: WhisperForConditionalGeneration,
    language: Optional[str],
    task: str,
    device: str,
) -> Optional[Tuple[torch.Tensor, torch.Tensor]]:
    """
    Build (decoder_input_ids, decoder_attention_mask) that forces Whisper language/task.
    """
    lang = (language or "").strip().lower()
    if lang in {"so", "so_so"}:
        lang = "somali"
    if not lang:
        return None

    try:
        forced = processor.get_decoder_prompt_ids(language=lang, task=task)
        forced = sorted(forced, key=lambda x: x[0])
        prompt_token_ids = [tok_id for _, tok_id in forced]
    except Exception:
        return None

    if not prompt_token_ids:
        return None

    start_id = getattr(model.config, "decoder_start_token_id", None)
    if start_id is None:
        return None

    decoder_input_ids = torch.tensor(
        [[int(start_id)] + [int(t) for t in prompt_token_ids]],
        dtype=torch.long,
        device=device,
    )
    decoder_attention_mask = torch.ones_like(decoder_input_ids, dtype=torch.long, device=device)
    return decoder_input_ids, decoder_attention_mask


def transcribe_one(
    processor: WhisperProcessor,
    model: WhisperForConditionalGeneration,
    audio_path: str,
    device: str,
    decoder_prompt: Optional[Tuple[torch.Tensor, torch.Tensor]],
    max_new_tokens: int,
) -> str:
    audio, sr = load_audio(audio_path)
    inputs = processor(audio, sampling_rate=sr, return_tensors="pt")
    input_features = inputs.input_features.to(device)

    gen_kwargs = {"max_new_tokens": int(max_new_tokens)}

    if decoder_prompt is not None:
        decoder_input_ids, decoder_attention_mask = decoder_prompt
        pred_ids = model.generate(
            input_features,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
            **gen_kwargs,
        )
    else:
        pred_ids = model.generate(input_features, **gen_kwargs)

    text = processor.batch_decode(pred_ids, skip_special_tokens=True)[0].strip()
    return text


# ----------------------------
# Manifest handling
# ----------------------------
def resolve_segment_path(manifest_path: Path, seg_path: str) -> str:
    """
    Resolve a segment audio path robustly:
    - if absolute and exists: use it
    - if relative: try relative to manifest directory
    - else: try relative to project root (cwd)
    """
    p = Path(seg_path)

    if p.is_absolute() and p.exists():
        return str(p)

    cand1 = (manifest_path.parent / p).resolve()
    if cand1.exists():
        return str(cand1)

    cand2 = (Path.cwd() / p).resolve()
    if cand2.exists():
        return str(cand2)

    return str(p)


# ----------------------------
# CLI
# ----------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=None, help="Manifest JSON (recommended).")
    ap.add_argument("--audio", default=None, help="Single audio file path (one-line transcript).")
    ap.add_argument("--out", default="outputs/transcripts/raw.txt", help="Raw transcript output path.")
    ap.add_argument("--model", default="openai/whisper-small", help="HF model id.")
    ap.add_argument("--language", default="somali", help="Whisper language prompt (e.g., 'somali' or 'so').")
    ap.add_argument("--task", default="transcribe", choices=["transcribe", "translate"], help="Whisper task.")
    ap.add_argument("--max_new_tokens", type=int, default=256, help="Max tokens per segment.")
    ap.add_argument("--device", default=None, help="cpu|cuda|mps (default auto).")
    ap.add_argument("--quiet", action="store_true", help="Silence HF advisory warnings.")
    args = ap.parse_args()

    configure_quiet_logging(args.quiet)

    if not args.manifest and not args.audio:
        raise SystemExit("Provide either --manifest or --audio")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    clean_path = out_path.parent / "clean.txt"
    tmp_dir = out_path.parent / "_tmp_resampled_16k"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    device = pick_device(args.device)

    processor = WhisperProcessor.from_pretrained(args.model)
    model = WhisperForConditionalGeneration.from_pretrained(args.model)
    model.to(device)
    model.eval()

    # Prevent config-level forced ids overriding our prompt logic
    try:
        if getattr(model.generation_config, "forced_decoder_ids", None) is not None:
            model.generation_config.forced_decoder_ids = None
    except Exception:
        pass

    decoder_prompt = build_decoder_prompt(
        processor=processor,
        model=model,
        language=args.language,
        task=args.task,
        device=device,
    )

    raw_lines: List[str] = []
    clean_lines: List[str] = []

    with torch.no_grad():
        if args.audio:
            audio_path = str(Path(args.audio).expanduser())
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio not found: {audio_path}")

            audio_path = ensure_16k_mono(audio_path, tmp_dir)

            text = transcribe_one(
                processor=processor,
                model=model,
                audio_path=audio_path,
                device=device,
                decoder_prompt=decoder_prompt,
                max_new_tokens=args.max_new_tokens,
            )

            raw_lines.append(text)
            clean_lines.append(normalize_text(text))
            print(f"[1/1] {Path(audio_path).name} -> {len(text)} chars")

        else:
            manifest_path = Path(args.manifest).expanduser()
            if not manifest_path.exists():
                raise FileNotFoundError(f"Manifest not found: {manifest_path}")

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            segments = manifest.get("segments", [])
            if not segments:
                raise RuntimeError("Manifest has no 'segments'. Did build_verification_fleurs.py run?")

            n = len(segments)
            for i, seg in enumerate(segments, start=1):
                seg_raw_path = seg.get("path")
                if not seg_raw_path:
                    raise RuntimeError(f"Segment missing 'path': {seg}")

                seg_path = resolve_segment_path(manifest_path, seg_raw_path)
                if not os.path.exists(seg_path):
                    raise FileNotFoundError(f"Segment audio not found: {seg_path}")

                seg_path_16k = ensure_16k_mono(seg_path, tmp_dir)

                text = transcribe_one(
                    processor=processor,
                    model=model,
                    audio_path=seg_path_16k,
                    device=device,
                    decoder_prompt=decoder_prompt,
                    max_new_tokens=args.max_new_tokens,
                )

                raw_lines.append(text)
                clean_lines.append(normalize_text(text))
                print(f"[{i}/{n}] {Path(seg_path).name} -> {len(text)} chars")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(raw_lines) + "\n")

    with open(clean_path, "w", encoding="utf-8") as f:
        f.write("\n".join(clean_lines) + "\n")

    print(f"Wrote raw:   {out_path}")
    print(f"Wrote clean: {clean_path}")


if __name__ == "__main__":
    main()
