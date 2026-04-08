#!/bin/bash
# Run script for OpenEnv Email Triage

set -e

echo "🚀 Starting OpenEnv Email Triage v2.0"
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Create static directory if it doesn't exist
if [ ! -d "static" ]; then
    echo "📁 Creating static directory..."
    mkdir -p static
fi

# Run the application
echo ""
echo "🌐 Starting server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📧 OpenEnv Email Triage is running!"
echo ""
echo "🌐 Frontend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "📖 ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
