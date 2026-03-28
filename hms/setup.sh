#!/bin/bash
# Quick Setup Script for HMS AI/ML System

echo "======================================"
echo "HMS AI/ML System - Quick Setup"
echo "======================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if pip is installed
if command -v pip &> /dev/null; then
    echo "✓ pip found"
else
    echo "✗ pip not found. Please install pip."
    exit 1
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set up your API key:"
echo "   export ANTHROPIC_API_KEY='your-key-here'"
echo ""
echo "2. Train all models:"
echo "   python hms/ml/model_trainer.py --train-all"
echo ""
echo "3. Test a single model:"
echo "   python hms/ml/disease_predictor.py"
echo ""
echo "4. Start with AI modules:"
echo "   python hms/ai/symptom_chatbot.py"
echo ""
echo "For more information, see README.md"
