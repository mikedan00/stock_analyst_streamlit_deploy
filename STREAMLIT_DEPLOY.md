# Streamlit Cloud 배포 가이드

이 폴더는 `stock_analyst_multi_llm_app`의 **Streamlit Cloud 배포 전용 버전**입니다.
로컬 모델 다운로드, CUDA, transformers 기반 추론을 포함하지 않고, HF / Anthropic / OpenAI-compatible API 호출 방식만 사용합니다.

## 1. 파일 구조

```text
stock_analyst_streamlit_deploy/
├── streamlit_app.py              # Streamlit Cloud 기본 entrypoint wrapper
├── app.py                        # 실제 Streamlit 앱
├── requirements.txt              # Cloud용 경량 의존성
├── packages.txt                  # apt 패키지 없음
├── .streamlit/
│   ├── config.toml               # 배포 테마/서버 설정
│   └── secrets.toml.example      # Streamlit Secrets 예시
├── src/
│   ├── config.py                 # .env + st.secrets 동시 지원
│   ├── orchestrator.py           # Cloud 안정화된 멀티 에이전트 오케스트레이터
│   ├── llm/router.py             # HF / Anthropic / OpenAI-compatible 라우터
│   ├── data/                     # yfinance + Google News RSS 보조 수집
│   └── agents/                   # 6개 전문 에이전트 프롬프트/클래스
└── docs/claude_agents/           # Claude Code 에이전트 원문 참조 문서
```

## 2. GitHub에 올리기

PowerShell 기준:

```powershell
cd stock_analyst_streamlit_deploy

git init
git add .
git commit -m "Deploy multi LLM stock analyst Streamlit app"

git branch -M main
git remote add origin https://github.com/사용자명/저장소명.git
git push -u origin main
```

이미 GitHub repo가 있다면 `remote add origin`의 URL만 본인 repo로 바꾸면 됩니다.

## 3. Streamlit Cloud에서 배포

1. Streamlit Cloud 접속
2. `New app` 선택
3. GitHub repo 선택
4. Branch: `main`
5. Main file path: `streamlit_app.py`
6. Advanced settings 또는 Settings > Secrets에 아래 내용을 입력

```toml
DEFAULT_PROVIDER = "huggingface"
APP_ENABLE_DATA_COLLECTOR = true
STREAMLIT_DEPLOY_MODE = "cloud"
APP_PASSWORD = "원하는_접근_비밀번호"

HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
HF_MODEL = "google/gemma-4-26B-A4B-it"

ANTHROPIC_API_KEY = "sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_ENABLE_WEB_SEARCH = false

OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4o-mini"
```

## 4. LLM 엔진별 사용법

### Hugging Face Gemma 4

```toml
DEFAULT_PROVIDER = "huggingface"
HF_TOKEN = "hf_..."
HF_MODEL = "google/gemma-4-26B-A4B-it"
```

앱 사이드바에서 `Hugging Face · HF_TOKEN · google/gemma-4-26B-A4B-it`를 선택합니다.

주의:
- Hugging Face 계정에서 Gemma 모델 라이선스 동의가 필요할 수 있습니다.
- 선택한 Inference Provider가 해당 모델을 지원해야 합니다.
- Provider 미지원이면 앱에 오류 메시지가 표시됩니다.

### Anthropic Claude

```toml
DEFAULT_PROVIDER = "anthropic"
ANTHROPIC_API_KEY = "sk-ant-api03-..."
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_ENABLE_WEB_SEARCH = false
```

`ANTHROPIC_ENABLE_WEB_SEARCH=true`는 계정/모델에서 지원될 때만 켜세요.
Streamlit Cloud에서는 비용과 지연시간을 줄이기 위해 기본값을 `false`로 두었습니다.

### OpenAI-compatible API

```toml
DEFAULT_PROVIDER = "openai_compatible"
OPENAI_API_KEY = "sk-..."
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4o-mini"
```

OpenRouter / DeepInfra / Together / vLLM 서버 등도 `OPENAI_BASE_URL`과 모델명만 바꾸면 사용할 수 있습니다.

## 5. 배포판에서 보강한 점

- `st.secrets` 지원 추가: Streamlit Cloud Secrets에서 API Key 자동 로드
- 비밀번호 게이트 추가: `APP_PASSWORD`로 공개 앱 사용 제한 가능
- API Key 비노출: Secrets 값은 입력창에 직접 표시하지 않음
- Cloud 모드 저장 정책: `STREAMLIT_DEPLOY_MODE="cloud"`일 때 서버 디스크 저장 생략
- 병렬 에이전트 안정화: worker thread 안에서 Streamlit UI를 직접 호출하지 않도록 수정
- `streamlit_app.py` 추가: Streamlit Cloud main file path로 바로 지정 가능
- `.streamlit/config.toml` 추가: 다크 터미널 스타일 테마 고정
- `requirements.txt` 경량화: CUDA, transformers, torch 미포함

## 6. 자주 발생하는 오류

### `HF_TOKEN이 비어 있습니다`

Streamlit Cloud > App > Settings > Secrets에 `HF_TOKEN`이 들어갔는지 확인하세요.
로컬에서는 `.env`에 넣으면 됩니다.

### Hugging Face `model_not_supported` 또는 provider 오류

모델 ID, 라이선스 동의, Inference Provider 활성화 여부를 확인하세요.
이 경우 같은 앱에서 Anthropic 또는 OpenAI-compatible Provider로 전환해 테스트할 수 있습니다.

### Streamlit Cloud에서 앱이 재시작됨

LLM 응답이 너무 길거나 동시 병렬 호출이 오래 걸리는 경우가 있습니다.
사이드바에서 `max_tokens`를 2500~3500, 병렬 에이전트 수를 1~2로 낮춰보세요.

### 공개 앱에서 API 비용이 걱정됨

`APP_PASSWORD`를 반드시 설정하세요.
비워두면 앱이 공개됩니다.
