# Pre-Implementation Checklist

- [ ] Read `.agent/specs/000_project_guardrails.md`.
- [ ] Read the task file or user request.
- [ ] Run `git status --short`.
- [ ] Identify affected layers: `app`, `core`, `llm`, `segmenters`, `detectors`, `matting`, `pipeline`, `exporters`, `packaging`, `tests`.
- [ ] Confirm allowed and disallowed files.
- [ ] Confirm whether export contract is affected.
- [ ] Confirm whether privacy/API key/cloud upload behavior is affected.
- [ ] Confirm optional dependency fallback behavior.
- [ ] Decide tests to add or update before coding.
