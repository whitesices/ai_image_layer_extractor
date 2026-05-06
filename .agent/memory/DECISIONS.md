# Decisions

Record durable engineering decisions here.

## 2026-05-06 Agentic Engineering System

- Created `.agent/` as the repository-local operating system for future Codex work.
- Guardrails are mandatory for every task.
- Feature work follows: Intention -> Specification -> Implementation Plan -> Task Breakdown -> Tests First -> Implementation -> Local Validation -> Review -> Documentation -> Memory Update.
- No business code was changed for the initial agentic engineering setup.
- Required baseline validation remains `python -B -m pytest`.
