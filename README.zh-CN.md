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

## AI Command 自然语言编辑

打开 `AI > AI Command Panel`，可以用自然语言描述编辑或导出任务。LLM 层只负责生成结构化的 `ImageEditPlan`，不会直接操作像素。真正执行计划的是本地、可测试的 Python 代码。

按钮：

- `Parse`：把文本解析成编辑计划。
- `Dry Run`：预览将要执行的操作，不写入文件。
- `Execute`：确认后执行计划。
- `Clear`：清空输入和预览。

如果没有配置外部 API Key，面板会自动使用离线 `MockLLMProvider`，它可以理解常见中文批量导出和重命名指令。

示例指令：

1. `把所有图层导出 512x512`
2. `把当前选中图层导出 256、512、1024 三套尺寸`
3. `把所有图层加 32 像素透明边距后导出`
4. `把角色图层重命名为 player_character`
5. `把 UI 图标全部导出为 128x128 透明 PNG`
6. `导出适合 UE UMG 使用的 512 和 1024 两套资源`

## Batch Export 批量导出

打开 `Batch > Batch Export`，可以把全部图层或当前选中图层导出为 128x128、256x256、512x512、1024x1024 等生产尺寸。

支持的 fit mode：

- `contain`：保持比例，完整放入目标画布。
- `cover`：保持比例，填满目标画布，必要时裁切。
- `stretch`：强制拉伸到目标宽高。
- `max_side`：让最长边匹配请求尺寸。
- `original`：保持原始 bbox 尺寸。

批量导出会写入 `batch_report.json`，并在 `Export/layers/` 下生成多尺寸目录。

## Mask Tools

打开 `Mask > Mask Tools` 可以编辑当前 preview mask 或选中图层的 mask。面板包含 Brush Add、Brush Erase、Size、Feather、Expand、Shrink、Smooth、Fill Holes、Remove Islands、Undo、Redo、Apply 和 Reset。

Mask Tools 只修改 mask，不修改源图片像素。

## UE UMG 导出

AI 指令 `把所有图层导出成 UE UMG 可以用的资源` 会生成 UE 资源包：

```text
Export_UE/
+-- Textures/
+-- Masks/
+-- Data/
+-- Scripts/
```

生成的 `Scripts/import_to_unreal.py` 可在 Unreal Editor Python 中运行，用于导入 PNG 贴图。自动创建完整 UMG Widget Blueprint 是后续扩展。

## 项目包

使用 `Project > Save Project` 和 `Project > Open Project` 可以保存/打开 `.ailp` 目录包。项目包包含 `project.json`、源图、mask、图层和 preview。API Key 永远不会写入项目包。

## PSD-Compatible 导出

AI 指令 `按 PSD 分层思路导出素材包` 会导出 PSD-compatible package，包含透明图层 PNG、mask、`project.json` 和 `README_PSD_COMPATIBLE.txt`。真实 PSD 写入属于实验性后续扩展。

## LLM Provider 设置

打开 `AI > Settings` 可以选择：

- `Mock`：离线规则解析器，不需要 API Key。
- `OpenAI`：可选外部解析器，用于把自然语言转换为 `ImageEditPlan` JSON。
- `OpenAI Compatible`、`DeepSeek Compatible`、`Local Server`：未来兼容文本规划 Provider 的占位。

可选 detector / segmenter / matting 设置包括 Mock、GroundingDINO、OCR、OpenCV GrabCut、rembg、SAM2、Simple 和 BiRefNet。缺少可选依赖时会安全 fallback，不影响应用启动。

OpenAI 支持是可选的。源码模式下如需使用，请自行安装 SDK：

```powershell
.\.venv\Scripts\python.exe -m pip install openai
```

Windows 安装包不会包含任何 API Key。

## API Key 安全说明

API Key 不会硬编码，也不会被打进安装包。

读取顺序：

1. `OPENAI_API_KEY` 环境变量。
2. 用户设置文件，且仅当用户明确选择保存时读取。

设置文件路径：

```text
%LOCALAPPDATA%/AIImageLayerExtractor/config/settings.json
```

不要提交 `settings.json`。如果没有系统级密钥存储，建议优先使用 `OPENAI_API_KEY` 环境变量，或选择不保存 API Key。

## 离线模式说明

没有 API Key 时，软件仍然支持：

- Open Image
- 手动框选和 mask 预览
- Create Layer
- Export All
- Batch Export
- Mock AI 指令解析
- Windows 安装版启动

核心工作流不需要网络访问。

## 云端图像编辑隐私说明

当前版本默认不会上传图片进行云端编辑。`image_editors/openai_image_editor.py` 只是可选扩展接口。

未来如加入云端图像编辑功能，应明确提示用户确认，因为源图片、mask 或选区可能会上传到 API 服务。

## 质量处理说明

批量导出使用本地质量处理管线：中间处理保持 RGBA，默认 PNG 无损写出，支持透明边距，并避免不必要的 JPEG 重复压缩。

处理管线包括：

- 保留 alpha 的高质量 resize
- contain / cover / stretch / max_side / original fit mode
- 可选边缘 refinement
- 可选透明边缘 halo 清理
- 导出质量报告

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
