# AI Image Layer Extractor

AI Image Layer Extractor 是一个本地桌面 MVP，用来把 AI image2image / text2image 生成的扁平 PNG、JPG、WEBP 图片，按用户框选区域抠成带透明通道的独立 PNG 图层，并记录每个图层在原图中的坐标信息。

第一版重点保证最小可运行：PySide6 桌面 UI、OpenCV GrabCut + 手动框选 mask、Pillow 导出透明 PNG、JSON 项目元数据。SAM2、rembg、OCR、PSD 和 UE 导入接口已预留。

## 安装

需要 Python 3.10+。

```powershell
cd C:\ML\EditImage\ai_image_layer_extractor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果本机 PowerShell 禁止执行激活脚本，也可以直接使用：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## 运行

```powershell
cd C:\ML\EditImage\ai_image_layer_extractor
python main.py
```

## 使用流程

1. 点击 `Open Image` 导入 PNG / JPG / WEBP 图片。
2. 在画布中用鼠标左键拖拽框选元素区域。
3. 松开鼠标后，程序会生成半透明 mask 预览。
4. 点击 `Create Layer`，当前 mask 会保存为一个图层。
5. 在右侧 `Layers` 面板中重命名、显示/隐藏、删除或单独导出图层。
6. 点击 `Export All` 导出所有图层、mask、`project.json` 和 `preview.png`。

画布操作：

- 鼠标滚轮缩放。
- 鼠标右键或中键拖动画布平移。
- `Fit View` 将图片适配回窗口。

## 导出结构

```text
Export/
├── layers/
│   ├── 001_layer_name.png
│   └── ...
├── masks/
│   ├── 001_layer_name_mask.png
│   └── ...
├── project.json
└── preview.png
```

`project.json` 示例：

```json
{
  "source_image": "input.png",
  "canvas": {
    "width": 1448,
    "height": 1086
  },
  "layers": [
    {
      "id": "001",
      "name": "character",
      "visible": true,
      "file": "layers/001_character.png",
      "mask": "masks/001_character_mask.png",
      "x": 120,
      "y": 350,
      "width": 280,
      "height": 420,
      "opacity": 1.0,
      "blend_mode": "normal"
    }
  ]
}
```

图层 PNG 和 mask PNG 都按 bbox 裁剪；`x`、`y`、`width`、`height` 用于还原到原始画布坐标。

## 项目结构

```text
ai_image_layer_extractor/
├── main.py
├── requirements.txt
├── README.md
├── app/
│   ├── main_window.py
│   ├── canvas_widget.py
│   ├── layer_panel.py
│   └── export_dialog.py
├── core/
│   ├── project.py
│   ├── layer.py
│   ├── mask_utils.py
│   ├── image_utils.py
│   └── exporter.py
├── segmenters/
│   ├── base_segmenter.py
│   ├── opencv_segmenter.py
│   ├── rembg_segmenter.py
│   └── sam2_segmenter.py
└── tests/
    ├── test_mask_utils.py
    └── test_exporter.py
```

## 测试

```powershell
cd C:\ML\EditImage\ai_image_layer_extractor
pytest
```

## 当前 MVP 能力

- 导入 PNG / JPG / WEBP。
- 中央画布显示图片。
- 支持缩放、平移、鼠标框选。
- 框选后用 OpenCV GrabCut 生成初步 mask，并进行连通域清理、轻微膨胀和羽化。
- 手动确认创建图层。
- 根据 mask 生成带透明通道的 PNG。
- 自动计算 bbox。
- 右侧图层列表支持重命名、显示/隐藏、删除、单独导出。
- 一键导出全部图层、mask、项目 JSON 和预览图。

## 后续扩展方向

1. 接入 SAM2 点选/框选分割，在 `segmenters/sam2_segmenter.py` 中实现模型加载、prompt 输入和多 mask 选择。
2. 接入 rembg 背景移除，在 `segmenters/rembg_segmenter.py` 中实现前景 alpha 输出。
3. 接入 OCR 识别文字图层，并把文字内容、字体候选、bbox 写入 `project.json`。
4. 导出 PSD，可新增 `core/psd_exporter.py`，把每个 LayerItem 转为 PSD layer。
5. 导出 UE UMG 布局 JSON，复用 `x/y/width/height/opacity` 元数据。
6. UE Python 自动导入 Texture2D，生成 Widget Blueprint 或 UMG 层级。
