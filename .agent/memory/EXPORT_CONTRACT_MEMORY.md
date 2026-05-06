# Export Contract Memory

Default export must remain backward-compatible:

```text
Export/
+-- layers/
+-- masks/
+-- project.json
+-- preview.png
```

Each layer in `project.json` must include:

- `id`
- `name`
- `visible`
- `file`
- `mask`
- `x`
- `y`
- `width`
- `height`
- `opacity`
- `blend_mode`

Layer and mask PNGs are bbox-cropped. JSON `x`, `y`, `width`, and `height` restore placement on the original canvas.

Additive metadata is allowed in extra files such as `batch_report.json`, UE data assets, or PSD-compatible package notes.
