# Build the editable prototype

Build from the latex directory inside the repository. Keep the figures folder adjacent to main.tex and keep palette.tex at the repository root. XeLaTeX reads the palette directly. Figure regeneration reads the same file from Python.

Use TeX Live with XeLaTeX, latexmk, STIX Two Text and STIX Two Math, with SimSun and SimHei available by font name.

    latexmk -norc -xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex

main.tex contains the layout and excerpt.tex contains the mathematical text. The figures directory provides the PDF vectors embedded by LaTeX, the editable SVGs, and the archived component slices used for recovery.
