# Prototype build and regeneration

See the [review index](../README.md) for the current PDF, previews, LaTeX and audit. A build from the delivered editable source requires the [root palette](../palette.tex), the LaTeX directory and its figure assets. See the [LaTeX build notes](latex/BUILD.md).

Regeneration from source also requires the original conversation JSON in the parent workspace or the previously extracted local transcript under archive. Use Python 3.10 or newer with PyMuPDF and Pillow, Pandoc, TeX Live, and the fonts identified in the build notes.

    .\build-prototype.ps1

The command reuses the extracted messages when available, regenerates the manuscript and vectors, compiles the PDF, and renders the QA pages under build. Add -RefreshArchive only when re-extraction is necessary. Conversation archives and extraction metadata remain local.

The original inspection, inventories and V1 verification record are retained in the [V1 checkpoint](https://github.com/Jincan-LI-HUB/RSI-learning/tree/f4a9c44c5823d803bd66aeb9badd187531557e90).
