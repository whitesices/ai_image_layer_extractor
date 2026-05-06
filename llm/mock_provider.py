from __future__ import annotations

import re

from core.edit_plan import (
    BatchOutputSpec,
    CommandContext,
    EditTask,
    ImageEditPlan,
    QualityOptions,
)

from .base_provider import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Rule-based Chinese parser used offline and in tests."""

    name = "Mock"

    def parse_command(self, user_text: str, context: CommandContext) -> ImageEditPlan:
        text = user_text.strip()
        if not text:
            return self._clarification_plan(user_text, "请输入要执行的图片编辑或导出指令。")

        if "重命名" in text:
            return self._parse_rename(text, context)

        if "导出" in text or "尺寸" in text or "透明" in text:
            return self._parse_export(text, context)

        return self._clarification_plan(user_text, "暂时只能解析批量导出、尺寸导出和图层重命名指令。")

    def _parse_export(self, text: str, context: CommandContext) -> ImageEditPlan:
        sizes = self._parse_sizes(text)
        if not sizes:
            sizes = [512]
        padding = self._parse_padding(text)
        output_format = "webp" if "webp" in text.lower() else "png"
        target, layer_ids = self._parse_target(text, context)
        task_type = "batch_export_layers"
        if target == "selected_layers" or layer_ids:
            task_type = "resize_layer" if "当前选中" in text or "选中" in text else "batch_export_layers"

        specs = [
            BatchOutputSpec(width=size, height=size, fit_mode="contain", padding=padding, output_format=output_format)
            for size in sizes
        ]
        task = EditTask(
            type=task_type,
            target=target,
            layer_ids=layer_ids,
            output_name=None,
            sizes=specs,
            transparent_background=True,
            quality=QualityOptions(remove_halo=True),
            params={},
        )
        return ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="batch_export",
            requires_confirmation=True,
            tasks=[task],
            raw_user_text=text,
        )

    def _parse_rename(self, text: str, context: CommandContext) -> ImageEditPlan:
        match = re.search(r"重命名为\s*([A-Za-z0-9_. -]+)", text)
        output_name = match.group(1).strip() if match else None
        target, layer_ids = self._parse_target(text, context)
        if not layer_ids and target == "all_layers":
            layer_ids = context.selected_layer_ids[:]
            target = "selected_layers" if layer_ids else "all_layers"
        task = EditTask(
            type="rename_layer",
            target=target,
            layer_ids=layer_ids,
            output_name=output_name,
            sizes=[],
            transparent_background=True,
            quality=QualityOptions(),
            params={},
        )
        return ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="rename",
            requires_confirmation=True,
            tasks=[task],
            raw_user_text=text,
            clarification_needed=None if output_name else "请提供新的图层名称。",
        )

    def _parse_target(self, text: str, context: CommandContext) -> tuple[str, list[str]]:
        if "当前选中" in text or "选中" in text:
            return "selected_layers", context.selected_layer_ids[:]
        if "所有" in text or "全部" in text or "全都" in text:
            return "all_layers", []

        for layer in context.available_layers:
            layer_id = str(layer.get("id", ""))
            layer_name = str(layer.get("name", ""))
            candidates = {layer_id.lower(), layer_name.lower()}
            if "character" in layer_name.lower():
                candidates.add("角色")
            if "icon" in layer_name.lower():
                candidates.add("图标")
            if any(candidate and candidate in text.lower() for candidate in candidates):
                return "layer_ids", [layer_id]

        if "角色" in text:
            return "layer_name:角色", []
        if "图标" in text or "icon" in text.lower():
            return "layer_name:icon", []
        return "all_layers", []

    def _parse_sizes(self, text: str) -> list[int]:
        normalized = text.replace("×", "x").replace("X", "x")
        sizes: list[int] = []
        for match in re.finditer(r"(?<!\d)(\d{2,4})\s*x\s*(\d{2,4})(?!\d)", normalized):
            width = int(match.group(1))
            height = int(match.group(2))
            if width == height and 1 <= width <= 8192:
                sizes.append(width)

        if sizes:
            return self._dedupe(sizes)

        for value in re.findall(r"(?<!\d)(128|256|512|1024|2048|4096|8192)(?!\d)", normalized):
            sizes.append(int(value))
        return self._dedupe(sizes)

    def _parse_padding(self, text: str) -> int:
        patterns = [
            r"(\d+)\s*(?:px|像素)?\s*(?:透明)?(?:边距|空白|留白)",
            r"(?:边距|空白|留白)\s*(\d+)\s*(?:px|像素)?",
            r"四周留\s*(\d+)\s*(?:px|像素)?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return max(0, min(1024, int(match.group(1))))
        return 0

    def _dedupe(self, values: list[int]) -> list[int]:
        result: list[int] = []
        for value in values:
            if value not in result:
                result.append(value)
        return result

    def _clarification_plan(self, raw_text: str, message: str) -> ImageEditPlan:
        return ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="clarification",
            requires_confirmation=True,
            tasks=[
                EditTask(
                    type="batch_export_layers",
                    target="all_layers",
                    layer_ids=[],
                    output_name=None,
                    sizes=[],
                    transparent_background=True,
                    quality=QualityOptions(),
                    params={},
                )
            ],
            raw_user_text=raw_text,
            clarification_needed=message,
        )
