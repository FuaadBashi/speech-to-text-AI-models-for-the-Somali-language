#!/usr/bin/env python3
"""
Two-stage fine-tuning for Somali ASR with Whisper:

Stage A (main): skydheere/soomali-asr-dataset (train) -> validate on (validation)
Stage B (optional): short adaptation on google/fleurs so_so TRAIN only
  - IMPORTANT: do NOT use FLEURS val/test for training.
  - We still evaluate on Stage-A validation so you can compare before/after adaptation.

Includes:
- T4-friendly defaults
- beam-search WER evaluation (predict_with_generate)
- terminal "table style" logs (step/epoch/loss/lr/grad_norm/time/gpu_mem)
"""

import argparse
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from datasets import Audio, DatasetDict, load_dataset

import evaluate
from transformers import (
    WhisperForConditionalGeneration,
    WhisperProcessor,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    TrainerCallback,
    set_seed,
)

# Text normalizer used by Whisper recipes
try:
    from transformers.models.whisper.english_normalizer import BasicTextNormalizer
except Exception:
    BasicTextNormalizer = None


def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def guess_columns(ds) -> Tuple[str, str]:
    cols = list(ds.column_names)
    # Guess audio column
    audio_col = None
    for c in ["audio", "speech", "wav", "path"]:
        if c in cols:
            audio_col = c
            break
    if audio_col is None:
        # fallback: first Audio feature
        for c in cols:
            if hasattr(ds.features.get(c, None), "sampling_rate"):
                audio_col = c
                break
    if audio_col is None:
        raise ValueError(f"Could not find audio column. Available columns: {cols}")

    # Guess text column
    text_col = None
    for c in ["sentence", "text", "transcription", "transcript", "normalized_text"]:
        if c in cols:
            text_col = c
            break
    if text_col is None:
        raise ValueError(f"Could not find transcript/text column. Available columns: {cols}")

    return audio_col, text_col


def normalize_somali_text(s: str) -> str:
    """
    Lightweight normalizer for WER:
    - lowercase
    - remove punctuation
    - collapse whitespace
    """
    s = s.lower().strip()
    s = re.sub(r"[“”\"'`´’]", "", s)
    s = re.sub(r"[^a-z0-9\s\-]", " ", s)  # keep letters/digits/hyphen
    s = re.sub(r"\s+", " ", s).strip()
    return s


