# 📊 주식 애널리스트 AI · Streamlit Cloud Deploy Edition

Claude Code 스타일의 6개 서브에이전트 구조를 Streamlit 앱으로 구현한 주식 분석 프로그램입니다.

## 핵심 기능

- 기업 개요 / 재무 분석 / 산업 분석 / 모멘텀 분석 / 리스크 분석 / 종합 추천
- Phase 1 병렬 실행 + Phase 2~4 순차 합성
- Hugging Face `HF_TOKEN` + `google/gemma-4-26B-A4B-it` 선택 지원
- Anthropic API 선택 지원
- OpenAI-compatible API 선택 지원
- yfinance 가격 데이터 + Google News RSS 보조 컨텍스트
- Streamlit Cloud Secrets 지원
- 공개 배포용 `APP_PASSWORD` 보호 옵션

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # Windows: copy .env.example .env
streamlit run app.py
```

## Streamlit Cloud 배포

Streamlit Cloud의 main file path는 다음으로 지정하세요.

```text
streamlit_app.py
```

자세한 배포 단계는 [`STREAMLIT_DEPLOY.md`](STREAMLIT_DEPLOY.md)를 보세요.

## Secrets 예시

`.streamlit/secrets.toml.example` 내용을 Streamlit Cloud의 Secrets 입력창에 붙여넣고 실제 키로 바꾸세요.

```toml
DEFAULT_PROVIDER = "huggingface"
APP_ENABLE_DATA_COLLECTOR = true
STREAMLIT_DEPLOY_MODE = "cloud"
APP_PASSWORD = "change-this-password"

HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
HF_MODEL = "google/gemma-4-26B-A4B-it"
```

## 주의

본 앱은 투자 리서치 보조 도구입니다. 매수·매도 판단 전 공시, 재무제표, 증권사 리포트, 실시간 시세를 별도로 확인하세요.
