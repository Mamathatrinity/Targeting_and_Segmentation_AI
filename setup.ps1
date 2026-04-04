# Setup Script for AI Testing Agent
# Run this to set up your development environment

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "AI Testing Agent - Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "1. Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "2. Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "   ⚠ Virtual environment already exists" -ForegroundColor Yellow
} else {
    python -m venv .venv
    Write-Host "   ✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "3. Activating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1
Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "4. Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "   ✓ pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "5. Installing dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ⚠ requirements.txt not found" -ForegroundColor Yellow
}

# Install Playwright browsers
Write-Host ""
Write-Host "6. Installing Playwright browsers..." -ForegroundColor Yellow
playwright install chromium
Write-Host "   ✓ Playwright browsers installed" -ForegroundColor Green

# Create .env file
Write-Host ""
Write-Host "7. Setting up environment file..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "   ✓ .env file created from template" -ForegroundColor Green
        Write-Host "   ⚠ IMPORTANT: Edit .env and add your Azure credentials!" -ForegroundColor Yellow
    } else {
        @"
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Langfuse (Optional)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
"@ | Out-File -FilePath .env -Encoding utf8
        Write-Host "   ✓ .env file created" -ForegroundColor Green
        Write-Host "   ⚠ IMPORTANT: Edit .env and add your Azure credentials!" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠ .env file already exists" -ForegroundColor Yellow
}

# Create necessary directories
Write-Host ""
Write-Host "8. Creating directories..." -ForegroundColor Yellow
$dirs = @("reports", "learning_data", "examples")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "   ✓ Created $dir/" -ForegroundColor Green
    }
}

# Run health check
Write-Host ""
Write-Host "9. Running health check..." -ForegroundColor Yellow
python -m ai_agent.health_check

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Edit .env file and add your Azure GPT-4o credentials"
Write-Host "  2. Run: python main.py --url 'https://example.com'"
Write-Host "  3. Check reports/ folder for results"
Write-Host ""
