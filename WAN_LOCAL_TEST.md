# Wan2.1 Local Testing on 6GB VRAM

## ⚠️ VRAM Limitations
Your 6GB VRAM is quite tight for the 14B Wan model, but we can try with optimizations:

## 🧪 Test Script: `test_wan_local.py`

### Memory Optimizations Applied:
- **Model CPU Offloading**: Keeps models on CPU when not in use
- **Attention Slicing**: Reduces memory usage during attention computation  
- **VAE Slicing**: Processes video frames in smaller batches
- **Reduced Resolution**: Uses 320x480 instead of 832x480
- **Fewer Frames**: 25 frames instead of 81 for low VRAM
- **Fewer Steps**: 15 inference steps instead of 20

### Usage:
```powershell
# Activate your virtual environment
.\venv\Scripts\Activate.ps1

# Set HuggingFace token (if you have one)
$env:HUGGINGFACE_TOKEN = "hf_your_token_here"

# Install required packages
pip install --upgrade diffusers transformers accelerate

# Run the test
python test_wan_local.py
```

## 🎯 Expected Outcomes:

### ✅ Best Case (6GB might work):
- Model loads with CPU offloading
- Generates 25-frame 320x480 video
- Takes 10-15 minutes on your system
- Proves Wan2.1 integration is viable

### ⚠️ Likely Case (6GB insufficient):
- Out of memory during model loading
- Fallback to CPU-only (very slow) 
- Or fails completely

### 🚀 Recommended Approach:
Since 6GB is borderline, I'd suggest:

1. **Try the test script** - it might work with heavy optimizations
2. **If it fails locally**, test directly on your **48GB RunPod instance**
3. **Integrate into your SDXL worker** where you have plenty of VRAM

## 🔧 Alternative: CPU-Only Test
If GPU fails, we can modify the script to run CPU-only (very slow but proves functionality):

```python
pipe = pipe.to("cpu")  # Force CPU mode
```

## 💡 Why Test Locally?
Even if it's slow/limited on 6GB, local testing helps:
- Verify the code integration works
- Test API changes before RunPod deployment  
- Avoid 3-hour RunPod feedback cycles
- Debug any import/dependency issues

Ready to try it? Run `python test_wan_local.py` and see what happens! 🎬
