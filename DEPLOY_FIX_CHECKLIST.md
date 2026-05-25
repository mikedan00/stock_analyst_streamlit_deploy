# Streamlit Cloud Blank Screen Fix Checklist

## 핵심 원인
GitHub에 올라간 `app.py`, `streamlit_app.py`, `requirements.txt`가 줄바꿈 없이 한 줄로 깨지면 Streamlit Cloud에서 빈 화면이 발생할 수 있습니다.

## 반드시 확인할 파일
- `app.py`: 여러 줄 Python 코드여야 합니다.
- `streamlit_app.py`: 여러 줄 앱 코드여야 합니다. 단순 `from app import *` 래퍼가 아니어야 합니다.
- `requirements.txt`: 패키지 하나당 한 줄이어야 합니다.
- `packages.txt`: 없어야 합니다.

## Streamlit Cloud 설정
- Main file path: `streamlit_app.py`
- Python version: Advanced settings에서 `3.11` 선택

## GitHub Push 후 확인
브라우저에서 아래 raw 파일을 열어 줄바꿈이 보이는지 확인하세요.
- `https://raw.githubusercontent.com/<계정>/<저장소>/main/requirements.txt`
- `https://raw.githubusercontent.com/<계정>/<저장소>/main/app.py`
- `https://raw.githubusercontent.com/<계정>/<저장소>/main/streamlit_app.py`
