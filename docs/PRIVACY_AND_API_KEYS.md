# Privacy and API Keys

Defaults:

- No image upload.
- Cloud image editing disabled.
- Cloud LLM text planning disabled unless the user opts in.
- Mock LLM provider works offline.
- API keys are never bundled into the installer.

OpenAI key lookup order:

1. `OPENAI_API_KEY` environment variable.
2. User settings file only if explicitly saved.

User settings live under:

```text
%LOCALAPPDATA%/AIImageLayerExtractor/config/settings.json
```

Do not commit real `settings.json` files or API keys.

