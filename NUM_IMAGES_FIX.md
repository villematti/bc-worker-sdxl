# 🔧 num_images Parameter Fix - RESOLVED

## ❌ **What Was Happening**

The Firebase team was sending requests with `num_images: 1`, but our schema was **rejecting** it:

```json
{
  "errors": [
    "Unexpected input. num_images is not a valid input option."
  ]
}
```

**Error Details:**
- Request contained: `"num_images": 1`
- Our schema didn't include `num_images` as a valid parameter
- RunPod's `validate()` function **rejects any unknown parameters**
- Result: 400 Bad Request error

## ✅ **Solution Applied**

### **1. Added num_images to Schema**
```python
# In schemas.py - added this parameter:
'num_images': {
    'type': int,
    'required': False,
    'default': 1,
    'constraints': lambda x: x == 1  # Only accept 1, since we always generate 1 image
},
```

### **2. Marked as Legacy Parameter**
- **Accepted**: Firebase can send it without errors
- **Ignored**: We don't actually use it (always generate 1 image)
- **Constrained**: Only allows `num_images: 1` (our actual behavior)

### **3. Updated Documentation**
Added section in INPUT_OUTPUT_GUIDE.md:
```markdown
### **Legacy Parameters (Accepted but Ignored):**
- **`num_images`** - Always generates 1 image (accepted for backward compatibility)
```

## 🧪 **Test Results**

The Yorkshire Terrier request that was failing:
```json
{
  "prompt": "A realistic photograph of a Yorkshire Terrier...",
  "num_images": 1,  // ✅ Now accepted!
  "height": 1024,
  "width": 1024,
  "guidance_scale": 7.5,
  "num_inference_steps": 20,
  "file_uid": "60142eab-76cf-4e21-ba84-ca230549e4c4",
  "user_id": "z9BLS15zMwc174rWKVBusQUdy5R2",
  "use_cloud_storage": true
}
```

**Validation Test:**
- ✅ All 9 parameters now valid
- ✅ `num_images: 1` accepted
- ✅ `num_images: 2` correctly rejected (we only generate 1)

## 🎯 **Why This Approach**

1. **Backward Compatibility**: Firebase team doesn't need to change their requests
2. **Future-Proof**: If we ever support multiple images, just change the constraint
3. **Clear Behavior**: Always generates exactly 1 image regardless of `num_images` value
4. **Error Prevention**: Rejects `num_images > 1` to avoid confusion

## 🚀 **Expected Behavior Now**

### **Firebase Request (Working):**
```json
{
  "task_type": "text2img",
  "prompt": "A Yorkshire Terrier in a meadow",
  "num_images": 1,  // ✅ Accepted and ignored
  "user_id": "firebase-user-id",
  "file_uid": "file-uuid",
  "use_cloud_storage": true
}
```

### **Response:**
```json
{
  "status": "success",
  "images": [
    "https://storage.googleapis.com/bc-image-gen.firebasestorage.app/generating/user123/image/file456.png"
  ],  // Always exactly 1 image
  "seed": 1234567890,
  "execution_time": 15.2
}
```

## ✅ **Fix Complete**

- ✅ **Schema updated** to accept `num_images`
- ✅ **Validation working** for Yorkshire Terrier requests  
- ✅ **Documentation updated** to explain legacy parameter
- ✅ **Test passed** confirming fix works
- ✅ **Firebase team** can continue using existing requests

**The 400 Bad Request error should be resolved! 🎉**
