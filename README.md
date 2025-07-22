![SDXL Worker Banner](https://cpjrphpz3t5wbwfe.public.blob.vercel-storage.com/worker-sdxl_banner-c7nsJLBOGHnmsxcshN7kSgALHYawnW.jpeg)

---

# SDXL + Wan2.1-T2V Multi-Modal Worker

Run [Stable Diffusion XL](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) and [Wan2.1-T2V-1.3B](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B-Diffusers) as a serverless endpoint to generate both **images** and **videos**.

---

[![RunPod](https://api.runpod.io/badge/runpod-workers/worker-sdxl)](https://www.runpod.io/console/hub/runpod-workers/worker-sdxl)

---

## 🎯 Features

- **Image Generation**: SDXL with text2img, img2img, and inpainting
- **Video Generation**: Wan2.1-T2V-1.3B for high-quality text-to-video
- **Multi-Modal**: Single endpoint supports both images and videos
- **Optimized**: 1.3B model for faster deployment (~14GB vs 33GB Docker image)
- **RunPod Ready**: Designed for 48GB VRAM serverless deployment

## 📋 Usage

### Image Generation (SDXL)

Set `task_type` to `text2img`, `img2img`, or `inpaint`:

| Parameter                 | Type    | Default  | Required  | Description                                                                                                         |
| :------------------------ | :------ | :------- | :-------- | :------------------------------------------------------------------------------------------------------------------ |
| `prompt`                  | `str`   | `None`   | **Yes\*** | The main text prompt describing the desired image.                                                                  |
| `negative_prompt`         | `str`   | `None`   | No        | Text prompt specifying concepts to exclude from the image                                                           |
| `height`                  | `int`   | `1024`   | No        | The height of the generated image in pixels                                                                         |
| `width`                   | `int`   | `1024`   | No        | The width of the generated image in pixels                                                                          |
| `seed`                    | `int`   | `None`   | No        | Random seed for reproducibility. If `None`, a random seed is generated                                              |
| `scheduler`               | `str`   | `'DDIM'` | No        | The noise scheduler to use. Options include `PNDM`, `KLMS`, `DDIM`, `K_EULER`, `DPMSolverMultistep`                 |
| `num_inference_steps`     | `int`   | `25`     | No        | Number of denoising steps for the base model                                                                        |
| `refiner_inference_steps` | `int`   | `50`     | No        | Number of denoising steps for the refiner model                                                                     |
| `guidance_scale`          | `float` | `7.5`    | No        | Classifier-Free Guidance scale. Higher values lead to images closer to the prompt, lower values more creative       |
| `strength`                | `float` | `0.3`    | No        | The strength of the noise added when using an `image_url` for image-to-image or refinement                          |
| `image_url`               | `str`   | `None`   | No        | URL of an initial image to use for image-to-image generation (runs only refiner). If `None`, performs text-to-image |
| `num_images`              | `int`   | `1`      | No        | Number of images to generate per prompt (Constraint: must be 1 or 2)                                                |
| `high_noise_frac`         | `float` | `None`   | No        | Fraction of denoising steps performed by the base model (e.g., 0.8 for 80%). `denoising_end` for base               |

### Video Generation (Wan2.1-T2V-1.3B)

Set `task_type` to `text2video`:

| Parameter                 | Type    | Default  | Required  | Description                                                                                                         |
| :------------------------ | :------ | :------- | :-------- | :------------------------------------------------------------------------------------------------------------------ |
| `task_type`               | `str`   | `None`   | **Yes**   | Set to `"text2video"` for video generation                                                                          |
| `prompt`                  | `str`   | `None`   | **Yes**   | Text description of the desired video content                                                                       |
| `negative_prompt`         | `str`   | `None`   | No        | Text prompt specifying concepts to exclude from the video                                                           |
| `video_height`            | `int`   | `480`    | No        | Video height in pixels (480 or 720 supported)                                                                       |
| `video_width`             | `int`   | `704`    | No        | Video width in pixels (704, 832, or 1280 supported)                                                                 |
| `num_frames`              | `int`   | `25`     | No        | Number of frames to generate (16-81 range, 25 optimal for 1.3B)                                                     |
| `video_guidance_scale`    | `float` | `6.0`    | No        | Guidance scale for video generation (1.0-20.0 range, 6.0 optimal for 1.3B)                                         |
| `fps`                     | `int`   | `8`      | No        | Frames per second for output video (6-30 range)                                                                     |
| `num_inference_steps`     | `int`   | `25`     | No        | Number of denoising steps for video generation                                                                      |
| `seed`                    | `int`   | `None`   | No        | Random seed for reproducibility                                                                                     |

> [!NOTE]  
> `prompt` is required unless `image_url` is provided

### Example Requests

#### Image Generation (SDXL)

```json
{
  "input": {
    "task_type": "text2img",
    "prompt": "A majestic steampunk dragon soaring through a cloudy sky, intricate clockwork details, golden hour lighting, highly detailed",
    "negative_prompt": "blurry, low quality, deformed, ugly, text, watermark, signature",
    "height": 1024,
    "width": 1024,
    "num_inference_steps": 25,
    "refiner_inference_steps": 50,
    "guidance_scale": 7.5,
    "strength": 0.3,
    "high_noise_frac": 0.8,
    "seed": 42,
    "scheduler": "K_EULER",
    "num_images": 1
  }
}
```

#### Video Generation (Wan2.1-T2V-1.3B)

```json
{
  "input": {
    "task_type": "text2video",
    "prompt": "A cat playing with a ball of yarn, fluffy and cute, smooth motion",
    "negative_prompt": "blurry, distorted, ugly, static, low quality",
    "video_height": 480,
    "video_width": 704,
    "num_frames": 25,
    "video_guidance_scale": 6.0,
    "fps": 8,
    "num_inference_steps": 25,
    "seed": 42
  }
}
```

which is producing an output like this:

```json
{
  "delayTime": 11449,
  "executionTime": 6120,
  "id": "447f10b8-c745-4c3b-8fad-b1d4ebb7a65b-e1",
  "output": {
    "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABAAAAAQACAIAAADwf7zU...",
    "images": [
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABAAAAAQACAIAAADwf7zU..."
    ],
    "seed": 42
  },
  "status": "COMPLETED",
  "workerId": "462u6mrq9s28h6"
}
```

and when you convert the base64-encoded image into an actual image, it looks like this:

<img src="https://cpjrphpz3t5wbwfe.public.blob.vercel-storage.com/worker-sdxl_output_1-AedTpZlz1eIwIgAEShlod6syLo6Jq6.jpeg" alt="SDXL Generated Image: 'A majestic steampunk dragon soaring through a cloudy sky, intricate clockwork details, golden hour lighting, highly detailed'" width="512" height="512">

## 🚀 Deployment Optimizations

### Wan2.1 Model Selection

This worker uses the **1.3B model** instead of the 14B model for optimal deployment:

| Aspect              | 14B Model          | 1.3B Model ✅      | Improvement |
| :------------------ | :----------------- | :----------------- | :---------- |
| Model Size          | ~23GB              | ~8GB               | **65% smaller** |
| Docker Image        | ~33GB              | ~14GB              | **58% smaller** |
| Upload Time         | 3+ hours           | ~45 minutes        | **4x faster** |
| Cold Start          | Slower             | Faster             | **Better UX** |
| Video Quality       | Highest            | High               | **Good balance** |
| VRAM Usage          | Higher             | Lower              | **More efficient** |

### Environment Variables

- `DOWNLOAD_WAN2_MODEL=true` - Enable video generation (set to `false` to disable)
- `HF_HOME=/runpod-volume` - Cache models on persistent storage
- `TRANSFORMERS_CACHE=/runpod-volume` - Cache transformers on persistent storage

### Supported Resolutions

**1.3B Model Optimizations:**
- **480p**: 704x480 (optimal), 832x480 (compatible)  
- **720p**: 1280x720 (high quality)
- **Frames**: 16-81 supported, 25 recommended for speed
- **Guidance**: 6.0 optimal (vs 7.5+ for 14B)
