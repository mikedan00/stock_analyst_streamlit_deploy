#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "=========================================="
echo "  Stock Analyst AI · Multi LLM Edition"
echo "=========================================="
echo ""

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Please edit API keys if needed."
fi

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Starting Streamlit..."
streamlit run app.py --server.port 8501 --server.headless false
