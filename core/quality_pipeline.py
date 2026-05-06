from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from .mask_utils import dilate_mask, erode_mask, feather_mask, normalize_mask


Resampling = Image.Resampling


@dataclass(slots=True)
class QualityReport:
    width: int
    height: int
    has_alpha: bool
    alpha_min: int
    alpha_max: int
    transparent_pixel_ratio: float
    warnings: list[str]


class QualityPipeline:
    """Small quality pipeline for transparent layer export."""

    def ensure_rgba(self, image: Image.Image) -> Image.Image:
        if image.mode == "RGBA":
            return image.copy()
        return image.convert("RGBA")

    def premultiply_alpha(self, image: Image.Image) -> Image.Image:
        rgba = np.asarray(self.ensure_rgba(image)).astype(np.float32)
        alpha = rgba[..., 3:4] / 255.0
        rgba[..., :3] *= alpha
        return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA")

    def unpremultiply_alpha(self, image: Image.Image) -> Image.Image:
        rgba = np.asarray(self.ensure_rgba(image)).astype(np.float32)
        alpha = rgba[..., 3:4]
        safe_alpha = np.where(alpha <= 0, 1.0, alpha)
        rgba[..., :3] = np.where(alpha <= 0, rgba[..., :3], rgba[..., :3] * 255.0 / safe_alpha)
        return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA")

    def remove_alpha_halo(self, rgba: Image.Image, mode: str = "auto") -> Image.Image:
        image = self.ensure_rgba(rgba)
        array = np.array(image, dtype=np.uint8)
        alpha = array[..., 3]
        visible = alpha > 0
        if not np.any(visible):
            return image

        if mode not in {"auto", "transparent_only"}:
            raise ValueError(f"Unsupported halo removal mode: {mode}")

        source_pixels = array[..., :3][alpha > 192]
        if source_pixels.size == 0:
            source_pixels = array[..., :3][visible]
        fill_rgb = np.median(source_pixels, axis=0).astype(np.uint8)

        # Only fully transparent pixels are changed by default. Visible pixels keep
        # their original RGB values, avoiding destructive edits to extracted art.
        transparent = alpha == 0
        array[..., :3][transparent] = fill_rgb
        return Image.fromarray(array, mode="RGBA")

    def refine_mask_edges(
        self,
        mask: np.ndarray,
        feather_radius: int = 1,
        dilate_pixels: int = 0,
        erode_pixels: int = 0,
    ) -> np.ndarray:
        refined = normalize_mask(mask)
        if dilate_pixels:
            refined = dilate_mask(refined, dilate_pixels)
        if erode_pixels:
            refined = erode_mask(refined, erode_pixels)
        if feather_radius:
            refined = feather_mask(refined, feather_radius)
        return normalize_mask(refined)

    def add_transparent_padding(self, rgba: Image.Image, padding: int) -> Image.Image:
        image = self.ensure_rgba(rgba)
        padding = max(0, int(padding))
        if padding == 0:
            return image
        output = Image.new("RGBA", (image.width + padding * 2, image.height + padding * 2), (0, 0, 0, 0))
        output.alpha_composite(image, dest=(padding, padding))
        return output

    def resize_rgba_high_quality(
        self,
        rgba: Image.Image,
        target_width: int,
        target_height: int,
        fit_mode: str = "contain",
        padding: int = 0,
    ) -> Image.Image:
        image = self.ensure_rgba(rgba)
        target_width = max(1, int(target_width))
        target_height = max(1, int(target_height))
        padding = max(0, int(padding))

        if fit_mode == "original":
            return self.add_transparent_padding(image, padding)

        inner_width = max(1, target_width - padding * 2)
        inner_height = max(1, target_height - padding * 2)

        if fit_mode == "stretch":
            resized = image.resize((inner_width, inner_height), Resampling.LANCZOS)
            return self._center_on_canvas(resized, target_width, target_height)

        if fit_mode == "contain":
            scale = min(inner_width / image.width, inner_height / image.height)
            resized = self._resize_by_scale(image, scale)
            return self._center_on_canvas(resized, target_width, target_height)

        if fit_mode == "cover":
            scale = max(inner_width / image.width, inner_height / image.height)
            resized = self._resize_by_scale(image, scale)
            left = max(0, (resized.width - inner_width) // 2)
            top = max(0, (resized.height - inner_height) // 2)
            cropped = resized.crop((left, top, left + inner_width, top + inner_height))
            return self._center_on_canvas(cropped, target_width, target_height)

        if fit_mode == "max_side":
            max_side = max(inner_width, inner_height)
            scale = max_side / max(image.width, image.height)
            resized = self._resize_by_scale(image, scale)
            return self.add_transparent_padding(resized, padding)

        raise ValueError(f"Unsupported fit_mode: {fit_mode}")

    def validate_export_quality(self, rgba: Image.Image) -> QualityReport:
        image = self.ensure_rgba(rgba)
        alpha = np.asarray(image.getchannel("A"), dtype=np.uint8)
        total_pixels = max(1, alpha.size)
        transparent_ratio = float(np.count_nonzero(alpha == 0) / total_pixels)
        warnings: list[str] = []
        if int(alpha.max()) == 0:
            warnings.append("Image is fully transparent.")
        if image.width <= 0 or image.height <= 0:
            warnings.append("Image has invalid dimensions.")
        return QualityReport(
            width=image.width,
            height=image.height,
            has_alpha="A" in image.getbands(),
            alpha_min=int(alpha.min()) if alpha.size else 0,
            alpha_max=int(alpha.max()) if alpha.size else 0,
            transparent_pixel_ratio=transparent_ratio,
            warnings=warnings,
        )

    def _resize_by_scale(self, image: Image.Image, scale: float) -> Image.Image:
        width = max(1, int(round(image.width * scale)))
        height = max(1, int(round(image.height * scale)))
        return image.resize((width, height), Resampling.LANCZOS)

    def _center_on_canvas(self, image: Image.Image, width: int, height: int) -> Image.Image:
        output = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        x = (width - image.width) // 2
        y = (height - image.height) // 2
        output.alpha_composite(image, dest=(x, y))
        return output
