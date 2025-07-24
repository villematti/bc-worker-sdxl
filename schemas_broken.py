# ============================================================================
# SEPARATE SCHEMAS FOR EACH PIPELINE - NO MIXING!
# ============================================================================

# Base common parameters for all image-related tasks
IMAGE_BASE_SCHEMA = {
    'prompt': {
        'type': str,
        'required': True,
    },
    'negative_prompt': {
        'type': str,
        'required': False,
        'default': None
    },
    'height': {
        'type': int,
        'required': False,
        'default': 1024,
        'constraints': lambda x: x in [512, 768, 1024, 1152, 1344, 1536]
    },
    'width': {
        'type': int,
        'required': False,
        'default': 1024,
        'constraints': lambda x: x in [512, 768, 1024, 1152, 1344, 1536]
    },
    'seed': {
        'type': int,
        'required': False,
        'default': None
    },
    'scheduler': {
        'type': str,
        'required': False,
        'default': 'DDIM',
        'constraints': lambda x: x in ['PNDM', 'KLMS', 'DDIM', 'K_EULER', 'DPMSolverMultistep', 'K_EULER_ANCESTRAL', 'DPMSolverSinglestep']
    },
    'num_inference_steps': {
        'type': int,
        'required': False,
        'default': 25,
        'constraints': lambda x: 10 <= x <= 100
    },
    'guidance_scale': {
        'type': float,
        'required': False,
        'default': 7.5,
        'constraints': lambda x: 1.0 <= x <= 20.0
    },
    'num_images': {
        'type': int,
        'required': False,
        'default': 1,
        'constraints': lambda img_count: 1 <= img_count <= 3
    },
    # Cloud storage and database integration
    'user_id': {
        'type': str,
        'required': False,
        'default': None
    },
    'file_uid': {
        'type': str,
        'required': False,
        'default': None
    },
    'use_cloud_storage': {
        'type': bool,
        'required': False,
        'default': False
    },
}

# 1. TEXT-TO-IMAGE SCHEMA (SDXL Base + Refiner)
TEXT2IMG_SCHEMA = {
    **IMAGE_BASE_SCHEMA,
    'task_type': {
        'type': str,
        'required': False,
        'default': 'text2img',
        'constraints': lambda x: x == 'text2img'
    },
    'refiner_inference_steps': {
        'type': int,
        'required': False,
        'default': 50,
        'constraints': lambda x: 10 <= x <= 100
    },
    'high_noise_frac': {
        'type': float,
        'required': False,
        'default': None,
        'constraints': lambda x: x is None or (0.0 <= x <= 1.0)
    },
}

# 2. IMAGE-TO-IMAGE SCHEMA (SDXL Refiner)
IMG2IMG_SCHEMA = {
    **IMAGE_BASE_SCHEMA,
    'task_type': {
        'type': str,
        'required': False,
        'default': 'img2img',
        'constraints': lambda x: x == 'img2img'
    },
    'image_url': {
        'type': str,
        'required': True,  # Required for img2img
    },
    'strength': {
        'type': float,
        'required': False,
        'default': 0.3,
        'constraints': lambda x: 0.1 <= x <= 1.0
    },
    'refiner_inference_steps': {
        'type': int,
        'required': False,
        'default': 50,
        'constraints': lambda x: 10 <= x <= 100
    },
}

# 3. INPAINTING SCHEMA (SDXL Inpaint)
INPAINT_SCHEMA = {
    **IMAGE_BASE_SCHEMA,
    'task_type': {
        'type': str,
        'required': False,
        'default': 'inpaint',
        'constraints': lambda x: x == 'inpaint'
    },
    'image_url': {
        'type': str,
        'required': True,  # Required for inpainting
    },
    'mask_url': {
        'type': str,
        'required': True,  # Required for inpainting
    },
}

