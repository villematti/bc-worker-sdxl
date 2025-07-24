# 🐛 CRITICAL BUG FIX: Image Requests Routed to Video Pipeline

## 🚨 The Problem

Your image generation requests were being incorrectly routed to the **video generation pipeline** instead of the **SDXL image pipeline**. This happened because:

### Root Cause Analysis

1. **Schema Default Issue**: In `schemas.py`, the `num_frames` field had a default value of `81`:
   ```python
   'num_frames': {
       'default': 81,  # ← This was the problem!
   }
   ```

2. **Routing Logic**: The handler used this logic to determine request type:
   ```python
   task_type = "text2video" if job_input.get("num_frames") else "text2image"
   ```

3. **The Bug**: Even for image requests (like your Yorkshire Terrier), the schema validator automatically added `num_frames: 81`, making `job_input.get("num_frames")` return `81` instead of `None`.

4. **Result**: ALL requests were routed to video generation, explaining why you saw:
   - Video parameters in the logs (`video_height`, `video_width`, `num_frames`, etc.)
   - Firestore updates to `/videos/` collection instead of `/images/`
   - Wan2.1 pipeline being triggered for image requests

## ✅ The Fix

### 1. Updated Schema (`schemas.py`)
```python
# BEFORE (caused the bug)
'num_frames': {
    'default': 81,  # Always set, even for images!
    'constraints': lambda x: 16 <= x <= 81
}

# AFTER (fixed)
'num_frames': {
    'default': None,  # Don't default for image requests
    'constraints': lambda x: x is None or (16 <= x <= 81)  # Allow None
}
```

### 2. Improved Routing Logic (`handler.py`)
```python
# BEFORE (ambiguous)
task_type = "text2video" if job_input.get("num_frames") else "text2image"

# AFTER (explicit)
num_frames = job_input.get("num_frames")
is_video_request = num_frames is not None and num_frames > 0
task_type = "text2video" if is_video_request else "text2image"
```

### 3. Added Debug Logging
```python
print(f"[Background] Request type: {task_type} (num_frames: {num_frames})")
```

## 🎯 Verified Results

✅ **Image Requests** (`task_type: "text2img"`, no `num_frames`)
- `num_frames: None`
- `is_video_request: False` 
- `task_type: "text2image"`
- `media_type: "images"`
- **Routes to SDXL pipeline** ← CORRECT!

✅ **Video Requests** (`task_type: "text2video"`, with `num_frames: 81`)
- `num_frames: 81`
- `is_video_request: True`
- `task_type: "text2video"`
- `media_type: "videos"`  
- **Routes to Wan2.1 pipeline** ← CORRECT!

## 📋 Files Modified

1. **`schemas.py`** - Fixed `num_frames` default and constraints
2. **`handler.py`** - Improved routing logic in multiple places
3. **Added test scripts** - To verify the fix works

## 🚀 What This Fixes

- ✅ Your Yorkshire Terrier image request will now use **SDXL image generation**
- ✅ Firestore updates will go to `/images/` collection (not `/videos/`)
- ✅ No more video parameters in image generation logs
- ✅ Proper task type detection (`text2image` vs `text2video`)
- ✅ Video requests still work correctly when `num_frames` is explicitly provided

## 🔧 Testing

The fix has been verified with test scripts showing:
- Image requests correctly route to SDXL
- Video requests correctly route to Wan2.1
- Schema constraints work properly
- No syntax errors in modified code

## 🎉 Impact

This critical fix ensures that:
1. **Image generation works as expected** using SDXL models
2. **Video generation still works** when explicitly requested  
3. **No more confusion** between request types
4. **Proper database updates** to correct collections
5. **Better debugging** with explicit logging

Your Yorkshire Terrier image request should now work perfectly! 🐕
