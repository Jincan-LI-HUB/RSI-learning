# Prototype V1 review feedback

Recorded for independent review before any Prototype V2 changes.

## P1 — Remove non-substantive conversation traces

Leave routine continuation requests and their corresponding acknowledgements out of the reading edition. Retain substantive mathematical questions when they contribute to the exposition. Integrate meaningful questions into the surrounding text.

## P2 — Increase information density

The current body type appears large and the pages contain too little material. Investigate more compact textbook typesetting in the next prototype. The initial candidates are an A4 single column, 10–10.5 pt body text, 1.15–1.20 line spacing, reduced paragraph, heading and display-equation spacing, and more efficient page geometry with fewer unnecessary breaks and less blank space.

These settings are candidates for review. Compare the manuscript with the original source to determine whether the perceived low density comes from typesetting or from accidental omission or condensation. Preserve the original mathematical content and explanations.

## P3 — Adopt the supplied color palette

Use [palette.tex](../palette.tex) as the authoritative color specification for mathematical visualizations, statistical plots and vector illustrations. Keep equivalent color definitions across LaTeX, TikZ, PGFPlots, SVG, and Python figure generation. Use the supplied colors consistently while retaining mathematical distinctions and sufficient contrast.

## P4 — Remove production metadata from the reading edition

Move prototype explanations, source-extraction notes, visualization recovery descriptions, and other production-process commentary into the editorial and audit reports. Keep mathematical captions, meaningful annotations and explanatory visualizations in the book.
