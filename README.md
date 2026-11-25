# RSI Learning · Prototype V2

The compact mathematical reader presents the original IV-A §§6.2–7.3 excerpt across five A4 pages.

| Review material | Files |
|---|---|
| Reading edition | [Prototype V2 PDF](reader_prototype/Mathematical_Exploration_Prototype.pdf) |
| Page previews | [01](reader_prototype/previews/page-01.png) · [02](reader_prototype/previews/page-02.png) · [03](reader_prototype/previews/page-03.png) · [04](reader_prototype/previews/page-04.png) · [05](reader_prototype/previews/page-05.png) |
| Editable LaTeX | [Preamble](reader_prototype/latex/main.tex) · [Excerpt](reader_prototype/latex/excerpt.tex) · [Build notes](reader_prototype/latex/BUILD.md) |
| Figures | [SVGs, PDF vectors and source components](reader_prototype/latex/figures/) · [Generation script](reader_prototype/scripts/build_excerpt.py) · [Palette](palette.tex) |
| Editorial review | [Changes, source alignment and verification](audit/prototype_v2.md) · [Conversion checks](reader_prototype/reports/prototype-conversion.json) |
| Earlier work | [Prototype V1 checkpoint](https://github.com/Jincan-LI-HUB/RSI-learning/tree/f4a9c44c5823d803bd66aeb9badd187531557e90) · [Original feedback](audit/prototype_v1_feedback.md) · [Project instructions](AGENTS.md) |

## Build the PDF

Keep the repository structure intact so the preamble can read the root palette. Use TeX Live with XeLaTeX, latexmk, STIX Two Text and STIX Two Math, and the SimSun and SimHei fonts. From the repository root:

    cd reader_prototype/latex
    latexmk -norc -xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex

To render page previews with Python, PyMuPDF and Pillow, run from the repository root:

    python reader_prototype/scripts/check_pdf.py reader_prototype/Mathematical_Exploration_Prototype.pdf

The full source-to-PDF regeneration procedure uses the private source archive and is described in the [pipeline notes](reader_prototype/README.md).
