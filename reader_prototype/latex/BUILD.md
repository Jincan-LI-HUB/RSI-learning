# Build the editable prototype

Use TeX Live with XeLaTeX, latexmk, STIX Two Text and STIX Two Math. Install or make available SimSun, SimHei and KaiTi by font name. Keep the figures folder relative to main.tex.

    latexmk -norc -xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex

main.tex contains the layout, excerpt.tex the continuous sample, and reader-questions.tex the original reader passages. The figures directory provides the embedded PDF vectors, editable SVGs and archived component slices. Pandoc is only needed when regenerating the TeX from the normalized conversation.
