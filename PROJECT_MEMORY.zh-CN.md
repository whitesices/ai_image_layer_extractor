# AI Image Layer Extractor 项目记忆

最后更新：2026-05-06

## 项目目标

AI Image Layer Extractor 是一个本地 Python 桌面 MVP，用于从 AI 生成的扁平图片中提取可编辑的透明 PNG 图层。当前工作流优先采用手动框选，再使用 OpenCV 辅助生成 mask，并导出适合 Photoshop、Figma、Unreal Engine UMG 或其他下游工具使用的干净元数据。

## 当前实现

- 入口文件：`main.py`
- 桌面 UI：`app/` 中的 PySide6 代码
- 核心项目状态和图像逻辑：`core/`
- 分割后端：`segmenters/`
- 测试：`tests/`

已实现的 MVP 能力：

- 打开 PNG / JPG / WEBP 源图片。
- 在中央画布显示图片。
- 使用鼠标滚轮缩放。
- 使用鼠标右键或中键拖拽平移。
- 使用鼠标左键拖拽绘制矩形选区。
- 选区完成后生成 mask 预览。
- 将当前预览确认为图层。
- 重命名、显示/隐藏、删除、导出单个图层、导出全部图层。
- 导出裁剪后的透明图层 PNG、裁剪后的 mask PNG、`project.json` 和 `preview.png`。

## 重要文件

- `core/layer.py`：`MaskResult` 和 `LayerItem`。
- `core/project.py`：`ProjectData`、图层集合、源图片状态。
- `core/mask_utils.py`：bbox、清理、羽化/膨胀/腐蚀、RGBA 应用。
- `core/exporter.py`：`LayerExporter` 和导出契约。
- `segmenters/base_segmenter.py`：后端接口。
- `segmenters/opencv_segmenter.py`：OpenCV GrabCut 后端，带矩形 fallback。
- `segmenters/rembg_segmenter.py`：未来 rembg 后端占位。
- `segmenters/sam2_segmenter.py`：未来 SAM2 后端占位。
- `app/canvas_widget.py`：图片显示、选区、缩放/平移、mask 叠加、图层 bbox 绘制。
- `app/layer_panel.py`：图层列表、图层操作、内联重命名编辑器尺寸。
- `app/main_window.py`：UI、项目状态、分割、导出和全局样式表之间的编排。

## 架构说明

UI 和核心逻辑有意保持解耦：

- UI 控件发出选区和图层操作信号。
- `MainWindow` 负责编排工作流。
- `ProjectData` 持有源图片状态和图层元数据。
- `BaseSegmenter` 实现返回全画布 `MaskResult` 对象。
- `LayerExporter` 写入文件，并更新图层相对文件路径。

Mask 是全画布 `uint8` 数组，取值范围为 `0..255`。图层 PNG 和 mask PNG 会裁剪到图层 bbox，而 `project.json` 会保存原始画布坐标。

## 导出契约

导出目录：

```text
Export/
+-- layers/
+-- masks/
+-- project.json
+-- preview.png
```

图层 JSON 字段：

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

除非下游导入器同步更新，否则应保持该契约稳定。

## UI 维护记录

2026-05-06，右侧图层列表重命名时，内联编辑器文本在垂直方向被裁切。截图显示选中的 `QListWidgetItem` 行和嵌入的重命名 `QLineEdit` 高度太短，导致字符被部分遮挡。

已应用修复：

- 在 `app/layer_panel.py` 中添加 `LayerItemDelegate`。
- 重写 `sizeHint()`，确保图层行至少 42 px 高。
- 重写 `createEditor()`，让内联 `QLineEdit` 编辑器获得足够的最小高度。
- 重写 `updateEditorGeometry()`，让编辑器在行内留出边距，避免贴住行边缘。
- 更新 `app/main_window.py` 样式表，为 `QListWidget::item` 和 `QListWidget QLineEdit` 设置 padding/min-height。

UI 修复后的验证：

```text
python -m compileall app core segmenters tests main.py
python -B -m pytest
QT_QPA_PLATFORM=offscreen MainWindow smoke test
```

结果：测试通过，`MainWindow` 可以成功实例化。

## 打包记录

2026-05-06，在不改变原 `main.py` 源码入口的前提下，新增了 Windows 安装版打包流水线。

新增文件：

- `launcher.py`：PyInstaller/安装版入口、用户数据目录创建、崩溃日志、`--smoke-test`、资源路径工具。
- `version.py`：应用名、可执行文件名、版本、发布者、描述。
- `requirements-dev.txt`：开发和打包依赖（`pytest`、`pyinstaller`）。
- `packaging/pyinstaller/AIImageLayerExtractor.spec`：PyInstaller onedir 构建配置。
- `packaging/inno/AIImageLayerExtractor.iss`：Inno Setup 当前用户安装脚本。
- `packaging/assets/app_icon.ico`：生成的占位图标。
- `packaging/assets/license.txt`：占位许可证文本。
- `packaging/scripts/*.ps1`：清理、EXE 构建、安装包构建、完整构建脚本。
- `packaging/README_PACKAGING.md`：打包工作流和故障排查。

运行依赖拆分：

- `requirements.txt`：仅运行依赖（`PySide6==6.7.3`、`Pillow`、`opencv-python`、`numpy`）。
- `requirements-dev.txt`：仅测试/构建工具。

安装版/打包版行为：

