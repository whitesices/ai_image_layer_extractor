# Export Contract

The stable export contract remains:

```text
Export/
+-- layers/
+-- masks/
+-- project.json
+-- preview.png
```

Each layer entry in `project.json` keeps:

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

New metadata may be added in other files such as `batch_report.json`, but the
base export structure remains backward-compatible.

