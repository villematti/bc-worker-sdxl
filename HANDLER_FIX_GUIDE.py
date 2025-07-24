"""
HANDLER UPDATE - Proper Pipeline Separation

This shows how to update the handler to use separate schemas for each pipeline.
The main changes needed in handler.py:
"""

def get_proper_schema_and_validate(job_input):
    """
    Determine task type and use appropriate schema for validation
    """
    from schemas import get_schema_for_task_type
    from runpod.serverless.utils.rp_validator import validate
    
    # First, determine the task type
    task_type = job_input.get('task_type', 'text2img')
    
    # Handle special cases for task type detection
    if job_input.get('image_url') and job_input.get('mask_url'):
        task_type = 'inpaint'
    elif job_input.get('image_url') and not job_input.get('mask_url'):
        task_type = 'img2img'
    elif job_input.get('num_frames') and job_input.get('num_frames') > 0:
        task_type = 'text2video'
    else:
        task_type = 'text2img'
    
    print(f"🎯 Detected task type: {task_type}")
    
    # Get the appropriate schema
    schema = get_schema_for_task_type(task_type)
    
    # Validate with the correct schema
    validated_input = validate(job_input, schema)
    
    return validated_input, task_type

def process_with_proper_routing(job, job_input, task_type):
    """
    Process the job with proper routing based on task type
    """
    print(f"🚀 Processing {task_type} request")
    
    if task_type == 'text2video':
        return process_text2video(job, job_input)
    elif task_type == 'inpaint':
        return process_inpaint(job, job_input)
    elif task_type == 'img2img':
        return process_img2img(job, job_input)
    else:  # text2img
        return process_text2img(job, job_input)

def process_text2img(job, job_input):
    """Process text-to-image generation (SDXL Base + Refiner)"""
    print("🖼️ [TEXT2IMG] Using SDXL Base + Refiner pipeline")
    
    # Validate that no video parameters are present
    video_params = ['num_frames', 'video_height', 'video_width', 'video_guidance_scale', 'fps']
    for param in video_params:
        if job_input.get(param) is not None:
            raise ValueError(f"Video parameter '{param}' not allowed in text2img requests")
    
    # Process with SDXL pipeline...
    # (existing text2img logic)

def process_img2img(job, job_input):
    """Process image-to-image generation (SDXL Refiner)"""
    print("🔄 [IMG2IMG] Using SDXL Refiner pipeline")
    
    # Validate required parameters
    if not job_input.get('image_url'):
        raise ValueError("image_url is required for img2img")
    
    # Validate that no video parameters are present
    video_params = ['num_frames', 'video_height', 'video_width', 'video_guidance_scale', 'fps']
    for param in video_params:
        if job_input.get(param) is not None:
            raise ValueError(f"Video parameter '{param}' not allowed in img2img requests")
    
    # Process with SDXL refiner pipeline...
    # (existing img2img logic)

def process_inpaint(job, job_input):
    """Process inpainting (SDXL Inpaint)"""
    print("🎨 [INPAINT] Using SDXL Inpaint pipeline")
    
    # Validate required parameters
    if not job_input.get('image_url'):
        raise ValueError("image_url is required for inpainting")
    if not job_input.get('mask_url'):
        raise ValueError("mask_url is required for inpainting")
    
    # Validate that no video parameters are present
    video_params = ['num_frames', 'video_height', 'video_width', 'video_guidance_scale', 'fps']
    for param in video_params:
        if job_input.get(param) is not None:
            raise ValueError(f"Video parameter '{param}' not allowed in inpaint requests")
    
    # Process with SDXL inpaint pipeline...
    # (existing inpaint logic)

def process_text2video(job, job_input):
    """Process text-to-video generation (Wan2.1 T2V)"""
    print("🎥 [TEXT2VIDEO] Using Wan2.1 T2V pipeline")
    
    # Validate required parameters
    if not job_input.get('num_frames'):
        raise ValueError("num_frames is required for video generation")
    
    # Validate that no image parameters are present
    image_params = ['height', 'width', 'refiner_inference_steps', 'high_noise_frac', 'strength']
    for param in image_params:
        if job_input.get(param) is not None:
            raise ValueError(f"Image parameter '{param}' not allowed in text2video requests")
    
    # Process with Wan2.1 pipeline...
    # (existing video logic)

"""
CRITICAL CHANGES NEEDED IN HANDLER.PY:

1. Replace the current validation in generate_image():
   
   # OLD (BROKEN):
   validated_input = validate(job_input, INPUT_SCHEMA)
   
   # NEW (FIXED):
   validated_input, task_type = get_proper_schema_and_validate(job_input)

2. Replace the current routing logic:
   
   # OLD (BROKEN):
   if job_input.get("num_frames"):  # Video generation
   
   # NEW (FIXED):
   if task_type == 'text2video':

3. Add proper parameter validation in each pipeline to prevent mixing

4. Remove all video parameters from image schemas and vice versa

5. Update all database/cloud storage calls to use the correct task_type
"""
