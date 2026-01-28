#!/bin/bash
set -e

echo "=================================================="
echo "OME Hackathon Season 14 - Project Setup"
echo "=================================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ uv installed successfully"
else
    echo "✅ uv is already installed"
fi

# Check if ty is installed
if ! command -v ty &> /dev/null; then
    echo "📦 Installing ty (type checker)..."
    curl -LsSf https://astral.sh/ty/install.sh | sh
    echo "✅ ty installed successfully"
else
    echo "✅ ty is already installed"
fi

# Check if ruff is installed
if ! command -v ruff &> /dev/null; then
    echo "📦 Installing ruff (linter & formatter)..."
    curl -LsSf https://astral.sh/ruff/install.sh | sh
    echo "✅ ruff installed successfully"
else
    echo "✅ ruff is already installed"
fi

echo ""
echo "🔧 Setting up Python project with uv..."
echo ""

# Initialize uv project if needed
if [ ! -f "pyproject.toml" ]; then
    echo "📝 Initializing uv project..."
    uv init
fi

# Sync project dependencies
echo "📚 Installing project dependencies..."
uv sync

echo ""
echo "✅ Project setup complete!"
echo ""
echo "=================================================="
echo "Next steps:"
echo "=================================================="
echo ""
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Run the dataset exploration:"
echo "   uv run python dataset/explore.py"
echo ""
echo "3. Lint and format code (optional):"
echo "   ruff check ."
echo "   ruff format ."
echo ""
echo "4. Check type errors (optional):"
echo "   ty check"
echo ""
echo "5. Start Docker services:"
echo "   docker compose up --build inference"
echo ""
echo "⚠️  Note: ML libraries (setfit, transformers) require Python 3.11-3.12"
echo "   Current Python version: $(python3 --version)"
echo ""
