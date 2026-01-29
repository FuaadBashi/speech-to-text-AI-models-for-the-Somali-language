# Install system dependencies
!apt-get update -qq && apt-get install -y ffmpeg

# Install Python packages
!pip install -q datasets==2.19.0 transformers==4.44.2 accelerate==0.34.2 \
    evaluate==0.4.2 soundfile librosa jiwer sentencepiece scipy

# Create directory structure
import os
os.makedirs("outputs/verification", exist_ok=True)
os.makedirs("outputs/checkpoints", exist_ok=True)
os.makedirs("outputs/final_model", exist_ok=True)

print("✅ Environment ready!")
print("📁 Directory structure created")