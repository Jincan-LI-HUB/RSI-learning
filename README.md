# RSI Learning · Prototype V1 baseline

This checkpoint preserves the 10-page prototype from IV-A §§6.2–7.3. The PDF contains the original Chinese–English exposition and derivations, five source tables, and six vector figures. The first round of feedback is recorded for independent review.

## Review index

| Material | Files |
|---|---|
| Baseline PDF | [Mathematical Exploration Prototype](reader_prototype/Mathematical_Exploration_Prototype.pdf) |
| All page previews | [01](reader_prototype/previews/page-01.png) · [02](reader_prototype/previews/page-02.png) · [03](reader_prototype/previews/page-03.png) · [04](reader_prototype/previews/page-04.png) · [05](reader_prototype/previews/page-05.png) · [06](reader_prototype/previews/page-06.png) · [07](reader_prototype/previews/page-07.png) · [08](reader_prototype/previews/page-08.png) · [09](reader_prototype/previews/page-09.png) · [10](reader_prototype/previews/page-10.png) |
| LaTeX source | [Preamble and typography](reader_prototype/latex/main.tex) · [Excerpt](reader_prototype/latex/excerpt.tex) · [Reader passages](reader_prototype/latex/reader-questions.tex) |
| Vector assets | [SVG, embedded PDF, and component source](reader_prototype/latex/figures/) · [Figure-generation script](reader_prototype/scripts/build_excerpt.py) |
| Source inspection and structural mapping | [Source inspection](reader_prototype/reports/source-inspection.md) · [Mathematical inventory](reader_prototype/reports/math-tables-code-index.csv) · [Inventory by message](reader_prototype/reports/content-inventory.csv) · [Proposed contents](reader_prototype/reports/proposed-contents.md) · [Source-to-manuscript map](audit/prototype_v1_source_map.csv) |
| Visualization inventory | [Figure manifest](reader_prototype/reports/figure-manifest.csv) · [Recovery assessment](reader_prototype/reports/visualization-recovery.md) |
| Editorial and build records | [Editorial decisions](reader_prototype/reports/editorial-and-layout.md) · [Compilation and rendering report](reader_prototype/reports/compilation-and-rendering.md) · [Baseline verification](audit/prototype_v1_verification.md) · [SHA-256 manifest](audit/prototype_v1_sha256.txt) |
| Review feedback and project instructions | [Prototype V1 feedback](audit/prototype_v1_feedback.md) · [AGENTS.md](AGENTS.md) · [Supplied palette](palette.tex) |

The supplied palette is included as a reference for the next approved revision. The V1 preamble and vector files retain the colors used in the delivered prototype.

## Rebuild the baseline

Use TeX Live with XeLaTeX, latexmk, STIX Two Text and STIX Two Math. The preamble names the Windows fonts SimSun, SimHei, and KaiTi. With those fonts available, run the following from the repository root.

    cd reader_prototype/latex
    latexmk -norc -xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex

The output is main.pdf. The embedded figure PDFs are resolved relative to main.tex. The build can run from the LaTeX directory and its included assets alone.

To render a copy of the page previews, install Python with PyMuPDF and Pillow and run the following from the root. The rendered output goes under the ignored build directory. Use the checked-in PDF as input to regenerate its exact PNG previews.

    python reader_prototype/scripts/check_pdf.py reader_prototype/Mathematical_Exploration_Prototype.pdf

Archive extraction and regeneration of the LaTeX require the locally supplied conversation JSON, Python, Pandoc and the tools listed in the [conversion instructions](reader_prototype/README.md). Paths to the raw archive, normalized transcript or complete local build logs in the earlier reports refer to local evidence. The review tree carries the selected source, the inventories and the verification results.
