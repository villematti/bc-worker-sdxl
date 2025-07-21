# Simple Local Development Setup
# Step-by-step setup that's easier to debug

Write-Host "🚀 Setting up SDXL Worker local development environment..." -ForegroundColor Green

# Step 1: Check Python
Write-Host "`n=== Step 1: Checking Python ===" -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Step 2: Check/Create virtual environment
Write-Host "`n=== Step 2: Setting up virtual environment ===" -ForegroundColor Cyan
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists" -ForegroundColor Yellow
    $response = Read-Host "Remove and recreate? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Removing old virtual environment..." -ForegroundColor Blue
        Remove-Item -Recurse -Force venv
    }
}

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Blue
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Step 3: Activate virtual environment
Write-Host "`n=== Step 3: Activating virtual environment ===" -ForegroundColor Cyan
$activateScript = ".\venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Blue
    & $activateScript
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "❌ Activation script not found: $activateScript" -ForegroundColor Red
    exit 1
}

# Step 4: Upgrade pip
Write-Host "`n=== Step 4: Upgrading pip ===" -ForegroundColor Cyan
python -m pip install --upgrade pip
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ pip upgraded successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️ pip upgrade had issues, continuing..." -ForegroundColor Yellow
}

# Step 5: Install basic dependencies
Write-Host "`n=== Step 5: Installing basic dependencies ===" -ForegroundColor Cyan
Write-Host "Installing torch, diffusers, and PIL..." -ForegroundColor Blue

# Install torch first
$torchInstalled = $false
try {
    # Try CUDA version first
    Write-Host "Trying to install PyTorch with CUDA support..." -ForegroundColor Blue
    python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
    if ($LASTEXITCODE -eq 0) {
        $torchInstalled = $true
        Write-Host "✅ PyTorch with CUDA installed" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ CUDA version failed, trying CPU version..." -ForegroundColor Yellow
}

if (-not $torchInstalled) {
    Write-Host "Installing PyTorch CPU version..." -ForegroundColor Blue
    python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PyTorch CPU installed" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install PyTorch" -ForegroundColor Red
        exit 1
    }
}

# Install other key dependencies
Write-Host "Installing diffusers and PIL..." -ForegroundColor Blue
python -m pip install diffusers pillow transformers accelerate
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Core dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install core dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 Basic setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Test installation: python validate_changes.py" -ForegroundColor White
Write-Host "2. For full testing: python download_weights.py" -ForegroundColor White
Write-Host "3. Run tests: python test_local.py" -ForegroundColor White
