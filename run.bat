@echo off
setlocal
cd /d "%~dp0"

echo.
echo   ==========================================
echo      Stock Analyst AI · Multi LLM Edition
echo   ==========================================
echo.

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo Created .env from .env.example. Please edit API keys if needed.
    )
)

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo Installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Starting Streamlit...
streamlit run app.py --server.port 8501 --server.headless false

pause
