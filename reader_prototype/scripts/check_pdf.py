"""Inspect searchable PDF content, vector resources, and page bounds, then render."""
import json
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

from inspect_archive import ROOT, write

BUILD = ROOT / "build"
QA = BUILD / "qa"


def render(pdf):
    QA.mkdir(parents=True, exist_ok=True)
    pages = []
    with pymupdf.open(pdf) as document:
        assert len(document) > 0
        assert len(document.get_toc()) >= 7
        for page in document:
            text = page.get_text()
            assert text.strip()
            assert "\ufffd" not in text
            images = page.get_image_info()
            assert not images, f"Unexpected raster image on page {page.number+1}"
            text_boxes = [b for b in page.get_text("blocks") if b[6] == 0]
            bounds = pymupdf.Rect(text_boxes[0][:4])
            for box in text_boxes[1:]:
                bounds |= pymupdf.Rect(box[:4])
            assert page.rect.contains(bounds)
            page.get_pixmap(matrix=pymupdf.Matrix(1.65, 1.65), alpha=False).save(
                QA / f"page-{page.number+1:02d}.png")
            pages.append({
                "page": page.number+1, "text_characters": len(text),
                "text_bbox_points": list(map(lambda x: round(x, 1), bounds)),
                "drawing_objects": len(page.get_drawings()), "raster_images": len(images),
                "links": len(page.get_links()),
                "top_text": " / ".join(text.splitlines()[:6]),
                "bottom_text": " / ".join(text.splitlines()[-5:]),
            })
        combined = "\n".join(p.get_text() for p in document)
        landmarks = ["Stylized Facts of Financial Returns", "Volatility Clustering", "Typical Financial Return ACF",
                     "Returns are uncorrelated", "Baseline", "Periods after shock",
                     "Student's t", "0.0000573%", "Potential Problem"]
        for marker in landmarks:
            assert marker in combined, marker
        for marker in ("研究准备中的提问", "续读请求", "数学读本样张"):
            assert marker not in combined, marker
        write(QA / "pdf-checks.json",
              json.dumps({"pages": pages, "outline": document.get_toc(), "search_landmarks": landmarks},
                         ensure_ascii=False, indent=2) + "\n")

    for start in range(0, len(pages), 4):
        indices = range(start+1, min(start+5, len(pages)+1))
        sheet = Image.new("RGB", (1092, 770*((len(indices)+1)//2)), "#e8eef0")
        draw = ImageDraw.Draw(sheet)
        for slot, number in enumerate(indices):
            with Image.open(QA / f"page-{number:02d}.png") as image:
                image.thumbnail((520, 736), Image.Resampling.LANCZOS)
                x, y = 12+(slot % 2)*546, 24+(slot // 2)*770
                draw.text((x, y-17), f"Page {number}", fill="#253037")
                sheet.paste(image, (x, y))
        sheet.save(QA / f"sheet-{start+1:02d}.png")
    return pages


if __name__ == "__main__":
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else BUILD / "main.pdf"
    print(*[f'{p["page"]:02d} · {p["text_bbox_points"]} · {p["top_text"]} … {p["bottom_text"]}'
            for p in render(pdf)], sep="\n")
