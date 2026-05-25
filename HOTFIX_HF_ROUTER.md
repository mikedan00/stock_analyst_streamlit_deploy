# HF Router Hotfix

이 버전은 Hugging Face 호출을 legacy `api-inference.huggingface.co`가 아니라 현재 Inference Providers Router인 `https://router.huggingface.co/v1`로 보냅니다.

Streamlit Secrets 예시:

```toml
DEFAULT_PROVIDER = "huggingface"
HF_TOKEN = "hf_xxx"
HF_MODEL = "google/gemma-4-26B-A4B-it"
HF_BASE_URL = "https://router.huggingface.co/v1"
# 모델이 특정 provider에서만 열리는 경우 입력: novita / deepinfra / together 등
HF_PROVIDER_SUFFIX = ""
```

앱 사이드바에서도 HF Router Base URL과 Provider suffix를 입력할 수 있습니다.
