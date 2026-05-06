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
    """Offline rule-based parser for common Chinese production commands."""

    name = "Mock"

    def parse_command(self, user_text: str, context: CommandContext) -> ImageEditPlan:
        text = user_text.strip()
        if not text:
            return self._clarification_plan(user_text, "请输入要执行的图片编辑或导出指令。")

        lowered = text.lower()
        if "重命名" in text:
            return self._parse_rename(text, context)
        if "ue" in lowered or "umg" in lowered or "unreal" in lowered:
            return self._parse_ue_export(text, context)
        if "psd" in lowered or "分层思路" in text:
            return self._single_task_plan(text, "future_psd_export", "psd_compatible_export", "all_layers")
        if "文字" in text or "文本" in text:
            return self._single_task_plan(
                text,
                "detect_text_regions",
                "detect_text",
                "text_regions",
                params={
                    "target_prompt": "text",
                    "risk_warning": "需要 OCR 后端；未启用时会提示用户手动框选文字区域。",
                },
            )
        if "白边" in text or "锯齿" in text or "透明边缘" in text or "边缘" in text and "优化" in text:
            return self._parse_refine_mask(text, context)
        if "分别" in text and len(self._parse_target_names(text)) > 1:
            return self._parse_extraction(text)
        if "提取" in text or "抠" in text or "抠出来" in text:
            return self._parse_extraction(text)
        if "背景" in text and ("导出" in text or "背景图" in text or "背景层" in text):
            return self._parse_background(text)
        if "导出" in text or "尺寸" in text or "透明" in text or "图标" in text:
            return self._parse_export(text, context)

        return self._clarification_plan(text, "暂时只能解析批量导出、目标提取、边缘优化、UE/PSD 导出和图层重命名指令。")

    def _parse_export(self, text: str, context: CommandContext) -> ImageEditPlan:
        sizes = self._parse_sizes(text) or [(512, 512)]
        padding = self._parse_padding(text)
        output_format = "webp" if "webp" in text.lower() else "png"
        fit_mode = self._parse_fit_mode(text)
        target, layer_ids = self._parse_target(text, context)
        task_type = "resize_layer" if target == "selected_layers" else "batch_export_layers"

        specs = [
            BatchOutputSpec(width=size[0], height=size[1], fit_mode=fit_mode, padding=padding, output_format=output_format)
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
            params={
                "scope": target,
                "risk_warning": "",
            },
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
        if not layer_ids and target in {"all_layers", "visible_layers"}:
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

    def _parse_ue_export(self, text: str, context: CommandContext) -> ImageEditPlan:
        sizes = self._parse_sizes(text) or [(512, 512), (1024, 1024)]
        target, layer_ids = self._parse_target(text, context)
        task = EditTask(
            type="export_for_ue_umg",
            target=target,
            layer_ids=layer_ids,
            output_name="Export_UE",
            sizes=[
                BatchOutputSpec(width=width, height=height, fit_mode="contain", padding=self._parse_padding(text), output_format="png")
                for width, height in sizes
            ],
            transparent_background=True,
            quality=QualityOptions(remove_halo=True),
            params={
                "generate_import_script": True,
                "ue_texture_prefix": "T_",
                "ue_mask_prefix": "M_",
            },
        )
        return ImageEditPlan("1.0", "zh-CN", "export_for_ue_umg", True, [task], text)

    def _parse_refine_mask(self, text: str, context: CommandContext) -> ImageEditPlan:
        target, layer_ids = self._parse_target(text, context)
        if target == "all_layers" and context.selected_layer_ids and "所有" not in text and "全部" not in text:
            target = "selected_layers"
            layer_ids = context.selected_layer_ids[:]
        task = EditTask(
            type="refine_mask",
            target=target,
            layer_ids=layer_ids,
            output_name=None,
            sizes=[],
            transparent_background=True,
            quality=QualityOptions(
                refine_edges=True,
                feather_radius=1 if "锯齿" in text or "透明边缘" in text else 0,
                dilate_pixels=0,
                erode_pixels=0,
                remove_halo=True,
            ),
            params={
                "clean_holes": True,
                "remove_small_islands": True,
                "remove_halo": True,
                "risk_warning": "该操作只修改 mask 或导出边缘质量，不修改原图像素。",
            },
        )
        return ImageEditPlan("1.0", "zh-CN", "refine_mask", True, [task], text)

    def _parse_background(self, text: str) -> ImageEditPlan:
        task = EditTask(
            type="create_background_layer",
            target="background",
            layer_ids=[],
            output_name="background",
            sizes=[],
            transparent_background=False,
            quality=QualityOptions(),
            params={
                "target_prompt": "background",
                "risk_warning": "如果没有前景 mask，背景层可能需要用户手动框选或高级模型支持。",
            },
        )
        return ImageEditPlan("1.0", "zh-CN", "create_background_layer", True, [task], text)

    def _parse_extraction(self, text: str) -> ImageEditPlan:
        target_names = self._parse_target_names(text)
        if len(target_names) > 1 or "分别" in text:
            task = EditTask(
                type="extract_multiple_targets",
                target="multiple_targets",
                layer_ids=[],
                output_name=None,
                sizes=[],
                transparent_background=True,
                quality=QualityOptions(),
                params={
                    "target_names": target_names,
                    "risk_warning": "没有检测器或 bbox 时会提示用户手动框选目标。",
                },
            )
            return ImageEditPlan("1.0", "zh-CN", "extract_multiple_targets", True, [task], text)

        target_prompt = target_names[0] if target_names else "object"
        task = EditTask(
            type="extract_target",
            target=target_prompt,
            layer_ids=[],
            output_name=target_prompt,
            sizes=[],
            transparent_background=True,
            quality=QualityOptions(),
            params={
                "target_prompt": target_prompt,
                "position_hint": self._parse_position_hint(text),
                "risk_warning": "没有检测器或 bbox 时会提示用户手动框选目标。",
            },
        )
        return ImageEditPlan("1.0", "zh-CN", "extract_target", True, [task], text)

    def _single_task_plan(
        self,
        text: str,
        task_type: str,
        intent: str,
        target: str | None,
        params: dict | None = None,
    ) -> ImageEditPlan:
        task = EditTask(
            type=task_type,
            target=target,
            layer_ids=[],
            output_name=None,
            sizes=[],
            transparent_background=True,
            quality=QualityOptions(),
            params=params or {},
        )
        return ImageEditPlan("1.0", "zh-CN", intent, True, [task], text)

    def _parse_target(self, text: str, context: CommandContext) -> tuple[str, list[str]]:
        lowered = text.lower()
        if "当前选中" in text or "选中" in text:
            return "selected_layers", context.selected_layer_ids[:]
        if "可见" in text:
            return "visible_layers", []

        for layer in context.available_layers:
            layer_id = str(layer.get("id", ""))
            layer_name = str(layer.get("name", ""))
            candidates = {layer_id.lower(), layer_name.lower()}
            if "character" in layer_name.lower() or "hero" in layer_name.lower() or "角色" in layer_name:
                candidates.update({"角色", "人物", "player", "character"})
            if "weapon" in layer_name.lower() or "武器" in layer_name:
                candidates.update({"武器", "weapon"})
            if "icon" in layer_name.lower() or "图标" in layer_name:
                candidates.update({"图标", "icon"})
            if "logo" in layer_name.lower():
                candidates.add("logo")
            if any(candidate and candidate.lower() in lowered for candidate in candidates):
                return "layer_ids", [layer_id]

        if "角色" in text or "人物" in text:
            return "layer_name:character", []
        if "武器" in text:
            return "layer_name:weapon", []
        if "图标" in text or "icon" in lowered:
            return "layer_name:icon", []
        if "logo" in lowered:
            return "layer_name:logo", []
        if "所有" in text or "全部" in text or "全都" in text:
            return "all_layers", []
        return "all_layers", []

    def _parse_target_names(self, text: str) -> list[str]:
        names: list[str] = []
        mapping = [
            ("人物", "person"),
            ("角色", "character"),
            ("武器", "weapon"),
            ("道具", "prop"),
            ("logo", "logo"),
            ("Logo", "logo"),
            ("文字", "text"),
            ("背景", "background"),
            ("阴影", "shadow"),
            ("装饰", "decoration"),
            ("服装", "clothing"),
        ]
        for token, normalized in mapping:
            if token in text and normalized not in names:
                names.append(normalized)
        return names

    def _parse_position_hint(self, text: str) -> str | None:
        if "左边" in text or "左侧" in text:
            return "left"
        if "右边" in text or "右侧" in text:
            return "right"
        if "中间" in text or "中央" in text:
            return "center"
        if "上方" in text or "上面" in text:
            return "top"
        if "下方" in text or "下面" in text:
            return "bottom"
        return None

    def _parse_sizes(self, text: str) -> list[tuple[int, int]]:
        normalized = text.replace("×", "x").replace("X", "x").replace("，", ",").replace("、", ",")
        sizes: list[tuple[int, int]] = []
        for match in re.finditer(r"(?<!\d)(\d{1,4})\s*x\s*(\d{1,4})(?!\d)", normalized):
            width = int(match.group(1))
            height = int(match.group(2))
            if 1 <= width <= 8192 and 1 <= height <= 8192:
                sizes.append((width, height))

        if sizes:
            return self._dedupe_sizes(sizes)

        for value in re.findall(r"(?<!\d)(128|256|512|1024|2048|4096|8192)(?!\d)", normalized):
            size = int(value)
            sizes.append((size, size))
        return self._dedupe_sizes(sizes)

    def _parse_padding(self, text: str) -> int:
        patterns = [
            r"(\d+)\s*(?:px|像素)?\s*(?:透明)?(?:边距|空白|留白)",
            r"(?:边距|空白|留白)\s*(\d+)\s*(?:px|像素)?",
            r"四周留\s*(\d+)\s*(?:px|像素)?",
            r"加\s*(\d+)\s*(?:px|像素)?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return max(0, min(1024, int(match.group(1))))
        return 0

    def _parse_fit_mode(self, text: str) -> str:
        lowered = text.lower()
        if "cover" in lowered or "填满" in text:
            return "cover"
        if "stretch" in lowered or "拉伸" in text:
            return "stretch"
        if "max_side" in lowered or "最长边" in text:
            return "max_side"
        if "original" in lowered or "原始" in text:
            return "original"
        return "contain"

    def _dedupe_sizes(self, values: list[tuple[int, int]]) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
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
