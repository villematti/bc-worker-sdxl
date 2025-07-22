# RunPod Registry Workaround Strategy

## 🚨 Current Situation
RunPod's image registry has persistent upload failures. The builds complete successfully but fail during the final upload phase.

## 🎯 Immediate Solution: Deploy SDXL-Only

### Step 1: Use Temporary Files
Replace these files in your RunPod build:

1. **Dockerfile** → Use `Dockerfile.sdxl-only`
2. **handler.py** → Use `handler_sdxl_only.py` 
3. **requirements.txt** → Use `requirements-sdxl-only.txt`
4. **download_weights.py** → Use `download_weights_sdxl_only.py`

### Step 2: Deploy Strategy

```bash
# In RunPod, use these files:
Dockerfile.sdxl-only         # Much smaller build (~3GB vs ~26GB)
handler_sdxl_only.py         # SDXL functionality only
requirements-sdxl-only.txt   # No video dependencies
download_weights_sdxl_only.py # Only SDXL models
```

### Step 3: What This Gives You

✅ **Working SDXL endpoint** with:
- Text-to-Image generation
- Image-to-Image (img2img)
- Inpainting
- All SDXL quality and features

❌ **Temporarily disabled:**
- Wan2.1 video generation (returns helpful error message)

## 🔄 Full Integration Later

Once RunPod fixes their registry issues (or we find a workaround), you can:

1. Switch back to the full integration files
2. Re-enable video generation
3. Get both SDXL + Wan2.1 functionality

## 📊 File Differences

### Original Integration (23GB+ build)
```
handler.py              # Full SDXL + Wan2.1
download_weights.py     # Downloads 23GB+ models
requirements.txt        # Video dependencies included
```

### Temporary SDXL-Only (3GB build)
```
handler_sdxl_only.py          # SDXL only, video gracefully disabled
download_weights_sdxl_only.py # Only SDXL models (~3GB)
requirements-sdxl-only.txt    # No video dependencies
```

## 🚀 Benefits of This Approach

1. **Get your endpoint running NOW** instead of fighting RunPod issues
2. **Smaller builds** = more reliable uploads
3. **All existing SDXL functionality** preserved
4. **Easy upgrade path** when registry is fixed
5. **Professional error handling** for video requests

## 📝 Usage During Transition

### What Works (SDXL):
```json
{
  "input": {
    "task_type": "text2img",
    "prompt": "A beautiful landscape, masterpiece",
    "height": 1024,
    "width": 1024
  }
}
```

### What Returns Helpful Message:
```json
{
  "input": {
    "task_type": "text2video",  // Returns informative error
    "prompt": "A cat walking"
  }
}
```

Response:
```json
{
  "error": "Video generation temporarily disabled due to RunPod registry issues. SDXL image generation is available.",
  "info": "Wan2.1-T2V will be re-enabled once RunPod resolves their upload infrastructure."
}
```

## 🎯 Action Plan

1. **Deploy SDXL-only version** (should upload successfully)
2. **Get your business running** with reliable image generation
3. **Monitor RunPod status** for registry fixes
4. **Switch back to full integration** when stable

This gets you 80% of the value immediately while we wait for RunPod to fix their infrastructure! 🚀
