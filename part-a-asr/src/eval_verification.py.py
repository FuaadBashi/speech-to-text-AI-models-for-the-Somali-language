#!/usr/bin/env python3
"""
Quick verification.wav WER test with proper Somali Latin script configuration
"""
import os
import argparse
import torch
import soundfile as sf
from transformers import WhisperProcessor, WhisperForConditionalGeneration

try:
    from text_normalize import normalize_text
except ModuleNotFoundError:
    import sys
    sys.path.append(os.path.dirname(__file__))
    from text_normalize import normalize_text


@torch.inference_mode()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", required=True)
    ap.add_argument("--ver_wav", required=True, help="Path to verification.wav")
    ap.add_argument("--language", default="somali")
    ap.add_argument("--task", default="transcribe", choices=["transcribe", "translate"])
    ap.add_argument("--num_beams", type=int, default=5)
    ap.add_argument("--output_dir", default="outputs/metrics/verification")
    ap.add_argument("--reference_text", default=None, help="Optional: reference transcription for WER calculation")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    print(f"Loading model from: {args.model_dir}")
    processor = WhisperProcessor.from_pretrained(args.model_dir)
    model = WhisperForConditionalGeneration.from_pretrained(args.model_dir).to(device)
    model.eval()

    # ========================================================================
    # CRITICAL: Configure forced_decoder_ids for Somali Latin script
    # ========================================================================
    forced_decoder_ids = processor.get_decoder_prompt_ids(language=args.language, task=args.task)
    
    tok = getattr(processor, "tokenizer", None)
    if tok is not None:
        if hasattr(tok, "set_prefix_tokens"):
            tok.set_prefix_tokens(language=args.language, task=args.task)
        else:
            try:
                tok.language = args.language
                tok.task = args.task
            except Exception:
                pass
    
    model.config.forced_decoder_ids = forced_decoder_ids
    if getattr(model, "generation_config", None) is not None:
        model.generation_config.forced_decoder_ids = forced_decoder_ids
        try:
            model.generation_config.language = args.language
            model.generation_config.task = args.task
        except Exception:
            pass
    
    print(f"[PROMPT] language={args.language} task={args.task}")
    print(f"[PROMPT] forced_decoder_ids={forced_decoder_ids}")
    # ========================================================================

    # Load audio
    print(f"\nLoading audio: {args.ver_wav}")
    audio, sr = sf.read(args.ver_wav)
    
    # Resample if needed
    if sr != 16000:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
        sr = 16000
    
    # Convert to mono if stereo
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    
    print(f"Audio: {len(audio)/sr:.2f}s @ {sr}Hz")

    # Process and generate
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to(device)
    
    print(f"\nGenerating transcription (beams={args.num_beams})...")
    pred_ids = model.generate(
        inputs,
        num_beams=args.num_beams,
        max_new_tokens=128,
        forced_decoder_ids=forced_decoder_ids,  # CRITICAL
    )
    
    pred_text = processor.batch_decode(pred_ids, skip_special_tokens=True)[0]
    
    # Save prediction
    pred_path = os.path.join(args.output_dir, "verification_pred.txt")
    with open(pred_path, "w", encoding="utf-8") as f:
        f.write(pred_text)
    
    print(f"\n{'='*70}")
    print(f"TRANSCRIPTION:")
    print(f"{'='*70}")
    print(pred_text)
    print(f"{'='*70}")
    print(f"\nSaved to: {pred_path}")
    
    # Calculate WER if reference provided
    if args.reference_text:
        def simple_wer(hyp, ref):
            hyp_norm = normalize_text(hyp)
            ref_norm = normalize_text(ref)
            hyp_words = hyp_norm.split()
            ref_words = ref_norm.split()
            
            # Simple edit distance
            dp = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
            for i in range(len(ref_words) + 1):
                dp[i][0] = i
            for j in range(len(hyp_words) + 1):
                dp[0][j] = j
            for i in range(1, len(ref_words) + 1):
                for j in range(1, len(hyp_words) + 1):
                    cost = 0 if ref_words[i-1] == hyp_words[j-1] else 1
                    dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
            
            edits = dp[len(ref_words)][len(hyp_words)]
            wer = edits / len(ref_words) if len(ref_words) > 0 else 0.0
            return wer, edits, len(ref_words)
        
        wer, edits, ref_words = simple_wer(pred_text, args.reference_text)
        
        print(f"\n{'='*70}")
        print(f"WER RESULTS:")
        print(f"{'='*70}")
        print(f"Reference: {args.reference_text}")
        print(f"Hypothesis: {pred_text}")
        print(f"\nNormalized:")
        print(f"Reference: {normalize_text(args.reference_text)}")
        print(f"Hypothesis: {normalize_text(pred_text)}")
        print(f"\nWER: {wer:.4f} ({edits} edits / {ref_words} words)")
        print(f"{'='*70}")
        
        # Save results
        results = {
            "reference": args.reference_text,
            "hypothesis": pred_text,
            "reference_normalized": normalize_text(args.reference_text),
            "hypothesis_normalized": normalize_text(pred_text),
            "wer": float(wer),
            "edits": edits,
            "ref_words": ref_words,
        }
        
        import json
        results_path = os.path.join(args.output_dir, "verification_results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {results_path}")


if __name__ == "__main__":
    main()