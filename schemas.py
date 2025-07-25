# ============================================================================
# UNIFIED INPUT SCHEMA - HANDLES ALL TASK TYPES
# ============================================================================

INPUT_SCHEMA = {
    'prompt': {
        'type': str,
        'required': True,  # Fixed: prompt should be required
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
    'refiner_inference_steps': {
        'type': int,
        'required': False,
        'default': 50,
        'constraints': lambda x: 10 <= x <= 100
    },
    'guidance_scale': {
        'type': float,
        'required': False,
        'default': 7.5,
        'constraints': lambda x: 1.0 <= x <= 20.0
    },
    'strength': {
        'type': float,
        'required': False,
        'default': 0.3,
        'constraints': lambda x: 0.1 <= x <= 1.0
    },
    
    # LEGACY PARAMETER (accepted but ignored for compatibility)
    'num_images': {
        'type': int,
        'required': False,
        'default': 1,
        'constraints': lambda x: x == 1  # Only accept 1, since we always generate 1 image
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
    'high_noise_frac': {
        'type': float,
        'required': False,
        'default': None,
        'constraints': lambda x: x is None or (0.0 <= x <= 1.0)
    },
    'task_type': {
        'type': str,
        'required': False,
        'default': 'text2img',
        'constraints': lambda x: x in ['text2img', 'img2img', 'inpaint', 'text2video']
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
    # VIDEO PARAMETERS (for text2video task_type only)
    'video_height': {
        'type': int,
        'required': False,
        'default': 480,  # Fixed: all videos are 480P
    },
    'video_width': {
        'type': int,
        'required': False,
        'default': 832,  # Fixed: all videos are 832 width
    },
    'num_frames': {
        'type': int,
        'required': False,
        'default': None,  # Only set for video requests - NO DEFAULT!
        'constraints': lambda x: x is None or (16 <= x <= 81)
    },
    'video_guidance_scale': {
        'type': float,
        'required': False,
        'default': 5.0,  # Fixed: recommended value from docs
    },
    'fps': {
        'type': int,
        'required': False,
        'default': 15,  # Fixed: all videos are 15 FPS
    },
}
