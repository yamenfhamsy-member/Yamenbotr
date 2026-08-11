# API Documentation

## Unified AI API Proxy
Base: `https://proxy-ai.img-api.workers.dev`

- `GET /` أو `/health`
- `GET /metrics`
- `GET /v1/models`
- `POST /v1/chat/completions`

الواجهة تستخدم `model`, `messages`, `stream`, وتضيف `enable_thinking: true` و`tools: [{type:"web_search"}]` في مساحات Qwen المناسبة. يتم تحليل SSE حتى `[DONE]`.

## Image Generation API
Base: `https://thorfin-synt-img.img-api.workers.dev`

- `GET /config`
- `GET /models`
- `POST /warm`
- `POST /prompt`

حقول `/prompt`: `model`, `prompt`, `width`, `height`, `quality`, `seed`, `style`, `negative_prompt`.

## Music Generation API
Base: `https://thorfin-music.img-api.workers.dev`

- `POST /compose`
- `POST /full-auto`
- `POST /generate-with-lyrics`
- `POST /voice-clone-generate`
- `POST /voice-upload`
- `GET /generate/jobs/:jobId`

صفحة الأغاني تستخدم `full-auto` و`generate-with-lyrics` و`voice-clone-generate`، وتستقصي حالة المهام كل 2.5 ثانية عند توفر `job_id`.

لا تضع مفاتيح سرية داخل HTML؛ في بيئة إنتاج تتطلب مفتاحاً، استخدم وسيطاً خلفياً.
