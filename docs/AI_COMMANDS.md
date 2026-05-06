# AI Commands

AI Command Panel converts natural language into a structured `ImageEditPlan`.
The LLM layer never edits pixels directly; execution is handled by local Python
pipelines through `CommandExecutor`.

## Offline Mock Commands

`MockLLMProvider` works without network access or API keys. It must support
these Chinese commands:

| Command | Parsed task | Notes |
| --- | --- | --- |
| `把所有图层导出 512x512` | `batch_export_layers` | target=`all_layers`, size=`512x512` |
| `把当前选中图层导出 256、512、1024 三套尺寸` | `resize_layer` | target=`selected_layers`, uses selected layer ids |
| `把所有图层加 32 像素透明边距后导出` | `batch_export_layers` | padding=`32`, transparent PNG |
| `把角色图层重命名为 player_character` | `rename_layer` | resolves character/角色 layer when possible |
| `把 UI 图标全部导出为 128x128 透明 PNG` | `batch_export_layers` | resolves icon/UI icon layers before all layers |
| `导出适合 UE UMG 使用的 512 和 1024 两套资源` | `export_for_ue_umg` | includes requested sizes and import script intent |
| `只导出可见图层` | `batch_export_layers` | target=`visible_layers` |
| `清理图层边缘白边` | `refine_mask` | local mask/alpha cleanup, no source pixel mutation |
| `优化透明边缘，减少锯齿` | `refine_mask` | edge smoothing / feather hint |
| `按 PSD 分层思路导出素材包` | `future_psd_export` | exports PSD-compatible package unless native PSD is available |

The Mock provider also recognizes extraction-oriented commands such as:

- `把人物、武器、背景分别导出`
- `提取左边的人物`
- `提取右边的道具`
- `把 logo 单独抠出来`
- `把文字区域识别出来`

These may require manual selection or optional detector backends if no bbox or
detector result is available.

## Optional OpenAI Provider

`OpenAIProvider` is optional. If the OpenAI SDK or API key is missing, the UI
falls back to `MockLLMProvider`. API keys are never hardcoded and are never
bundled into the installer.

## Reserved Task Types

Some task types are intentionally reserved for future local pipelines or
optional model backends. `CommandExecutor` must return a clear `NotImplemented`
result instead of crashing when a reserved task has no local executor yet.
