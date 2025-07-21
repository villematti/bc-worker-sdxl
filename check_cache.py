import os

cache_dir = r'C:\Users\ville\.cache\huggingface\hub'
total_size = 0

for root, dirs, files in os.walk(cache_dir):
    for file in files:
        file_path = os.path.join(root, file)
        if os.path.exists(file_path):
            total_size += os.path.getsize(file_path)

print(f'Current HuggingFace cache size: {total_size / (1024**3):.2f} GB')

# List model directories
print('\nCached models:')
for item in os.listdir(cache_dir):
    if item.startswith('models--'):
        model_path = os.path.join(cache_dir, item)
        if os.path.isdir(model_path):
            model_size = 0
            for root, dirs, files in os.walk(model_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        model_size += os.path.getsize(file_path)
            print(f'  - {item}: {model_size / (1024**3):.2f} GB')
