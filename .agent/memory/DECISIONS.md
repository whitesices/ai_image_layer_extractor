# Decisions

Record durable engineering decisions here.

## 2026-05-06 Agentic Engineering System

- Created `.agent/` as the repository-local operating system for future Codex work.
- Guardrails are mandatory for every task.
- Feature work follows: Intention -> Specification -> Implementation Plan -> Task Breakdown -> Tests First -> Implementation -> Local Validation -> Review -> Documentation -> Memory Update.
- No business code was changed for the initial agentic engineering setup.
- Required baseline validation remains `python -B -m pytest`.

## 2026-05-06 Offline AI Command Expansion

- Enhanced `MockLLMProvider` for the required Chinese AI Command Panel commands without adding any cloud service or new dependency.
- Kept OpenAI optional; UI fallback remains Mock when OpenAI SDK or API key is unavailable.
- Resolved named layer targets such as UI icons before broad words such as `全部`, so `把 UI 图标全部导出为 128x128 透明 PNG` targets icon layers instead of all layers.
- `CommandExecutor` now returns an explicit `NotImplemented` result for recognized reserved task types that do not yet have a local executor.
- Validation target: `python -B -m pytest`.

## 2026-05-06 Custom LLM Base URL

- Added `llm_base_url` to settings for OpenAI-compatible, DeepSeek-compatible, and local server providers.
- `OpenAIProvider` now reads custom base URLs from settings, `LLM_API_BASE_URL`, or `OPENAI_BASE_URL`.
- Compatible providers require a configured base URL and still fall back to Mock when SDK/key/URL is unavailable.
- No new cloud service or dependency was added.

## 2026-05-07 LLM Provider Factory Refactor

- Moved LLM provider selection, availability fallback, and status text composition into `llm/provider_factory.py`.
- `AICommandPanel` now depends on the provider factory instead of concrete Mock/OpenAI provider classes.
- Behavior is unchanged: unavailable compatible providers still fall back to offline Mock.
- Validation target: `python -B -m pytest`.

## 2026-05-07 Smart Slice Pipeline Bridge

- `MockLLMProvider` now recognizes smart slice commands that combine local extraction with batch export, for example `把图中所有人物图片元素全部输出 512x512`.
- `CommandExecutor` can execute `extract_target`, `extract_multiple_targets`, `detect_text_regions`, and `create_background_layer` through local pipelines.
- The implementation remains offline-first: Mock detector and OpenCV/local pipelines are the baseline, while SAM2/GroundingDINO/OCR remain optional future backends.
- LLM output still stops at structured `ImageEditPlan`; pixel changes are performed by local pipeline code only.
- Added tests for smart command parsing, extraction execution, text-region extraction, background layer creation, and chained extraction-to-export.
- Validation target: `python -B -m pytest`.
