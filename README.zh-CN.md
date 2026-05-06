# AI Image Layer Extractor

AI Image Layer Extractor 是一个本地桌面 MVP 工具，用于从 AI 生成的扁平 PNG/JPG/WEBP 图片中提取可编辑的透明 PNG 图层。

当前 MVP 使用：

- PySide6 构建桌面 UI
- OpenCV GrabCut 根据矩形框选生成 mask
- Pillow 负责图片读写和透明 PNG 导出
- numpy 负责 mask 和数组处理

本项目同时支持源码运行流程和 Windows 安装版流程。

## 安装版使用方式

下载或构建：

```text
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

然后：

1. 双击 `AIImageLayerExtractor_Setup_0.1.0_x64.exe`。
2. 如需桌面快捷方式，保持桌面快捷方式选项勾选。
3. 从桌面快捷方式或开始菜单快捷方式启动程序。

安装程序使用当前用户目录作为安装目录：

```text
%LOCALAPPDATA%/Programs/AI Image Layer Extractor
```

已安装的应用会把用户数据存放在安装目录之外：

```text
%LOCALAPPDATA%/AIImageLayerExtractor/
+-- logs/
+-- config/
+-- cache/
+-- exports/
```

卸载应用只会删除程序文件，不会删除用户数据目录。

## 开发版运行方式

需要 Python 3.10+。

```powershell
cd C:\ML\EditImage\ai_image_layer_extractor
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

如果 PowerShell 执行策略阻止激活脚本，可以像上面一样直接调用 `.venv` 中的 Python。

安装测试和打包工具：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -B -m pytest
```

## Windows PySide6 DLL 说明

本项目固定使用：

```text
PySide6==6.7.3
```

在当前机器上，`PySide6==6.11.0` 会出现 Qt DLL 加载错误。如果你看到：

```text
ImportError: DLL load failed while importing QtWidgets
```

请重新安装固定版本：

```powershell
.\.venv\Scripts\python.exe -m pip install --force-reinstall PySide6==6.7.3
```

## 基本工作流

1. 点击 `Open Image` 加载 PNG、JPG、JPEG 或 WEBP 图片。
2. 在画布上按住鼠标左键拖拽，框选一个元素。
3. 松开鼠标后生成半透明 mask 预览。
4. 点击 `Create Layer` 将当前 mask 保存为图层。
5. 在右侧面板中重命名、显示/隐藏、删除或导出图层。
6. 点击 `Export All` 导出图层、mask、`project.json` 和 `preview.png`。

画布操作：

- 鼠标滚轮：缩放
- 鼠标右键或中键拖拽：平移
- `Fit View`：让图片适配视口

## 导出结构

```text
Export/
+-- layers/
|   +-- 001_layer_name.png
|   +-- ...
+-- masks/
|   +-- 001_layer_name_mask.png
|   +-- ...
+-- project.json
+-- preview.png
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

图层 PNG 和 mask PNG 会裁剪到 bbox。JSON 坐标用于把每个图层恢复到原始画布位置。

## 打包

参见：

```text
packaging/README_PACKAGING.md
```

一键构建：

```powershell
.\packaging\scripts\build_all.ps1
```

输出：

```text
dist/AIImageLayerExtractor/
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

## 项目结构

```text
ai_image_layer_extractor/
+-- main.py
+-- launcher.py
+-- version.py
+-- requirements.txt
+-- requirements-dev.txt
+-- README.md
+-- app/
+-- core/
+-- segmenters/
+-- tests/
+-- packaging/
```

## 后续扩展

1. SAM2 点选/框选分割。
2. rembg 背景移除。
3. OCR 文字图层检测。
4. PSD 导出。
5. Unreal Engine UMG 布局 JSON 导出。
6. UE Python Texture2D 自动导入。
