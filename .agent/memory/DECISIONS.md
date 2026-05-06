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
