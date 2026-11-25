# Mathematical Exploration · Prototype

This project state covers archive inspection, extraction, structural mapping, visualization recovery assessment and the design prototype. The sample is drawn from IV-A §§6.2–7.3. Full-book production awaits review and approval of the prototype.

## Deliverables

| Item | File |
|---|---|
| Reading prototype | [Mathematical Exploration Prototype](Mathematical_Exploration_Prototype.pdf) |
| Editable LaTeX and all figure dependencies | [Source bundle](LaTeX_source.zip) · [main.tex](latex/main.tex) |
| Source inspection | [Report](reports/source-inspection.md) · [Message tree](reports/message-tree.csv) |
| Mathematical content | [Content by message](reports/content-inventory.csv) · [Mathematics, tables and code](reports/math-tables-code-index.csv) · [Original headings](reports/source-headings.csv) |
| Visualization inventory | [Figure manifest](reports/figure-manifest.csv) · [Recovery assessment](reports/visualization-recovery.md) · [Exact component source](archive/visualization-sources.jsonl) |
| Structure | [Proposed contents](reports/proposed-contents.md) |
| Typography, source mapping and departures | [Editorial and layout record](reports/editorial-and-layout.md) |
| Validation | [Typesetting and rendering report](reports/compilation-and-rendering.md) · [Conversion evidence](reports/prototype-conversion.json) |
| Archival transcript | [Byte-identical copy](archive/科研准备学习路线__6b057087.json) · [All records](archive/normalized-all.jsonl) · [Latest visible ancestry](archive/normalized-path.jsonl) |

The inventories use original JSON array positions and message IDs. Their source line numbers are 1-based within a content block, with the exact message text under archive/messages. The figure manifest includes both enclosing layouts and nested figures.

## Build from editable LaTeX

Extract the source bundle or enter the latex directory. The supplied TeX source references PDF vectors by relative path, so keep the figures directory adjacent to main.tex. Use TeX Live with XeLaTeX and the STIX Two Text and Math packages. Windows fonts used are SimSun, SimHei and KaiTi. They are referenced by font name. The publication sample can be built from the delivered TeX and vector assets with no archive parsing.

    latexmk -norc -xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex

## Reproduce extraction, conversion and QA

Use Python 3.10 or newer with PyMuPDF and Pillow, Pandoc, TeX Live, and the Windows fonts named above. The verified run used Python 3.13.5, Pandoc 2.12, PyMuPDF 2.1, XeTeX from TeX Live 2025 and latexmk 4.87. Open a PowerShell prompt in this directory. Keep the original JSON in the parent workspace folder when using the refresh flag.

    .\build-prototype.ps1 -RefreshArchive

Omit the flag to reuse the normalized message files. The script renders page images and contact sheets and publishes the PDF at the project root after the automated checks pass. TeX build evidence and the raster previews used for visual review live under build. The PDF's figures remain vector.

## Handoff state

Extraction and mapping are complete for all 78 stored messages. The prototype contains only the mapped passages and six recovered figures listed in the editorial and recovery reports. No full-book chapter files have been produced. Open items for a later stage are review of the layout and graphic treatments, handling of the missing IV-D image assets, and conversion and verification of the remaining SVGs, charts and interactive states.
