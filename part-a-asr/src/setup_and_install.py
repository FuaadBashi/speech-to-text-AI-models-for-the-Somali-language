# Install system and Python dependencies.
#
# This was a notebook cell using Jupyter "!" shell syntax, which is not Python: main.py failed with
# a SyntaxError before running any step. It now runs the same commands through subprocess.
import os
import shutil
import subprocess
import sys

if shutil.which("ffmpeg") is None:
    if shutil.which("apt-get") is None:
        sys.exit("ffmpeg is required: install it with your package manager, then re-run.")
    subprocess.run(["apt-get", "update", "-qq"], check=True)
    subprocess.run(["apt-get", "install", "-y", "ffmpeg"], check=True)

subprocess.run(
    [
        sys.executable, "-m", "pip", "install", "-q",
        "datasets==2.19.0", "transformers==4.44.2", "accelerate==0.34.2", "evaluate==0.4.2",
        "soundfile", "librosa", "jiwer", "sentencepiece", "scipy",
    ],
    check=True,
)  # fmt: skip

# Create directory structure

os.makedirs("outputs/verification", exist_ok=True)
os.makedirs("outputs/checkpoints", exist_ok=True)
os.makedirs("outputs/final_model", exist_ok=True)

print("✅ Environment ready!")
print("📁 Directory structure created")
