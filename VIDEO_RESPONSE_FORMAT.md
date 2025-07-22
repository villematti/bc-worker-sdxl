# Video Generation Response Format

When you send a `text2video` request, your worker will return a response like this:

## ✅ Successful Video Generation Response

```json
{
  "video_url": "https://your-bucket.s3.amazonaws.com/job-id/video.mp4",
  "video_info": {
    "frames": 81,
    "width": 1280,
    "height": 720,
    "fps": 15,
    "duration_seconds": 5.4
  },
  "seed": 42
}
```

## 📊 Response Fields Explained

- **`video_url`**: Direct URL to the generated MP4 video file
- **`video_info`**: Metadata about the generated video
  - `frames`: Total number of frames generated
  - `width/height`: Actual video resolution
  - `fps`: Frame rate used
  - `duration_seconds`: Calculated video length
- **`seed`**: The seed used for generation (for reproducibility)

## 🔄 Comparison with Image Response

### Video Response (task_type: "text2video")
```json
{
  "video_url": "https://...",
  "video_info": { ... },
  "seed": 42
}
```

### Image Response (task_type: "text2img")
```json
{
  "images": ["https://..."],
  "image_url": "https://...",
  "seed": 42
}
```

## ❌ Error Response Format

If video generation fails:

```json
{
  "error": "Video generation error: CUDA out of memory",
  "refresh_worker": true
}
```

## 🎯 Key Differences from Image Generation

1. **Response Structure**: Videos return `video_url` instead of `image_url`
2. **File Format**: MP4 video file instead of PNG images
3. **Generation Time**: Videos take longer (5-15 minutes vs 1-3 minutes)
4. **File Size**: Videos are larger (10-100MB vs 1-5MB)
5. **Additional Metadata**: Frame count, duration, fps information
