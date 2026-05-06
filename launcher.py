from __future__ import annotations

import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

from version import APP_EXE_NAME, APP_NAME


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_app_base_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_resource_path(relative_path: str | os.PathLike[str]) -> Path:
    """Resolve resources in source mode and PyInstaller onedir mode."""

    relative = Path(relative_path)
    if relative.is_absolute():
        return relative

    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidate = Path(meipass) / relative
            if candidate.exists():
                return candidate
        return Path(sys.executable).resolve().parent / relative

    return Path(__file__).resolve().parent / relative


def get_user_data_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_EXE_NAME
    return Path.home() / "AppData" / "Local" / APP_EXE_NAME


def ensure_user_dirs() -> dict[str, Path]:
    root = get_user_data_dir()
    paths = {
        "root": root,
        "logs": root / "logs",
        "config": root / "config",
        "cache": root / "cache",
        "exports": root / "exports",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    os.environ["AI_IMAGE_LAYER_EXTRACTOR_USER_DATA_DIR"] = str(paths["root"])
    os.environ["AI_IMAGE_LAYER_EXTRACTOR_LOG_DIR"] = str(paths["logs"])
    os.environ["AI_IMAGE_LAYER_EXTRACTOR_CONFIG_DIR"] = str(paths["config"])
    os.environ["AI_IMAGE_LAYER_EXTRACTOR_CACHE_DIR"] = str(paths["cache"])
    os.environ["AI_IMAGE_LAYER_EXTRACTOR_EXPORT_DIR"] = str(paths["exports"])
    return paths


def run_core_smoke_test(output_root: Path) -> None:
    import numpy as np
    from PIL import Image, ImageDraw

    from core.exporter import LayerExporter
    from core.project import ProjectData
    from segmenters.opencv_segmenter import OpenCVSegmenter

    smoke_dir = output_root / "smoke_export"
    if smoke_dir.exists():
        shutil.rmtree(smoke_dir)

    image = Image.new("RGB", (64, 64), (20, 20, 24))
    draw = ImageDraw.Draw(image)
    draw.rectangle((18, 14, 46, 50), fill=(230, 240, 255))

    segmenter = OpenCVSegmenter(grabcut_iterations=1, feather_radius=0)
    result = segmenter.segment(image, (14, 10, 38, 46))
    if result.is_empty:
        raise RuntimeError("Smoke segmentation produced an empty mask")

    if not isinstance(result.mask, np.ndarray):
        raise RuntimeError("Smoke segmentation did not return a numpy mask")

    project = ProjectData()
    project.set_source_image("smoke_input.png", image)
    project.add_layer_from_mask("smoke_layer", result)
    LayerExporter(smoke_dir).export_all_layers(project)

    expected = [
        smoke_dir / "layers" / "001_smoke_layer.png",
        smoke_dir / "masks" / "001_smoke_layer_mask.png",
        smoke_dir / "project.json",
        smoke_dir / "preview.png",
    ]
    missing = [str(path) for path in expected if not path.exists()]
    if missing:
        raise RuntimeError(f"Smoke export missing files: {missing}")


def get_crash_log_path() -> Path:
    return get_user_data_dir() / "logs" / "crash.log"


def write_crash_log(exc_type: type[BaseException], exc_value: BaseException, exc_tb) -> Path:
    try:
        ensure_user_dirs()
        crash_log = get_crash_log_path()
    except Exception:
        fallback_dir = Path(tempfile.gettempdir()) / APP_EXE_NAME / "logs"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        crash_log = fallback_dir / "crash.log"
    formatted = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    crash_log.write_text(formatted, encoding="utf-8")
    return crash_log


def show_startup_error(message: str, crash_log: Path) -> None:
    text = f"{message}\n\nCrash log:\n{crash_log}"
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication(sys.argv[:1])
        QMessageBox.critical(None, f"{APP_NAME} Startup Error", text)
        if app is not None:
            app.processEvents()
    except Exception:
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, text, f"{APP_NAME} Startup Error", 0x10)
        except Exception:
            pass


def install_exception_hook() -> None:
    default_hook = sys.excepthook

    def handle_exception(exc_type: type[BaseException], exc_value: BaseException, exc_tb) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            default_hook(exc_type, exc_value, exc_tb)
            return
        crash_log = write_crash_log(exc_type, exc_value, exc_tb)
        show_startup_error(str(exc_value), crash_log)
        default_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = handle_exception


def run_app(smoke_test: bool = False) -> int:
    user_dirs = ensure_user_dirs()
    install_exception_hook()

    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from PySide6.QtWidgets import QApplication
    from app.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()

    if smoke_test:
        run_core_smoke_test(user_dirs["cache"])
        print(f"{APP_NAME} smoke test OK")
        return 0

    window.show()
    return int(app.exec())


def main() -> int:
    smoke_test = "--smoke-test" in sys.argv
    try:
        return run_app(smoke_test=smoke_test)
    except Exception as exc:
        crash_log = write_crash_log(type(exc), exc, exc.__traceback__)
        if not smoke_test:
            show_startup_error(str(exc), crash_log)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
