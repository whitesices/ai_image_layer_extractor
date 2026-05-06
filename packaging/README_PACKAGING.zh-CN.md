# 打包 AI Image Layer Extractor

本目录包含 AI Image Layer Extractor 的 Windows 打包流水线。
它不会替代源码/开发工作流。

## 环境要求

- Windows 10/11 x64
- Python 3.10+
- Inno Setup 6
- PowerShell 5+

构建脚本会创建或复用 `.venv`，从 `requirements.txt` 安装运行依赖，并从 `requirements-dev.txt` 安装打包依赖。

## 一键构建

```powershell
cd C:\ML\EditImage\ai_image_layer_extractor
.\packaging\scripts\build_all.ps1
```

如果 PowerShell 执行策略阻止本地脚本，请使用：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\packaging\scripts\build_all.ps1
```

输出：

```text
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

## 只构建 EXE

```powershell
.\packaging\scripts\build_exe.ps1
```

输出：

```text
dist/AIImageLayerExtractor/AIImageLayerExtractor.exe
```

## 只构建安装包

请先运行 `build_exe.ps1`，然后执行：

```powershell
.\packaging\scripts\build_installer.ps1
```

输出：

```text
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

## 清理构建产物

```powershell
.\packaging\scripts\clean_build.ps1
```

该脚本会删除 `build/`、`dist/`、`release/`、项目根目录下生成的 `.spec` 文件，以及 `__pycache__` 文件夹。它不会删除 `packaging/pyinstaller/AIImageLayerExtractor.spec`。

## 已安装应用的数据目录

打包版 launcher 会在以下路径创建用户数据目录：

```text
%LOCALAPPDATA%/AIImageLayerExtractor/
+-- logs/
+-- config/
+-- cache/
+-- exports/
```

安装程序只会卸载应用文件。它会有意保留 `%LOCALAPPDATA%/AIImageLayerExtractor`。

## LLM 和可选依赖

安装包不会包含 OpenAI API Key，也不会强制安装 `torch`、SAM2、rembg 或 OCR 包。默认安装版可以在离线状态下继续使用手动工具、批量导出和 Mock LLM Provider。

OpenAI LLM 解析是可选能力。源码模式下如需使用，请自行安装 SDK：

```powershell
.\.venv\Scripts\python.exe -m pip install openai
```

如果缺少 OpenAI SDK 或 API Key，UI 会回退到 Mock Provider，而不是崩溃。

## 常见问题

### PySide6 DLL load failed

本项目固定使用 `PySide6==6.7.3`。在部分 Windows/Anaconda 机器上，较新的 PySide6 版本可能因为 Qt DLL 加载到不兼容的 ICU DLL 而失败。

修复：

```powershell
.\.venv\Scripts\python.exe -m pip install --force-reinstall PySide6==6.7.3
```

### 找不到 Qt platform plugin windows

PyInstaller spec 已经显式收集 PySide6 platform 和 imageformat 插件。如果仍然出现该问题，请从干净状态重新构建：

```powershell
.\packaging\scripts\clean_build.ps1
.\packaging\scripts\build_exe.ps1
```

### cv2 import failed

确认 `.venv` 中已经安装 `opencv-python`：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

然后重新构建 EXE。

### ISCC.exe not found

请安装 Inno Setup 6。脚本会检查：

```text
C:\Users\<you>\AppData\Local\Programs\Inno Setup 6\ISCC.exe
C:\Program Files (x86)\Inno Setup 6\ISCC.exe
C:\Program Files\Inno Setup 6\ISCC.exe
```

它也支持 PATH 中的 `ISCC.exe`。

### 杀毒软件误报

PyInstaller 会打包 Python 和原生 DLL，这可能触发启发式警告。发布前建议在干净机器上构建，避免 onefile 模式，并在需要分发时为安装包签名。

### 安装后的应用无法打开

请检查：

```text
%LOCALAPPDATA%/AIImageLayerExtractor/logs/crash.log
```

launcher 会把未处理的启动异常写入该文件，并在错误弹窗中显示该路径。

## 源码工作流保持不变

打包文件位于 `packaging/` 下。
构建产物位于 `build/`、`dist/` 和 `release/` 下。

源码工作流仍然可用：

```powershell
python main.py
python -B -m pytest
```