# 4. TEXT-TO-VIDEO SCHEMA (Wan2.1 T2V)
TEXT2VIDEO_SCHEMA = {
    'prompt': {
        'type': str,
        'required': True,
    },
    'negative_prompt': {
        'type': str,
        'required': False,
        'default': None
    },
    'task_type': {
        'type': str,
        'required': False,
        'default': 'text2video',
        'constraints': lambda x: x == 'text2video'
    },
    'seed': {
        'type': int,
        'required': False,
        'default': None
    },
    # VIDEO-SPECIFIC PARAMETERS ONLY
    'video_height': {
        'type': int,
        'required': False,
        'default': 480,
        'constraints': lambda x: x in [480, 720]
    },
    'video_width': {
        'type': int,
        'required': False,
        'default': 832,
        'constraints': lambda x: x in [832, 1280]
    },
    'num_frames': {
        'type': int,
        'required': False,
        'default': 81,
        'constraints': lambda x: 16 <= x <= 81
    },
    'video_guidance_scale': {
        'type': float,
        'required': False,
        'default': 5.0,
        'constraints': lambda x: 1.0 <= x <= 20.0
    },
    'fps': {
        'type': int,
        'required': False,
        'default': 15,
        'constraints': lambda x: 6 <= x <= 30
    },
    # Cloud storage and database integration
    'user_id': {
        'type': str,
        'required': False,
        'default': None
    },
    'file_uid': {
        'type': str,
        'required': False,
        'default': None
    },
    'use_cloud_storage': {
        'type': bool,
        'required': False,
        'default': False
    },
}

# ============================================================================
# LEGACY UNIFIED SCHEMA (DEPRECATED - FOR BACKWARD COMPATIBILITY ONLY)
# ============================================================================
    'prompt': {
        'type': str,
        'required': False,
    },
    'negative_prompt': {
        'type': str,
        'required': False,
        'default': None
    },
    'height': {
        'type': int,
        'required': False,
        'default': 1024
    },
    'width': {
        'type': int,
        'required': False,
        'default': 1024
    },
    'seed': {
        'type': int,
        'required': False,
        'default': None
    },
    'scheduler': {
        'type': str,
        'required': False,
        'default': 'DDIM'
    },
    'num_inference_steps': {
        'type': int,
        'required': False,
        'default': 25
    },
    'refiner_inference_steps': {
        'type': int,
        'required': False,
        'default': 50
    },
    'guidance_scale': {
        'type': float,
        'required': False,
        'default': 7.5
    },
    'strength': {
        'type': float,
        'required': False,
        'default': 0.3
    },
    'image_url': {
        'type': str,
        'required': False,
        'default': None
    },
    'mask_url': {
        'type': str,
        'required': False,
        'default': None
    },
    'num_images': {
        'type': int,
        'required': False,
        'default': 1,
        'constraints': lambda img_count: 3 > img_count > 0
    },
    'high_noise_frac': {
        'type': float,
        'required': False,
        'default': None
    },
    # Video generation parameters for Wan2.1-T2V-14B
    'task_type': {
        'type': str,
        'required': False,
        'default': 'text2img',
        'constraints': lambda x: x in ['text2img', 'img2img', 'inpaint', 'text2video']
    },
    'video_height': {
        'type': int,
        'required': False,
        'default': 480,
        'constraints': lambda x: x in [480, 720]  # 1.3B model supports both (720p less stable)
    },
    'video_width': {
        'type': int,
        'required': False,
        'default': 832,  # Official default for 1.3B model
        'constraints': lambda x: x in [832, 1280]  # 832x480 or 1280x720
    },
    'num_frames': {
        'type': int,
        'required': False,
        'default': None,  # Don't set default - let it be None for image generation
        'constraints': lambda x: x is None or (16 <= x <= 81)  # Allow None or valid range
    },
    'video_guidance_scale': {
        'type': float,
        'required': False,
        'default': 5.0,  # Official default for 1.3B model
        'constraints': lambda x: 1.0 <= x <= 20.0
    },
    'fps': {
        'type': int,
        'required': False,
        'default': 15,  # Official default for video export
        'constraints': lambda x: 6 <= x <= 30
    },
    # Cloud storage and database integration
    'user_id': {
        'type': str,
        'required': False,
        'default': None
    },
    'file_uid': {
        'type': str,
        'required': False,
        'default': None
    },
    'use_cloud_storage': {
        'type': bool,
        'required': False,
        'default': False
    },
}
