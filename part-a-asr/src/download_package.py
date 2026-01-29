# ============================================================================
# FIXED DOWNLOAD SCRIPT - Copy this entire cell
# ============================================================================

import shutil
from google.colab import files
import os
import json

print("="*80)
print("📦 PREPARING DOWNLOAD PACKAGE")
print("="*80)

# Check what files exist
files_created = []

if os.path.exists("outputs/verification/verification.wav"):
    size_mb = os.path.getsize("outputs/verification/verification.wav") / (1024**2)
    files_created.append(f"✓ verification.wav ({size_mb:.1f} MB)")

if os.path.exists("outputs/verification/verification_manifest.json"):
    with open("outputs/verification/verification_manifest.json", "r") as f:
        manifest = json.load(f)
    num_segments = len(manifest.get('segments', []))
    files_created.append(f"✓ verification_manifest.json ({num_segments} segments)")

# Check for any evaluation results file
eval_files = [
    "outputs/verification/evaluation_results.json",
    "outputs/verification/evaluation_results_FIXED.json",
    "outputs/verification/detailed_evaluation_all_segments.json",
]

wer_val = None
for eval_file in eval_files:
    if os.path.exists(eval_file):
        with open(eval_file, "r") as f:
            results = json.load(f)

        # Try different possible WER field names
        if 'wer_full' in results:
            wer_val = results['wer_full']
        elif 'overall_wer' in results:
            wer_val = results['overall_wer']
        elif 'wer_metrics' in results:
            wer_val = results['wer_metrics'].get('wer_full')
        elif 'wer' in results:
            wer_val = results['wer']

        if wer_val is not None:
            files_created.append(f"✓ {os.path.basename(eval_file)} (WER: {wer_val*100:.1f}%)")
            break

if os.path.exists("outputs/verification/detailed_evaluation_all_segments.csv"):
    files_created.append(f"✓ detailed_evaluation_all_segments.csv")

if os.path.exists("outputs/verification/full_comparison_all_129_segments.txt"):
    files_created.append(f"✓ full_comparison_all_129_segments.txt")

print("\n📁 Files available for download:")
for f in files_created:
    print(f"  {f}")

# Create zip archive
print("\n🗜️  Creating zip archive...")
archive_name = "somali_asr_verification_results"
shutil.make_archive(archive_name, "zip", "outputs/verification")
print(f"✓ Created {archive_name}.zip")

# Get file size
zip_size = os.path.getsize(f"{archive_name}.zip") / (1024**2)
print(f"  Size: {zip_size:.1f} MB")

# Display final summary
if wer_val is not None:
    print("\n" + "="*80)
    print("🎯 FINAL SUMMARY")
    print("="*80)
    print(f"  Verification WER: {wer_val*100:.2f}%")
    print(f"  Target: ≤ 20%")

    if wer_val <= 0.20:
        print(f"\n  🎉 ✅ TARGET ACHIEVED!")
        print(f"  Your Somali ASR model is production-ready!")
    else:
        print(f"\n  ⚠️  Target not met")
    print("="*80)

# Download
print("\n⬇️  Starting download...")
files.download(f"{archive_name}.zip")
print("✅ Download complete!")

print("\n" + "="*80)
print("📋 CONTENTS OF ZIP FILE:")
print("="*80)
print("  • verification.wav - 5-minute audio clip")
print("  • verification_manifest.json - 129 segments with timestamps")
print("  • evaluation_results.json - WER metrics")
print("  • detailed_evaluation_all_segments.json - Full TP/FP/FN stats")
print("  • detailed_evaluation_all_segments.csv - Excel-ready data")
print("  • full_comparison_all_129_segments.txt - All REF vs HYP")
print("="*80)
print("\n✅ NOTEBOOK EXECUTION COMPLETE")
print("="*80)