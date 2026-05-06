# AI Commands And Optional Backends

## ImageEditPlan Rules

LLM providers parse natural language into validated JSON. They do not mutate pixels or call exporters directly.

Supported local-first task families include:

- `batch_export_layers`
- `resize_layer`
- `rename_layer`
- `extract_target`
- `extract_multiple_targets`
- `remove_background`
- `refine_mask`
- `export_project`
- `export_for_ue_umg`
- `create_background_layer`
- `create_shadow_layer`
- `detect_text_regions`
- `future_psd_export`

Unknown or unimplemented tasks should return warnings or NotImplemented-style results, never crash the app.

## Mock Provider Expectations

MockLLMProvider must work offline and parse common Chinese commands, including:

- `把所有图层导出 512x512`
- `把当前选中图层导出 256、512、1024 三套尺寸`
- `把人物、武器、背景分别导出`
- `提取左边的人物`
- `把 logo 单独抠出来`
- `把文字区域识别出来`
- `只导出可见图层`
- `清理图层边缘白边`
- `把所有图层导出成 UE UMG 可以用的资源`
- `按 PSD 分层思路导出素材包`

## Optional Backend Rules

OpenAI/OpenAI-compatible providers:

- Read API keys from environment or user settings only.
- Fall back to Mock when SDK/key/config is missing.
- Ask before uploading images; text planning alone must not imply image upload.

Model backends:

- `OpenCVSegmenter` is the reliable local baseline.
- `RembgSegmenter`, `SAM2Segmenter`, `GroundingDINODetector`, `OCRDetector`, and `BiRefNetRefiner` must check availability.
- Missing packages, weights, or settings should produce warnings and fallback behavior.

## Privacy Defaults

Default settings:

- no image upload.
- cloud image editing disabled.
- cloud LLM planning disabled unless enabled.
- API keys excluded from projects, git, and installer.
