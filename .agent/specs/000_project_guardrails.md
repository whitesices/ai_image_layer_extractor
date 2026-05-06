# Project Guardrails

These rules are hard constraints for every Codex task in AI Image Layer Extractor.

## Non-Negotiable Files And Modes

- Do not delete `main.py`.
- Do not delete `launcher.py`.
- Do not break source mode: `python main.py`.
- Do not break installer mode: `launcher.py`, PyInstaller onedir output, and Inno Setup installer.
- Do not break the default export contract:
  - `Export/layers/`
  - `Export/masks/`
  - `Export/project.json`
  - `Export/preview.png`

## Security And Privacy

- Do not hardcode API keys.
- Do not store real API keys in repository files.
- Do not bundle API keys into the installer.
- Do not upload user images by default.
- Without an API key, the application must remain usable offline.
- Cloud image editing must be opt-in and must ask before uploading images.

## Optional AI Backends

- Missing SAM2, GroundingDINO, rembg, OCR, OpenAI SDK, model weights, or API keys must not crash startup.
- Advanced models must remain optional backends.
- Every optional backend must report availability and fallback safely.

## LLM And Pixel Safety

- LLM providers may only generate structured plans such as `ImageEditPlan`.
- LLM providers must not directly modify pixels, masks, project state, or files.
- Pixel and mask changes must run through local, testable Python pipelines.
- UI code must not directly depend on concrete model implementations.

## Engineering Quality

- New features must include tests.
- Bug fixes should include regression tests when feasible.
- Each task must finish by running:

```powershell
python -B -m pytest
```

- If GUI tests are needed in a headless environment, use `QT_QPA_PLATFORM=offscreen` smoke tests.
- Do not refactor unrelated code while completing a task.
- Do not change export metadata fields unless the change is backward-compatible.
