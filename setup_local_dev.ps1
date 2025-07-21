# SDXL Worker Local Development Setup Script
# Run this in PowerShell to set up local development environment

Write-Host "🚀 Setting up SDXL Worker local development environment..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if CUDA is available (optional but recommended)
try {
    $nvidiaSmi = nvidia-smi 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ NVIDIA GPU detected" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ No NVIDIA GPU detected - will use CPU (slower)" -ForegroundColor Yellow
}

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Blue
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, removing old one..."
    Remove-Item -Recurse -Force venv
}

python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Blue
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "📈 Upgrading pip..." -ForegroundColor Blue
python -m pip install --upgrade pip

# Install PyTorch first (with CUDA support if available)
Write-Host "🔥 Installing PyTorch..." -ForegroundColor Blue
try {
    $nvidiaSmi = nvidia-smi 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Installing PyTorch with CUDA support..."
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
    } else {
        Write-Host "Installing PyTorch CPU version..."
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    }
} catch {
    Write-Host "Installing PyTorch CPU version (fallback)..."
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
}

# Install development requirements
Write-Host "📚 Installing development dependencies..." -ForegroundColor Blue
pip install -r requirements-dev.txt

# Download a minimal model for testing (just the tokenizer/text encoder)
Write-Host "📥 Downloading minimal models for testing..." -ForegroundColor Blue
python -c @"
import torch
from transformers import CLIPTokenizer, CLIPTextModel
print('Downloading CLIP text encoder for basic testing...')
tokenizer = CLIPTokenizer.from_pretrained('openai/clip-vit-large-patch14')
text_encoder = CLIPTextModel.from_pretrained('openai/clip-vit-large-patch14')
print('✅ Basic models downloaded')
"@

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Activate the environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Test your changes: python test_local.py" -ForegroundColor White
Write-Host "3. Run quick validation: python -c `"import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())`"" -ForegroundColor White
Write-Host ""
Write-Host "For full model testing, you'll need to download the actual SDXL models:" -ForegroundColor Yellow
Write-Host "python download_weights.py" -ForegroundColor White
Write-Host "(Warning: This downloads ~13GB of models)" -ForegroundColor Red
