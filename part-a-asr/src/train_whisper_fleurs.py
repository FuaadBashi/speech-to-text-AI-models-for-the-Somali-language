#!/usr/bin/env python3
"""
Fine-tune Whisper on FLEURS Somali (so_so) train + validation.
"""

import os
import io
import json
import argparse
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import soundfile as sf
from datasets import load_dataset, Audio

import torch
from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

# -------------------------
# Option B: robust import
# -------------------------
try:
    from text_normalize import normalize_text  # when running inside src/
except ModuleNotFoundError:
    import sys
    sys.path.append(os.path.dirname(__file__))  # add src/ to sys.path
    from text_normalize import normalize_text


# -------------------------
# Audio decode helpers
# -------------------------
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
            raise RuntimeError(f"Audio object has neither 'bytes' nor 'path'. Keys={list(audio_obj.keys())}")
        wav_bytes = _ffmpeg_decode_16k_mono_wav_bytes_from_path(path)

    audio, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32")
    if sr != 16000:
        raise RuntimeError(f"Expected 16000 Hz after ffmpeg decode, got {sr}")
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return audio


# -------------------------
# Data collator
# -------------------------
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


# -------------------------
# WER metric (aligned)
# -------------------------
def compute_wer_word_level(pred_strs: List[str], ref_strs: List[str]) -> float:
    pred_norm = [normalize_text(x) for x in pred_strs]
    ref_norm = [normalize_text(x) for x in ref_strs]

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

    total_edits = 0
    total_words = 0
    for p, r in zip(pred_norm, ref_norm):
        pw = p.split()
        rw = r.split()
        total_edits += edit_distance_words(pw, rw)
        total_words += len(rw)

    if total_words == 0:
        return 0.0 if total_edits == 0 else 1.0
    return float(total_edits) / float(total_words)


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--base_model", default="openai/whisper-small")
    ap.add_argument("--language", default="somali")
    ap.add_argument("--out_dir", default="outputs/checkpoints/whisper_fleurs_so_best")
    ap.add_argument("--max_audio_seconds", type=float, default=30.0)

    ap.add_argument("--num_train_epochs", type=int, default=5)
    ap.add_argument("--learning_rate", type=float, default=1e-5)
    ap.add_argument("--warmup_steps", type=int, default=200)
    ap.add_argument("--per_device_train_batch_size", type=int, default=8)
    ap.add_argument("--per_device_eval_batch_size", type=int, default=8)
    ap.add_argument("--gradient_accumulation_steps", type=int, default=2)

    ap.add_argument("--eval_steps", type=int, default=500)
    ap.add_argument("--save_steps", type=int, default=500)
    ap.add_argument("--logging_steps", type=int, default=50)

    ap.add_argument("--fp16", action="store_true")
    ap.add_argument("--bf16", action="store_true")
    ap.add_argument("--gradient_checkpointing", action="store_true")
    ap.add_argument("--dataloader_num_workers", type=int, default=2)

    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # Load FLEURS Somali (so_so) train + validation.
    train_ds = load_dataset("google/fleurs", data_dir="so_so", split="train", revision="refs/convert/parquet")
    val_ds   = load_dataset("google/fleurs", data_dir="so_so", split="validation", revision="refs/convert/parquet")

    # Avoid HF audio decoding
    train_ds = train_ds.cast_column("audio", Audio(decode=False))
    val_ds   = val_ds.cast_column("audio", Audio(decode=False))

    processor = WhisperProcessor.from_pretrained(args.base_model)
    model = WhisperForConditionalGeneration.from_pretrained(args.base_model)

    # Force Somali decoding
    forced_decoder_ids = processor.get_decoder_prompt_ids(language=args.language, task="transcribe")
    model.config.forced_decoder_ids = forced_decoder_ids
    if hasattr(model, "generation_config") and hasattr(model.generation_config, "forced_decoder_ids"):
        model.generation_config.forced_decoder_ids = forced_decoder_ids
    model.config.suppress_tokens = []

    # Gradient checkpointing fix: use_reentrant=False (prevents double-backward errors on some stacks)
    if args.gradient_checkpointing:
        import inspect
        sig = inspect.signature(model.gradient_checkpointing_enable)
        if "gradient_checkpointing_kwargs" in sig.parameters:
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        else:
            model.gradient_checkpointing_enable()
        model.config.use_cache = False  # required for checkpointing on encoder-decoder models

    def pick_text(ex: Dict[str, Any]) -> str:
        txt = ex.get("transcription")
        if txt is None or str(txt).strip() == "":
            txt = ex.get("raw_transcription", "")
        return str(txt)

    # Dummy small values so datasets.map ALWAYS sees the same keys (avoids KeyError)
    dummy_feat = np.zeros((80, 10), dtype=np.float32)
    dummy_labels = [processor.tokenizer.pad_token_id]

    def prep_example(ex: Dict[str, Any]) -> Dict[str, Any]:
        audio = load_audio_16k_mono(ex["audio"])
        dur = float(len(audio)) / 16000.0
        if dur > args.max_audio_seconds:
            return {"input_features": dummy_feat, "labels": dummy_labels, "_filtered": True}

        txt = normalize_text(pick_text(ex))
        if txt.strip() == "":
            return {"input_features": dummy_feat, "labels": dummy_labels, "_filtered": True}

        inputs = processor.feature_extractor(audio, sampling_rate=16000)
        labels = processor.tokenizer(txt).input_ids

        return {"input_features": inputs.input_features[0], "labels": labels, "_filtered": False}

    train_mapped = train_ds.map(prep_example, remove_columns=train_ds.column_names, desc="Preparing train")
    train_mapped = train_mapped.filter(lambda x: not x["_filtered"]).remove_columns(["_filtered"])

    val_mapped = val_ds.map(prep_example, remove_columns=val_ds.column_names, desc="Preparing validation")
    val_mapped = val_mapped.filter(lambda x: not x["_filtered"]).remove_columns(["_filtered"])

    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)

    def compute_metrics(eval_pred):
        pred_ids = eval_pred.predictions
        label_ids = eval_pred.label_ids

        if isinstance(pred_ids, tuple):
            pred_ids = pred_ids[0]

        label_ids = np.where(label_ids != -100, label_ids, processor.tokenizer.pad_token_id)

        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

        return {"wer": compute_wer_word_level(pred_str, label_str)}

    # Use eval_strategy if available, else fallback
    import inspect
    ta_sig = inspect.signature(Seq2SeqTrainingArguments.__init__)
    ta_kwargs = dict(
        output_dir=args.out_dir,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        num_train_epochs=args.num_train_epochs,
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        predict_with_generate=True,
        generation_max_length=225,
        fp16=bool(args.fp16),
        bf16=bool(args.bf16),
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        dataloader_num_workers=args.dataloader_num_workers,
        report_to="none",
        seed=args.seed,
        remove_unused_columns=False,
    )

    if "eval_strategy" in ta_sig.parameters:
        ta_kwargs["eval_strategy"] = "steps"
    else:
        ta_kwargs["evaluation_strategy"] = "steps"

    # Safety: disable torch.compile if this transformers version supports the flag
    if "torch_compile" in ta_sig.parameters:
        ta_kwargs["torch_compile"] = False

    training_args = Seq2SeqTrainingArguments(**ta_kwargs)

    # Avoid "tokenizer is deprecated" warning by using processing_class when available
    trainer_kwargs = dict(
        args=training_args,
        model=model,
        train_dataset=train_mapped,
        eval_dataset=val_mapped,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    tr_sig = inspect.signature(Seq2SeqTrainer.__init__)
    if "processing_class" in tr_sig.parameters:
        trainer_kwargs["processing_class"] = processor
    else:
        trainer_kwargs["tokenizer"] = processor.feature_extractor

    trainer = Seq2SeqTrainer(**trainer_kwargs)
    trainer.train()

    trainer.save_model(args.out_dir)
    processor.save_pretrained(args.out_dir)

    with open(os.path.join(args.out_dir, "train_config.json"), "w", encoding="utf-8") as f:
        json.dump(vars(args), f, indent=2)

    print(f"Saved trained model -> {args.out_dir}")


if __name__ == "__main__":
    main()
