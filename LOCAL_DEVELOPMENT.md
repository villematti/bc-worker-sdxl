# Local Development Setup for SDXL Worker

This guide helps you test your SDXL Worker changes locally before pushing to production.

## Quick Setup

### 1. Run the Setup Script
```powershell
# In PowerShell, navigate to your project directory
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser  # Allow script execution
.\setup_local_dev.ps1
```

### 2. Activate Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Quick Validation (No Model Download)
```powershell
python validate_changes.py
```

This will check:
- ✅ Code structure and imports
- ✅ Schema validation
- ✅ Dependency installation
- ✅ SDXL inpainting model references

## Full Testing (with Models)

### 1. Download Models (~13GB)
```powershell
# This downloads all SDXL models including the new inpainting model
python download_weights.py
```

### 2. Run Local Tests
```powershell
# Test basic functionality without RunPod
python test_local.py
```

## What Changed for SDXL Inpainting

### ✅ Model Change
- **Old**: `kandinsky-community/kandinsky-2-2-decoder-inpaint`
- **New**: `diffusers/stable-diffusion-xl-1.0-inpainting-0.1`

### ✅ Key Differences
1. **Better Quality**: SDXL-based inpainting vs Kandinsky
2. **Consistency**: All models now use SDXL architecture
3. **Parameters**: Uses same VAE and settings as base/refiner models

### ✅ Updated Files
- `handler.py` - Updated `load_inpaint()` method
- `download_weights.py` - Updated model download path
- `test_input.json` - Can now test inpainting with `mask_url`

## Testing Different Scenarios

### Text-to-Image (Basic)
```json
{
  "input": {
    "prompt": "a beautiful landscape",
    "height": 512,
    "width": 512,
    "num_inference_steps": 5
  }
}
```

### Inpainting (New Feature)
```json
{
  "input": {
    "prompt": "a red flower",
    "image_url": "data:image/png;base64,...",
    "mask_url": "data:image/png;base64,...",
    "height": 512,
    "width": 512,
    "num_inference_steps": 20,
    "strength": 0.99
  }
}
```

### Image-to-Image (Existing)
```json
{
  "input": {
    "prompt": "make it more colorful",
    "image_url": "data:image/png;base64,...",
    "height": 512,
    "width": 512,
    "strength": 0.7
  }
}
```

## Troubleshooting

### Import Errors
```powershell
# Reinstall dependencies
pip install -r requirements-dev.txt
```

### CUDA Issues
```powershell
# Check CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# If no CUDA, models will run on CPU (slower but works)
```

### Memory Issues
- Reduce image size: `"height": 512, "width": 512`
- Reduce steps: `"num_inference_steps": 5`
- Close other applications

### Model Download Fails
- Check internet connection
- May need HuggingFace token for some models
- Set environment variable: `$env:HUGGINGFACE_TOKEN="your_token"`

## Deployment Checklist

Before pushing to production:

- [ ] `python validate_changes.py` passes ✅
- [ ] `python test_local.py` runs without errors ✅
- [ ] Text-to-image works ✅
- [ ] Inpainting works with new SDXL model ✅
- [ ] No references to old Kandinsky model ✅
- [ ] Dockerfile builds successfully ✅

## Performance Notes

### Expected Improvements
- **Better Inpainting Quality**: SDXL vs Kandinsky
- **Consistent Style**: All operations use SDXL
- **Better Integration**: Same VAE across all pipelines

### Expected Behavior
- **First Run**: Slower (model loading)
- **Subsequent Runs**: Faster (models cached)
- **Memory Usage**: Similar to before
- **Quality**: Significantly better inpainting results

## Next Steps

Once local testing passes:
1. Build Docker image locally (optional)
2. Push changes to your repository
3. Deploy to RunPod
4. Test in production environment

The local testing should catch 90% of issues before deployment!