@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: WhisperProcessor
    decoder_start_token_id: int

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        # input_features
        input_features = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        # labels
        label_features = [{"input_ids": f["labels"]} for f in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        labels = labels_batch["input_ids"]
        # Replace padding with -100 for loss
        labels = labels.masked_fill(labels_batch["attention_mask"].ne(1), -100)

        # Remove initial BOS token if present (common Whisper practice)
        if (labels[:, 0] == self.decoder_start_token_id).all().item():
            labels = labels[:, 1:]

        batch["labels"] = labels

        # Helps avoid "attention_mask cannot be inferred" warnings in some setups
        batch["decoder_attention_mask"] = labels_batch["attention_mask"]

        return batch


class TableLoggerCallback(TrainerCallback):
    def __init__(self, print_every_steps: int = 50):
        self.print_every_steps = print_every_steps
        self.t0 = None
        self.header_printed = False

    def on_train_begin(self, args, state, control, **kwargs):
        self.t0 = time.time()
        self.header_printed = False

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return
        step = int(state.global_step)
        if step == 0:
            return
        if step % self.print_every_steps != 0 and "eval_wer" not in logs and "eval_wer_norm" not in logs:
            return

        elapsed = int(time.time() - self.t0) if self.t0 else 0
        gpu_mem = ""
        if torch.cuda.is_available():
            mb = torch.cuda.max_memory_allocated() / (1024**2)
            gpu_mem = f"{mb:,.0f}"

        if not self.header_printed:
            print("STEP   EPOCH   LOSS     LR         GNORM    ELAPSED(s)  GPU_MAX_MB   EVAL_WER  EVAL_WER_N")
            print("-----  ------  -------  ---------  -------  ----------  ----------  --------  ---------")
            self.header_printed = True

        loss = logs.get("loss", None)
        lr = logs.get("learning_rate", None)
        gn = logs.get("grad_norm", None)
        ew = logs.get("eval_wer", logs.get("eval_wer_raw", None))
        ewn = logs.get("eval_wer_norm", None)

        def fnum(x, fmt):
            return (fmt % x) if isinstance(x, (float, int)) else ""

        print(
            f"{step:5d}  "
            f"{state.epoch:6.2f}  "
            f"{fnum(loss,'%.4f'):>7}  "
            f"{fnum(lr,'%.6f'):>9}  "
            f"{fnum(gn,'%.3f'):>7}  "
            f"{elapsed:10d}  "
            f"{gpu_mem:>10}  "
            f"{fnum(ew,'%.3f'):>8}  "
            f"{fnum(ewn,'%.3f'):>9}"
        )


def build_compute_metrics(processor: WhisperProcessor):
    wer = evaluate.load("wer")
    basic_norm = BasicTextNormalizer() if BasicTextNormalizer is not None else None

    def compute_metrics(pred):
        pred_ids = pred.predictions
        if isinstance(pred_ids, tuple):
            pred_ids = pred_ids[0]

        label_ids = pred.label_ids

        # Replace -100 in labels so we can decode
        label_ids = np.where(label_ids == -100, processor.tokenizer.pad_token_id, label_ids)

        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

        # Raw WER (still useful)
        wer_raw = wer.compute(predictions=pred_str, references=label_str)

        # Normalized WER (recommended)
        if basic_norm is not None:
            pred_norm = [basic_norm(s) for s in pred_str]
            lab_norm = [basic_norm(s) for s in label_str]
        else:
            pred_norm = [normalize_somali_text(s) for s in pred_str]
            lab_norm = [normalize_somali_text(s) for s in label_str]
        wer_norm = wer.compute(predictions=pred_norm, references=lab_norm)

        return {"wer_raw": wer_raw, "wer_norm": wer_norm}

    return compute_metrics


def prepare_dataset(
    dsd: DatasetDict,
    processor: WhisperProcessor,
    max_audio_seconds: float,
    stage_name: str,
) -> Tuple[Any, Any]:
    train_ds = dsd["train"]
    val_ds = dsd.get("validation", None)
    if val_ds is None:
        raise ValueError("Dataset must provide a 'validation' split for Stage A.")

    audio_col, text_col = guess_columns(train_ds)

    # Ensure audio is decoded at 16kHz
    train_ds = train_ds.cast_column(audio_col, Audio(sampling_rate=16000))
    val_ds = val_ds.cast_column(audio_col, Audio(sampling_rate=16000))

    def _prep(batch):
        audio = batch[audio_col]
        batch["input_features"] = processor.feature_extractor(
            audio["array"], sampling_rate=audio["sampling_rate"]
        ).input_features[0]
        batch["labels"] = processor.tokenizer(batch[text_col]).input_ids
        batch["input_length"] = len(audio["array"]) / audio["sampling_rate"]
        return batch

    print(f"[{now_ts()}] Preparing {stage_name} train...")
    train_ds = train_ds.map(_prep, remove_columns=train_ds.column_names, desc=f"Preparing {stage_name} train")
    print(f"[{now_ts()}] Preparing {stage_name} validation...")
    val_ds = val_ds.map(_prep, remove_columns=val_ds.column_names, desc=f"Preparing {stage_name} validation")

    def _filt(x):
        return x["input_length"] <= max_audio_seconds

    train_ds = train_ds.filter(_filt, desc="Filter")
    val_ds = val_ds.filter(_filt, desc="Filter")

    return train_ds, val_ds


def prepare_fleurs_train(
    processor: WhisperProcessor,
    max_audio_seconds: float,
    fleurs_lang: str = "so_so",
):
    fleurs = load_dataset("google/fleurs", fleurs_lang, split="train")
    audio_col, text_col = guess_columns(fleurs)
    fleurs = fleurs.cast_column(audio_col, Audio(sampling_rate=16000))

    def _prep(batch):
        audio = batch[audio_col]
        batch["input_features"] = processor.feature_extractor(
            audio["array"], sampling_rate=audio["sampling_rate"]
        ).input_features[0]
        batch["labels"] = processor.tokenizer(batch[text_col]).input_ids
        batch["input_length"] = len(audio["array"]) / audio["sampling_rate"]
        return batch

    print(f"[{now_ts()}] Preparing Stage-B FLEURS train (so_so)...")
    fleurs = fleurs.map(_prep, remove_columns=fleurs.column_names, desc="Preparing FLEURS train")
    fleurs = fleurs.filter(lambda x: x["input_length"] <= max_audio_seconds, desc="Filter")
    return fleurs


def make_training_args(
    *,
    output_dir: str,
    num_train_epochs: float,
    max_steps: int,
    per_device_train_batch_size: int,
    per_device_eval_batch_size: int,
    gradient_accumulation_steps: int,
    learning_rate: float,
    warmup_steps: int,
    warmup_ratio: float,
    weight_decay: float,
    logging_steps: int,
    eval_strategy: str,
    eval_steps: int,
    save_strategy: str,
    save_steps: int,
    save_total_limit: int,
    fp16: bool,
    gradient_checkpointing: bool,
    dataloader_num_workers: int,
    group_by_length: bool,
    predict_with_generate: bool,
    generation_num_beams: int,
    generation_max_length: int,
):
    # Compatibility across Transformers versions: eval_strategy vs evaluation_strategy
    common_kwargs = dict(
        output_dir=output_dir,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_eval_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        warmup_steps=warmup_steps,
        warmup_ratio=warmup_ratio,
        weight_decay=weight_decay,
        num_train_epochs=num_train_epochs,
        max_steps=max_steps if max_steps > 0 else -1,
        logging_steps=logging_steps,
        save_steps=save_steps,
        save_strategy=save_strategy,
        save_total_limit=save_total_limit,
        fp16=fp16,
        gradient_checkpointing=gradient_checkpointing,
        dataloader_num_workers=dataloader_num_workers,
        group_by_length=group_by_length,
        predict_with_generate=predict_with_generate,
        generation_num_beams=generation_num_beams,
        generation_max_length=generation_max_length,
        load_best_model_at_end=True,
        metric_for_best_model="wer_norm",
        greater_is_better=False,
        report_to=[],  # keep terminal clean (no wandb)
        logging_first_step=True,
        remove_unused_columns=False,
    )

    try:
        return Seq2SeqTrainingArguments(
            **common_kwargs,
            eval_strategy=eval_strategy,
            eval_steps=eval_steps,
        )
    except TypeError:
        # Older versions
        return Seq2SeqTrainingArguments(
            **common_kwargs,
            evaluation_strategy=eval_strategy,
            eval_steps=eval_steps,
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model", default="openai/whisper-medium")
    ap.add_argument("--language", default="somali", help="Whisper language name, e.g. 'somali'")
    ap.add_argument("--out_dir", default="outputs/checkpoints/whisper_medium_two_stage_t4")

    ap.add_argument("--stage_a_dataset", default="skydheere/soomali-asr-dataset")
    ap.add_argument("--max_audio_seconds", type=float, default=15.0)

    # Stage A training control
    ap.add_argument("--num_train_epochs", type=float, default=1.0)
    ap.add_argument("--max_steps", type=int, default=0, help="If >0, overrides epochs (faster on Colab).")

    ap.add_argument("--learning_rate", type=float, default=1e-5)
    ap.add_argument("--warmup_steps", type=int, default=0)
    ap.add_argument("--warmup_ratio", type=float, default=0.05)
    ap.add_argument("--weight_decay", type=float, default=0.01)

    ap.add_argument("--per_device_train_batch_size", type=int, default=1)
    ap.add_argument("--per_device_eval_batch_size", type=int, default=1)
    ap.add_argument("--gradient_accumulation_steps", type=int, default=16)

    ap.add_argument("--fp16", action="store_true")
    ap.add_argument("--gradient_checkpointing", action="store_true")
    ap.add_argument("--freeze_encoder", action="store_true", help="Reduces memory; can help T4 stability.")

    ap.add_argument("--eval_strategy", default="steps", choices=["no", "steps", "epoch"])
    ap.add_argument("--eval_steps", type=int, default=500)
    ap.add_argument("--save_strategy", default="steps", choices=["steps", "epoch"])
    ap.add_argument("--save_steps", type=int, default=500)
    ap.add_argument("--save_total_limit", type=int, default=2)

    ap.add_argument("--logging_steps", type=int, default=50)
    ap.add_argument("--dataloader_num_workers", type=int, default=2)
    ap.add_argument("--group_by_length", action="store_true")

    # Beam search during eval/inference
    ap.add_argument("--eval_num_beams", type=int, default=5)
    ap.add_argument("--generation_max_length", type=int, default=225)

    # Stage B adaptation
    ap.add_argument("--adapt_fleurs", action="store_true")
    ap.add_argument("--adapt_epochs", type=float, default=1.0)
    ap.add_argument("--adapt_max_steps", type=int, default=0)
    ap.add_argument("--adapt_lr", type=float, default=5e-6)
    ap.add_argument("--adapt_max_seconds", type=float, default=12.0)

    ap.add_argument("--seed", type=int, default=42)

    args = ap.parse_args()

    set_seed(args.seed)

    os.makedirs(args.out_dir, exist_ok=True)
    print(f"[{now_ts()}] Using GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print(f"[{now_ts()}] base_model={args.base_model}")
    print(f"[{now_ts()}] out_dir={args.out_dir}")

    # Processor + Model
    processor = WhisperProcessor.from_pretrained(args.base_model)

    model = WhisperForConditionalGeneration.from_pretrained(args.base_model)

    # IMPORTANT for training with gradient checkpointing
    model.config.use_cache = False

    # Configure language/task in generation config (modern approach)
    model.generation_config.language = args.language
    model.generation_config.task = "transcribe"

    # Optional memory saver
    if args.freeze_encoder:
        for p in model.model.encoder.parameters():
            p.requires_grad = False
        print(f"[{now_ts()}] Encoder frozen (freeze_encoder=True)")

    # Gradient checkpointing: prefer non-reentrant (can fix some backward issues)
    if args.gradient_checkpointing:
        try:
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            print(f"[{now_ts()}] Gradient checkpointing enabled (use_reentrant=False)")
        except TypeError:
            model.gradient_checkpointing_enable()
            print(f"[{now_ts()}] Gradient checkpointing enabled (default)")

    # Stage A dataset
    dsd = load_dataset(args.stage_a_dataset)
    if not isinstance(dsd, DatasetDict):
        raise ValueError("Expected DatasetDict with train/validation splits.")

    train_a, val_a = prepare_dataset(
        dsd, processor, max_audio_seconds=args.max_audio_seconds, stage_name="Stage-A"
    )
    print(f"[Stage-A] train_kept={len(train_a)}  val_kept={len(val_a)}")

    data_collator = DataCollatorSpeechSeq2SeqWithPadding(
        processor=processor, decoder_start_token_id=model.config.decoder_start_token_id
    )

    compute_metrics = build_compute_metrics(processor)

    stage_a_dir = os.path.join(args.out_dir, "stage_a")
    training_args_a = make_training_args(
        output_dir=stage_a_dir,
        num_train_epochs=args.num_train_epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        logging_steps=args.logging_steps,
        eval_strategy=args.eval_strategy,
        eval_steps=args.eval_steps,
        save_strategy=args.save_strategy,
        save_steps=args.save_steps,
        save_total_limit=args.save_total_limit,
        fp16=args.fp16,
        gradient_checkpointing=args.gradient_checkpointing,
        dataloader_num_workers=args.dataloader_num_workers,
        group_by_length=args.group_by_length,
        predict_with_generate=True,
        generation_num_beams=args.eval_num_beams,
        generation_max_length=args.generation_max_length,
    )

    cb = TableLoggerCallback(print_every_steps=args.logging_steps)

    trainer_kwargs = dict(
        model=model,
        args=training_args_a,
        train_dataset=train_a,
        eval_dataset=val_a,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        callbacks=[cb],
    )

    # Avoid deprecation problems: processing_class (new) vs tokenizer (old)
    try:
        trainer_a = Seq2SeqTrainer(**trainer_kwargs, processing_class=processor)
    except TypeError:
        trainer_a = Seq2SeqTrainer(**trainer_kwargs, tokenizer=processor.tokenizer)

    print(f"[{now_ts()}] Stage A: training on {args.stage_a_dataset}...")
    trainer_a.train()
    trainer_a.save_model(stage_a_dir)
    processor.save_pretrained(stage_a_dir)

    # Optional Stage B: FLEURS train-only adaptation
    if args.adapt_fleurs:
        print(f"[{now_ts()}] Stage B: short domain adaptation on google/fleurs so_so TRAIN only...")
        fleurs_train = prepare_fleurs_train(processor, max_audio_seconds=args.adapt_max_seconds, fleurs_lang="so_so")

        stage_b_dir = os.path.join(args.out_dir, "stage_b")
        training_args_b = make_training_args(
            output_dir=stage_b_dir,
            num_train_epochs=args.adapt_epochs,
            max_steps=args.adapt_max_steps,
            per_device_train_batch_size=args.per_device_train_batch_size,
            per_device_eval_batch_size=args.per_device_eval_batch_size,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            learning_rate=args.adapt_lr,
            warmup_steps=0,
            warmup_ratio=0.0,
            weight_decay=args.weight_decay,
            logging_steps=args.logging_steps,
            eval_strategy=args.eval_strategy,
            eval_steps=args.eval_steps,
            save_strategy=args.save_strategy,
            save_steps=args.save_steps,
            save_total_limit=args.save_total_limit,
            fp16=args.fp16,
            gradient_checkpointing=args.gradient_checkpointing,
            dataloader_num_workers=args.dataloader_num_workers,
            group_by_length=args.group_by_length,
            predict_with_generate=True,
            generation_num_beams=args.eval_num_beams,
            generation_max_length=args.generation_max_length,
        )

        trainer_kwargs_b = dict(
            model=trainer_a.model,          # continue from Stage A weights
            args=training_args_b,
            train_dataset=fleurs_train,     # TRAIN ONLY
            eval_dataset=val_a,             # evaluate on Stage-A validation (allowed)
            data_collator=data_collator,
            compute_metrics=compute_metrics,
            callbacks=[cb],
        )

        try:
            trainer_b = Seq2SeqTrainer(**trainer_kwargs_b, processing_class=processor)
        except TypeError:
            trainer_b = Seq2SeqTrainer(**trainer_kwargs_b, tokenizer=processor.tokenizer)

        trainer_b.train()
        trainer_b.save_model(stage_b_dir)
        processor.save_pretrained(stage_b_dir)

    print(f"[{now_ts()}] DONE. Outputs in: {args.out_dir}")


if __name__ == "__main__":
    main()
