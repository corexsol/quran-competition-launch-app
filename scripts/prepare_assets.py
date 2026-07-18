from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageOps


@dataclass(frozen=True)
class AssetSpec:
    source: str
    output: str
    scale: float
    trim: bool = True


ASSETS = (
    AssetSpec("Asset 3.pdf", "title.png", 4.0),
    AssetSpec("Asset 2.pdf", "minister.png", 4.0),
    AssetSpec("Asset 1.pdf", "start-button.png", 3.0),
    AssetSpec("Asset 4.pdf", "background-sides.png", 1.125, False),
    AssetSpec("Asset 5.pdf", "background-medallion.png", 1.5),
    AssetSpec("Asset 1022.pdf", "statistics.png", 2.5),
)

OUTPUT_NAMES = tuple(spec.output for spec in ASSETS) + (
    "icon-180.png",
    "icon-192.png",
    "icon-512.png",
)


def render_pdf(path: Path, scale: float, page_index: int = 0) -> Image.Image:
    document = pdfium.PdfDocument(str(path))
    page = document[page_index]
    bitmap = page.render(
        scale=scale,
        fill_color=(255, 255, 255, 0),
        rev_byteorder=True,
    )
    return bitmap.to_pil().convert("RGBA")


def trim_transparent(image: Image.Image, padding: int = 24) -> Image.Image:
    alpha = image.getchannel("A")
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError("Rendered artwork is fully transparent")
    left, top, right, bottom = bounds
    return image.crop(
        (
            max(0, left - padding),
            max(0, top - padding),
            min(image.width, right + padding),
            min(image.height, bottom + padding),
        )
    )


def save_png(image: Image.Image, path: Path) -> None:
    image.save(path, format="PNG", optimize=True, compress_level=9)


def create_icons(master_pdf: Path, output_dir: Path) -> None:
    master_page = render_pdf(master_pdf, scale=1.0, page_index=1).convert("RGB")
    logo_crop = master_page.crop((720, 245, 1200, 725))
    square = ImageOps.fit(
        logo_crop,
        (512, 512),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    for size in (180, 192, 512):
        icon = square.resize((size, size), Image.Resampling.LANCZOS)
        save_png(icon, output_dir / f"icon-{size}.png")


def prepare_assets(source_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for spec in ASSETS:
        source = source_dir / spec.source
        if not source.is_file():
            raise FileNotFoundError(source)
        image = render_pdf(source, spec.scale)
        if spec.trim:
            image = trim_transparent(image)
        save_png(image, output_dir / spec.output)
    create_icons(source_dir / "تطبيق التدشين.pdf", output_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "launch-app" / "assets",
    )
    arguments = parser.parse_args()
    prepare_assets(arguments.source_dir, arguments.output_dir)


if __name__ == "__main__":
    main()
