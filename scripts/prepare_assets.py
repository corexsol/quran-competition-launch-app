from __future__ import annotations

import argparse
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageOps


PAGE_SCALE = 1.125
PAGE_SIZE = (2160, 1215)
OUTPUT_NAMES = (
    "page-1.png",
    "page-2.png",
    "icon-180.png",
    "icon-192.png",
    "icon-512.png",
)
def render_pdf(path: Path, scale: float, page_index: int) -> Image.Image:
    document = pdfium.PdfDocument(str(path))
    page = document[page_index]
    bitmap = page.render(
        scale=scale,
        fill_color=(12, 70, 38, 255),
        rev_byteorder=True,
    )
    image = bitmap.to_pil().convert("RGB")
    if image.size != PAGE_SIZE:
        raise ValueError(f"Unexpected rendered page size: {image.size}")
    return image


def save_png(image: Image.Image, path: Path) -> None:
    image.save(path, format="PNG", optimize=True, compress_level=9)


def create_icons(page_two: Image.Image, output_dir: Path) -> None:
    emblem = page_two.crop((675, 235, 1485, 1045))
    square = ImageOps.fit(
        emblem,
        (512, 512),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.48),
    )
    for size in (180, 192, 512):
        save_png(
            square.resize((size, size), Image.Resampling.LANCZOS),
            output_dir / f"icon-{size}.png",
        )


def prepare_assets(master_pdf: Path, output_dir: Path) -> None:
    if not master_pdf.is_file():
        raise FileNotFoundError(master_pdf)
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = [render_pdf(master_pdf, PAGE_SCALE, index) for index in (0, 1)]
    for number, page in enumerate(pages, start=1):
        save_png(page, output_dir / f"page-{number}.png")
    create_icons(pages[1], output_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-pdf", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "launch-app" / "assets",
    )
    arguments = parser.parse_args()
    prepare_assets(arguments.master_pdf, arguments.output_dir)


if __name__ == "__main__":
    main()
