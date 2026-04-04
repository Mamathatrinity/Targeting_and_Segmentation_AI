#!/bin/bash
# Setup Script for AI Testing Agent (Linux/Mac)

set -e

echo "======================================"
echo "AI Testing Agent - Setup"
echo "======================================"
echo ""

# Check Python version
echo "1. Checking Python version..."
if command -v python3 &> /dev/null; then
    python3 --version
    echo "   ✓ Python found"
else
    echo "   ✗ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment
echo ""
echo "2. Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "   ⚠ Virtual environment already exists"
else
    python3 -m venv .venv
    echo "   ✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "3. Activating virtual environment..."
source .venv/bin/activate
echo "   ✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "4. Upgrading pip..."
pip install --upgrade pip --quiet
echo "   ✓ pip upgraded"

# Install dependencies
echo ""
echo "5. Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo "   ✓ Dependencies installed"
else
    echo "   ⚠ requirements.txt not found"
fi

# Install Playwright browsers
echo ""
echo "6. Installing Playwright browsers..."
playwright install chromium
echo "   ✓ Playwright browsers installed"

# Create .env file
echo ""
echo "7. Setting up environment file..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✓ .env file created from template"
        echo "   ⚠ IMPORTANT: Edit .env and add your Azure credentials!"
    else
        cat > .env << 'EOF'
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Langfuse (Optional)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
EOF
        echo "   ✓ .env file created"
        echo "   ⚠ IMPORTANT: Edit .env and add your Azure credentials!"
    fi
else
    echo "   ⚠ .env file already exists"
fi

# Create necessary directories
echo ""
echo "8. Creating directories..."
for dir in reports learning_data examples; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "   ✓ Created $dir/"
    fi
done

# Run health check
echo ""
echo "9. Running health check..."
python -m ai_agent.health_check

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next Steps:"
echo "  1. Edit .env file and add your Azure GPT-4o credentials"
echo "  2. Run: python main.py --url 'https://example.com'"
echo "  3. Check reports/ folder for results"
echo ""