- 打包版应用使用 `launcher.py`。
- 源码版仍可使用 `python main.py`。
- 安装目标为当前用户目录：`%LOCALAPPDATA%/Programs/AI Image Layer Extractor`。
- 打包版用户数据会创建在 `%LOCALAPPDATA%/AIImageLayerExtractor`，包含 `logs/`、`config/`、`cache/` 和 `exports/`。
- `MainWindow._default_export_dir()` 只在 launcher 设置 `AI_IMAGE_LAYER_EXTRACTOR_EXPORT_DIR` 时使用该目录；源码模式保持不变。
- Inno 卸载只删除程序文件，不删除用户数据。

已完成的构建验证：

```text
packaging/scripts/build_all.ps1
dist/AIImageLayerExtractor/AIImageLayerExtractor.exe
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

额外 smoke 验证：

- 源码 launcher smoke test 在可写 `LOCALAPPDATA` 覆盖目录下通过。
- PyInstaller EXE smoke test 通过。
- 安装包使用 Inno Setup 6.7.1 构建成功。
- 静默安装包解包 smoke test 通过。
- 已安装 EXE smoke test 通过。
- 静默卸载器返回退出码 0。

环境说明：当前机器通过 `winget` 安装 Inno Setup，`ISCC.exe` 位于 `%LOCALAPPDATA%/Programs/Inno Setup 6/ISCC.exe`。`build_installer.ps1` 除了常见 Program Files 路径外，也会检查这个当前用户路径。

## AI Command 和批量导出记录

2026-05-06，应用新增了模块化 AI 指令计划和生产向批量导出能力。

新增模块：

- `core/edit_plan.py`：结构化 `ImageEditPlan`、任务、质量选项、批量尺寸和命令上下文 dataclass。
- `llm/`：Provider 接口、离线 `MockLLMProvider`、可选 `OpenAIProvider`、prompt template、schema 校验和配置辅助函数。
- `core/quality_pipeline.py`：RGBA 安全 resize、透明 padding、alpha halo 清理、mask 边缘 refinement 和质量报告。
- `core/batch_exporter.py`：多尺寸图层导出、original 目录、masks、`batch_report.json`、preview 和 project metadata。
- `core/command_executor.py`：为 `batch_export_layers`、`resize_layer` 和 `rename_layer` 提供 dry-run 与执行能力。
- `image_editors/`：本地图像编辑辅助能力和可选 OpenAI 图像编辑扩展点。
- `app/ai_command_panel.py`：可停靠的自然语言指令 UI，包含 Parse、Dry Run、Execute 和 Clear。
- `app/batch_export_panel.py`：可停靠的批量导出 UI，包含尺寸预设、自定义尺寸、fit mode、padding 和输出格式。
- `app/settings_dialog.py`：Provider、可选 API Key、默认导出目录和批量默认值设置。

设计决策：

- LLM Provider 只生成结构化计划，绝不直接修改像素。
- 缺少 OpenAI SDK 或 API Key 时回退到 Mock Provider，不破坏手动工作流。
- OpenAI API Key 只从 `OPENAI_API_KEY` 或用户设置读取，绝不会被打进安装包。
- 批量导出不会修改原始 `LayerItem` 几何信息或 mask。
- SAM2、rembg、OCR、PSD、云端图像编辑和 UE 导入仍保持为未来可选扩展。

该功能阶段后的验证：

```text
python -B -m pytest
18 passed
```

## 验证

已知通过的命令：

```powershell
cd C:\ML\EditImage\ai_image_layer_extractor
python -B -m pytest
```

最新结果：

```text
18 passed in 0.25s
```

`pytest.ini` 将测试发现范围限制在 `tests/`，并禁用 pytest cache，因为早先的环境尝试在项目根目录创建了无法访问的 `pytest-cache-files-*` 文件夹。

## 环境说明

创建时，当前全局 Python 是 3.12.7。它没有安装 `PySide6` 或 `cv2`。代码仍然可以测试，因为 `mask_utils.py` 和 `OpenCVSegmenter` 在 `cv2` 不可用时包含最小 fallback。

2026-05-06，`PySide6==6.11.0` 在当前机器上失败：

```text
ImportError: DLL load failed while importing QtWidgets: specified program could not be found.
```

`dumpbin` 显示 `Qt6Core.dll` 尝试加载 ICU 相关 DLL，而系统/Anaconda ICU 版本不兼容。固定并重新安装 `PySide6==6.7.3` 后，`QtCore`、`QtWidgets` 和 `MainWindow` smoke test 均恢复正常。除非本地验证了新版 PySide6，否则保持 `requirements.txt` 中的固定版本。

如需完整 GUI 和 GrabCut 行为，请安装：

```powershell
pip install -r requirements.txt
```

然后运行：

```powershell
python main.py
```

## 已知环境残留

项目根目录可能保留三个名字类似 `pytest-cache-files-*` 的目录。它们是在系统拒绝 pytest cache 写入时由 pytest 创建的，之后当前进程无法访问。这些目录已被 `.gitignore` 忽略，并被 `pytest.ini` 排除。

## 后续改进建议

1. 添加基于画笔的手动 mask 编辑。
2. 在图层面板中添加每个图层的 mask 预览缩略图。
3. 添加 `Save Project` / `Open Project`，用于恢复图层状态。
4. 在 `segmenters/sam2_segmenter.py` 中添加 SAM2 点选/框选分割。
5. 在 `segmenters/rembg_segmenter.py` 中添加 rembg 后端。
6. 添加 OCR 文字图层检测。
7. 添加 PSD 导出。
8. 添加 UE UMG JSON 导出和 UE Python Texture2D 导入自动化。
