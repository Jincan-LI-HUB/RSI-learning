# Compilation and rendering report

## Delivered prototype

The PDF contains 10 A4 pages, two original reader passages, the continuous IV-A §§6.2–7.3 excerpt, 39 display equations, five source tables and six figures. Fig. 4 also includes a print table of the source interactive readouts at three settings. The supplied LaTeX source bundle has the generated TeX, the eight PDF vector assets that make up the six figures, their editable SVGs and the six exact component sources used for recovery.

- Final PDF size is 763,174 bytes.
- SHA-256 is 6823ecd74c93a1a2df2be0eb6eba3ad9f13be8f84b8d17839c65fd56762f5ee6.
- The final XeLaTeX log has no TeX errors, missing-character diagnostics, box warnings or unresolved-reference warnings. The Windows Perl launcher printed its locale fallback notice. [Final compile log](../build/main.log)
- Font inspection confirmed embedded fonts and usable Unicode maps. The PDF is unencrypted and includes nine outline items and eight internal contents links. Search probes passed for Chinese text, English terms, labels and numerical values. The figure assets and all final PDF pages have zero raster image placements. [Machine-readable checks](../build/qa/pdf-checks.json)
- The 39 display formula payloads matched the message source in order after trimming the surrounding whitespace. The inline comparison checked expression multiplicities. The five original table bodies were converted from parsed Markdown. The table modifications in the converter apply widths and captions. [Conversion evidence](prototype-conversion.json)

## Visual inspection

All final pages were rendered at 1.65× PDF point scale and reviewed. The mechanism, GARCH panels and density comparison were also inspected at page scale. The inspection covered title and question typography, bookmarks and contents labels, math typography, equation breaks, table widths and alignment, figure labels and artwork, caption placement, and text margins.

| Pages | Inspection |
|---|---|
| 1 | Opening leaf, original questions and linked contents |
| 2–4 | Volatility and ACF on successive pages, source axes and labels, aligned covariance proof and boxed conclusions |
| 5–7 | ARCH and GARCH comparison and parameter tables, diagram geometry and math labels, unconditional-variance derivation, three readable slider states |
| 8 | Density curves and legend, numerical tail probabilities and comparison bars |
| 9–10 | Moment condition and proof, table line breaks, bounded closing section |

The initial render exposed short lead-ins split from displays and undersized axis labels in the three-up figure. The conversion now joins mathematical lead-ins to their following displays and enlarges the GARCH panel labels. The final render keeps the §7.2 proof and §7.3 opening comparison on their respective pages. Figures and their captions remain together. The GARCH mechanism and the density comparison start on the page immediately following their introductory material, preserving source order at readable scales.

[Pages 1–4](../build/qa/sheet-01.png) · [Pages 5–8](../build/qa/sheet-05.png) · [Pages 9–10](../build/qa/sheet-09.png)
