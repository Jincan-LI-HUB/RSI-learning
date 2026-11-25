# Prototype V1 baseline verification

## PDF, source and previews

- The delivered PDF retains SHA-256 6823ecd74c93a1a2df2be0eb6eba3ad9f13be8f84b8d17839c65fd56762f5ee6. The handoff retains the original PDF bytes.
- A clean XeLaTeX build ran in an isolated directory containing only the LaTeX source tree and its figure assets. The rebuild and delivered PDF both have 10 A4 pages and identical PDF outlines.
- At 1.65× display scale, every page of the rebuild matched the corresponding delivered page pixel for pixel. Each of the 10 review PNGs was rendered directly from the delivered PDF at that same scale. The files run from page-01.png to page-10.png at 983 × 1390 pixels.
- The clean XeLaTeX log had no errors, missing-character messages, box warnings or unresolved-reference warnings. The original visual inspection and Unicode and vector checks are documented in the [compilation and rendering report](../reader_prototype/reports/compilation-and-rendering.md).
- The [SHA-256 manifest](prototype_v1_sha256.txt) covers the PDF, previews, LaTeX files and dependencies, the supplied palette, and AGENTS.md. Paths are relative to the workspace root.

## Publication scope

This public checkpoint uses source ordinals for traceability. The raw archive and private message identifiers are held locally.
