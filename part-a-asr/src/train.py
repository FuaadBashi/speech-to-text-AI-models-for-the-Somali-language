"""Fine-tune Whisper for Somali ASR (skeleton).

Recommended approach:
  - Bulk train on skydheere/soomali-asr-dataset (train split), validate on validation split.
  - Optional short domain adaptation on FLEURS Somali train split (NOT validation/test).

This file is intentionally a skeleton to keep the scaffold lightweight.
Implement using the HF Whisper fine-tuning recipe:
  https://huggingface.co/blog/fine-tune-whisper
"""

def main():
    raise NotImplementedError(
        "TODO: Implement fine-tuning pipeline (datasets -> processor -> seq2seq trainer)."
    )

if __name__ == "__main__":
    main()
