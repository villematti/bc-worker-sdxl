# Local Docker Build Test
# Tests if your Docker image builds successfully before pushing to production

Write-Host "🐳 Testing Docker build locally..." -ForegroundColor Green

# Check if Docker is running
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found or not running" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and make sure it's running" -ForegroundColor Yellow
    exit 1
}

# Build the Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Blue
Write-Host "⚠️ This will take 10-30 minutes and download ~13GB" -ForegroundColor Yellow

$imageName = "sdxl-worker-test"

try {
    docker build -t $imageName .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker image built successfully!" -ForegroundColor Green
        
        # Show image size
        $imageInfo = docker images $imageName --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
        Write-Host "📊 Image info:" -ForegroundColor Blue
        Write-Host $imageInfo
        
        # Optional: Test run the container (requires GPU for full test)
        Write-Host ""
        Write-Host "🧪 To test the container locally:" -ForegroundColor Yellow
        Write-Host "docker run --rm --gpus all -p 8000:8000 $imageName" -ForegroundColor White
        Write-Host ""
        Write-Host "✅ Ready to push to production!" -ForegroundColor Green
        
    } else {
        Write-Host "❌ Docker build failed" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "❌ Docker build error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🧹 To clean up the test image:" -ForegroundColor Blue
Write-Host "docker rmi $imageName" -ForegroundColor White
