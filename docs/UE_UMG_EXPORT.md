# UE UMG Export

UE export writes:

```text
Export_UE/
+-- Textures/
|   +-- T_layer_name.png
+-- Masks/
|   +-- M_layer_name.png
+-- Data/
|   +-- DA_LayerExtractResult.json
|   +-- ue_import_config.json
+-- Scripts/
|   +-- import_to_unreal.py
```

`DA_LayerExtractResult.json` records canvas coordinates, texture paths, mask
paths, z-order, opacity, and suggested UMG slot placement.

`import_to_unreal.py` is designed to run inside Unreal Editor Python. It imports
PNG textures and writes `ue_import_report.json`. Full Widget Blueprint creation
is reserved for a later extension.

