# Mathematical Exploration · Personal Reader Edition

[Read the complete PDF](Mathematical_Exploration_Personal_Edition.pdf) · [Editable LaTeX](main.tex) · [Chapter files](chapters/) · [Vector assets](figures/) · [Final release audit](audit/release-reconciliation.md)

## Build from the publication source

Use TeX Live with XeLaTeX, latexmk, STIX Two Text, STIX Two Math, SimSun, SimHei and Consolas. From the repository root:

    cd book
    latexmk -norc -xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -outdir=build main.tex

The result is build/main.pdf. Keep the repository layout intact. The preamble, palette and six approved prototype figure files are shared with the prototype. Other graphics are under figures.

## Regenerate from the local transcript

With the original local archive available, reuse the normalized transcript prepared during inspection. Python needs PyMuPDF and Pillow, and Pandoc and Node.js must be on PATH. From the root:

    python book/scripts/build_book.py --part 1
    python book/scripts/build_book.py --part 2
    python book/scripts/build_book.py --part 3
    python book/scripts/build_book.py --part 4
    python book/scripts/release_edits.py

Omit the Part flag to run all four sequentially. The converter reads only the selected conversation ancestry. Individual chapter .tex files and audit records are written after each chapter. Recompile, then run the following verification from the root:

    python book/scripts/release_fidelity.py
    python book/scripts/release_records.py
    python book/scripts/check_book.py

The public files use archive record ordinals and source line ranges. The raw archive, normalized transcript and private metadata remain local.
