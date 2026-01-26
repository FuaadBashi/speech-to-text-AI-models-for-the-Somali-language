#!/usr/bin/env python3
"""
Two-stage Whisper fine-tuning for Somali ASR.
"""

import os
import io
import json
import time
import argparse
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf
import torch
from datasets import load_dataset, Audio
from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    TrainerCallback,
)

# ---- Option B robust import for your repo ----
try:
    from text_normalize import normalize_text
except ModuleNotFoundError:
    import sys
    sys.path.append(os.path.dirname(__file__))
    from text_normalize import normalize_text


# =========================
# Audio decode helpers
# =========================
def _ffmpeg_decode_16k_mono_wav_bytes_from_path(path: str) -> bytes:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", path,
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        "pipe:1",
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed for {path}:\n{p.stderr.decode('utf-8', errors='ignore')}")
    return p.stdout


def _ffmpeg_decode_16k_mono_wav_bytes_from_bytes(b: bytes) -> bytes:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", "pipe:0",
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        "pipe:1",
    ]
    p = subprocess.run(cmd, input=b, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed from bytes:\n{p.stderr.decode('utf-8', errors='ignore')}")
    return p.stdout


def load_audio_16k_mono(audio_obj: Dict[str, Any]) -> np.ndarray:
    if audio_obj.get("bytes") is not None:
        wav_bytes = _ffmpeg_decode_16k_mono_wav_bytes_from_bytes(audio_obj["bytes"])
    else:
        path = audio_obj.get("path")
        if not path:
            raise RuntimeError(f"Audio object missing 'path'/'bytes'. Keys={list(audio_obj.keys())}")
        wav_bytes = _ffmpeg_decode_16k_mono_wav_bytes_from_path(path)

    audio, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32")
    if sr != 16000:
        raise RuntimeError(f"Expected 16000 Hz after ffmpeg decode, got {sr}")
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return audio


# =========================
# Data collator
# =========================
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: WhisperProcessor

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        input_features = [{"input_features": f["input_features"]} for f in features]
        label_features = [{"input_ids": f["labels"]} for f in features]

        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        labels = labels_batch["input_ids"].masked_fill(labels_batch["attention_mask"].ne(1), -100)
        batch["labels"] = labels
        return batch


# =========================
# Simple console table logger
# =========================
class ConsoleTableCallback(TrainerCallback):
    def __init__(self):
        self.t0 = time.time()
        self.header_printed = False

    def _gpu_mem_mb(self) -> str:
        if not torch.cuda.is_available():
            return "-"
        mb = torch.cuda.max_memory_allocated() / (1024**2)
        return f"{mb:,.0f}"

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs:
            return
        if not self.header_printed:
            print("\nSTEP   EPOCH   LOSS     LR         GNORM    ELAPSED   GPU_MB")
            print("-----  ------  -------  ---------  -------  --------  ------")
            self.header_printed = True

        step = state.global_step
        epoch = state.epoch if state.epoch is not None else 0.0
        loss = logs.get("loss", None)
        lr = logs.get("learning_rate", None)
        gn = logs.get("grad_norm", None)
        elapsed = time.time() - self.t0

        def fmt(x, w=7, p=4):
            if x is None:
                return " " * w
            return f"{x:{w}.{p}f}"

        print(
            f"{step:5d}  {epoch:6.2f}  "
            f"{fmt(loss,7,4)}  {fmt(lr,9,6)}  {fmt(gn,7,3)}  "
            f"{elapsed:8.0f}s  {self._gpu_mem_mb():>6}"
        )

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if not metrics:
            return
        wer = metrics.get("eval_wer", None)
        if wer is not None:
            print(f"\n[EVAL] step={state.global_step} epoch={state.epoch:.2f}  WER={wer:.4f}\n")


# =========================
# WER metric
# =========================
def wer_word_level(preds: List[str], refs: List[str]) -> float:
    # word-level Levenshtein WER
    def edit_distance_words(h: List[str], r: List[str]) -> int:
        dp = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
        for i in range(len(r) + 1):
            dp[i][0] = i
        for j in range(len(h) + 1):
            dp[0][j] = j
        for i in range(1, len(r) + 1):
            for j in range(1, len(h) + 1):
                cost = 0 if r[i - 1] == h[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost,
                )
        return dp[len(r)][len(h)]

    total_edits, total_words = 0, 0
    for p, r in zip(preds, refs):
        p = normalize_text(p)
        r = normalize_text(r)
        pw, rw = p.split(), r.split()
        total_edits += edit_distance_words(pw, rw)
        total_words += len(rw)

    if total_words == 0:
        return 0.0 if total_edits == 0 else 1.0
    return float(total_edits) / float(total_words)


# =========================
# Dataset helpers
# =========================
def pick_text(ex: Dict[str, Any]) -> str:
    # Robust across datasets
    for k in ["sentence", "text", "transcription", "transcript", "raw_transcription"]:
        if k in ex and ex[k] is not None and str(ex[k]).strip() != "":
            return str(ex[k])
    return ""


def prepare_dataset(
    ds,
    processor: WhisperProcessor,
    max_audio_seconds: float,
    desc: str,
):
    ds = ds.cast_column("audio", Audio(decode=False))

    # Dummy feature to keep schema stable even for filtered rows
    dummy_feats = np.zeros((80, 1), dtype=np.float32)
    dummy_labels = [processor.tokenizer.pad_token_id]

    def prep(ex: Dict[str, Any]) -> Dict[str, Any]:
        audio = load_audio_16k_mono(ex["audio"])
        dur = float(len(audio)) / 16000.0

        txt = normalize_text(pick_text(ex))
        bad = (dur > max_audio_seconds) or (txt.strip() == "")

        if bad:
            return {"input_features": dummy_feats, "labels": dummy_labels, "_filtered": True}

        feats = processor.feature_extractor(audio, sampling_rate=16000).input_features[0]
        labels = processor.tokenizer(txt).input_ids
        return {"input_features": feats, "labels": labels, "_filtered": False}

    mapped = ds.map(prep, remove_columns=ds.column_names, desc=desc)
    kept = mapped.filter(lambda x: not x["_filtered"]).remove_columns(["_filtered"])
    return kept


# =========================
# Main
# =========================
def main():
    ap = argparse.ArgumentParser()

    # Core
    ap.add_argument("--base_model", default="openai/whisper-medium")
    ap.add_argument("--language", default="somali")
    ap.add_argument("--out_dir", default="outputs/checkpoints/whisper_medium_two_stage_t4")

    # Stage A dataset
    ap.add_argument("--stage_a_dataset", default="skydheere/soomali-asr-dataset")
    ap.add_argument("--max_audio_seconds", type=float, default=20.0)

    # Training (Stage A)
    ap.add_argument("--num_train_epochs", type=int, default=5)
    ap.add_argument("--learning_rate", type=float, default=1e-5)
    ap.add_argument("--warmup_steps", type=int, default=500)
    ap.add_argument("--per_device_train_batch_size", type=int, default=2)   # whisper-medium on T4
    ap.add_argument("--per_device_eval_batch_size", type=int, default=2)
    ap.add_argument("--gradient_accumulation_steps", type=int, default=8)   # effective batch ~16
    ap.add_argument("--fp16", action="store_true")
    ap.add_argument("--gradient_checkpointing", action="store_true")
    ap.add_argument("--eval_steps", type=int, default=500)
    ap.add_argument("--save_steps", type=int, default=500)
    ap.add_argument("--logging_steps", type=int, default=50)
    ap.add_argument("--eval_num_beams", type=int, default=5)

    # Stage B (FLEURS adapt)
    ap.add_argument("--adapt_fleurs", action="store_true")
    ap.add_argument("--adapt_epochs", type=int, default=1)
    ap.add_argument("--adapt_lr", type=float, default=3e-6)
    ap.add_argument("--adapt_max_seconds", type=float, default=20.0)

    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    stage_a_dir = os.path.join(args.out_dir, "stage_a")
    stage_b_dir = os.path.join(args.out_dir, "stage_b_adapt_fleurs")
    os.makedirs(stage_a_dir, exist_ok=True)

    # GPU print
    if torch.cuda.is_available():
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Using GPU: {torch.cuda.get_device_name(0)}")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] base_model={args.base_model}")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] out_dir={args.out_dir}")

    processor = WhisperProcessor.from_pretrained(args.base_model)
    model = WhisperForConditionalGeneration.from_pretrained(args.base_model)

    # Force Somali + transcribe
    forced_decoder_ids = processor.get_decoder_prompt_ids(language=args.language, task="transcribe")
    model.config.forced_decoder_ids = forced_decoder_ids
    if hasattr(model, "generation_config") and hasattr(model.generation_config, "forced_decoder_ids"):
        model.generation_config.forced_decoder_ids = forced_decoder_ids

    model.config.suppress_tokens = []

    # If gradient checkpointing: MUST disable cache
    if args.gradient_checkpointing:
        model.config.use_cache = False
        if hasattr(model, "generation_config"):
            model.generation_config.use_cache = False

    # ---- Stage A: skydheere/soomali-asr-dataset ----
    ds_a = load_dataset(args.stage_a_dataset)
    train_a = ds_a["train"]
    val_a = ds_a["validation"]

    train_a = prepare_dataset(train_a, processor, args.max_audio_seconds, "Preparing Stage-A train")
    val_a = prepare_dataset(val_a, processor, args.max_audio_seconds, "Preparing Stage-A validation")

    print(f"[Stage-A] train_kept={len(train_a)}  val_kept={len(val_a)}")

    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)

    def compute_metrics(eval_pred):
        pred_ids = eval_pred.predictions
        label_ids = eval_pred.label_ids
        if isinstance(pred_ids, tuple):
            pred_ids = pred_ids[0]
        label_ids = np.where(label_ids != -100, label_ids, processor.tokenizer.pad_token_id)

        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)
        return {"wer": wer_word_level(pred_str, label_str)}

    training_args_a = Seq2SeqTrainingArguments(
        output_dir=stage_a_dir,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        num_train_epochs=args.num_train_epochs,
        fp16=bool(args.fp16),

        # IMPORTANT: new-style key name
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,

        predict_with_generate=True,
        generation_num_beams=args.eval_num_beams,
        generation_max_length=225,

        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        save_total_limit=2,
        report_to="none",
        seed=args.seed,

        # CRITICAL FIX (PyTorch 2.5 + checkpointing):
        gradient_checkpointing=bool(args.gradient_checkpointing),
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    trainer_a = Seq2SeqTrainer(
        args=training_args_a,
        model=model,
        train_dataset=train_a,
        eval_dataset=val_a,
        data_collator=data_collator,
        tokenizer=processor.feature_extractor,
        compute_metrics=compute_metrics,
        callbacks=[ConsoleTableCallback()],
    )

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Stage A: training on {args.stage_a_dataset}...")
    trainer_a.train()

    trainer_a.save_model(stage_a_dir)
    processor.save_pretrained(stage_a_dir)

    best_a = trainer_a.state.best_model_checkpoint or stage_a_dir
    print(f"[Stage-A] best_checkpoint={best_a}")

    # ---- Stage B: optional FLEURS adapt on train only ----
    if args.adapt_fleurs:
        os.makedirs(stage_b_dir, exist_ok=True)

        processor_b = WhisperProcessor.from_pretrained(best_a)
        model_b = WhisperForConditionalGeneration.from_pretrained(best_a)

        # keep checkpointing stable if enabled
        if args.gradient_checkpointing:
            model_b.config.use_cache = False
            if hasattr(model_b, "generation_config"):
                model_b.generation_config.use_cache = False

        fleurs_train = load_dataset(
            "google/fleurs",
            data_dir="so_so",
            split="train",
            revision="refs/convert/parquet",
        )
        fleurs_train = prepare_dataset(
            fleurs_train, processor_b, args.adapt_max_seconds, "Preparing Stage-B (FLEURS train) adapt"
        )
        print(f"[Stage-B] fleurs_train_kept={len(fleurs_train)}")

        training_args_b = Seq2SeqTrainingArguments(
            output_dir=stage_b_dir,
            per_device_train_batch_size=args.per_device_train_batch_size,
            per_device_eval_batch_size=args.per_device_eval_batch_size,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            learning_rate=args.adapt_lr,
            warmup_steps=max(50, args.warmup_steps // 10),
            num_train_epochs=args.adapt_epochs,
            fp16=bool(args.fp16),

            eval_strategy="no",
            save_strategy="steps",
            save_steps=args.save_steps,
            logging_steps=args.logging_steps,

            predict_with_generate=False,
            load_best_model_at_end=False,
            save_total_limit=2,
            report_to="none",
            seed=args.seed,

            gradient_checkpointing=bool(args.gradient_checkpointing),
            gradient_checkpointing_kwargs={"use_reentrant": False},
        )

        trainer_b = Seq2SeqTrainer(
            args=training_args_b,
            model=model_b,
            train_dataset=fleurs_train,
            eval_dataset=None,
            data_collator=data_collator,
            tokenizer=processor_b.feature_extractor,
            callbacks=[ConsoleTableCallback()],
        )

        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Stage B: adapting on FLEURS so_so train...")
        trainer_b.train()

        trainer_b.save_model(stage_b_dir)
        processor_b.save_pretrained(stage_b_dir)

        print(f"[DONE] Stage-B model saved -> {stage_b_dir}")
    else:
        print("[DONE] Stage-A model saved ->", stage_a_dir)

    with open(os.path.join(args.out_dir, "train_config.json"), "w", encoding="utf-8") as f:
        json.dump(vars(args), f, indent=2)


if __name__ == "__main__":
    main()
