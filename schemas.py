INPUT_SCHEMA = {
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
        'constraints': lambda x: x in [480, 720]  # 1.3B model supports both
    },
    'video_width': {
        'type': int,
        'required': False,
        'default': 704,  # Optimized for 1.3B model
        'constraints': lambda x: x in [704, 832, 1280]  # 704x480, 832x480, or 1280x720
    },
    'num_frames': {
        'type': int,
        'required': False,
        'default': 25,  # Optimized default for 1.3B model
        'constraints': lambda x: 16 <= x <= 81  # Reasonable range for 1.3B
    },
    'video_guidance_scale': {
        'type': float,
        'required': False,
        'default': 6.0,  # Recommended for 1.3B model
        'constraints': lambda x: 1.0 <= x <= 20.0
    },
    'fps': {
        'type': int,
        'required': False,
        'default': 8,  # Standard fps for video generation
        'constraints': lambda x: 6 <= x <= 30
    },
}
