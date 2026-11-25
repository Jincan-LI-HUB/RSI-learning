# Visualization recovery assessment

The manifest records each identifiable graphic or component with its message ID, 1-based source range, containing component, labels or available expressions, mathematical context, parameters, behavior, recovery status and proposed print representation. Nested items are linked by their containing range. A card that contains two SVG panels has three manifest rows. The manuscript figure count will depend on how those panels are grouped. [Figure manifest](figure-manifest.csv) · Exact source slices and expressions

## Active-path inventory

| Archived item | Count | Assessment |
|---|---:|---|
| Standalone/static SVG markup without template expressions | 49 | All 49 parsed as XML. Retain shapes, typeset or embed original labels and resolve inherited print styles. |
| SVG templates with fixed data or formulas | 102 | Original drawing primitives and local expressions are present. Materialize the geometry as vector paths and text after template-specific checks. |
| SVG templates with live controls in their component | 31 | Original SVG and expressions support default and representative states. Use static vector panels or comparisons, guided by control ranges and the surrounding explanation. |
| Client chart specifications | 31 | 23 line and 8 bar charts. Archive includes plotted data, series and labels, with some explicit axis limits. Vector replotting can preserve the plotted quantities. Client typography, hover and layout require a print decision. |
| Component containers | 306 | 194 boxes, 80 cards, 26 grids and 6 rows. This includes wrapper duplicates and text-only layouts. It preserves non-SVG mechanisms such as bars, comparisons and checklist structures as candidates. 61 contain controls. |
| Mermaid and fenced text diagrams | 6 | One original Mermaid specification and five text diagrams. Use SVG/PDF for the Mermaid specification and fixed-width geometry for the text diagrams. |
| Fenced plotting programs | 2 | Both IV-A audit examples assume an input dataframe and have no archived result image or underlying market data. Keep code and flag the original render as unverified. |
| Dynamic image requests | 3 | Only query, target aspect ratio and fit metadata survive. The exact original graphics are unrecoverable from the supplied export. |

The same inventory covers alternate and hidden branches with explicit dispositions. Active-path counts describe source occurrences even when an original chart or template was reused at a later teaching point. Availability judgments for the full archive are assessments. Only the six prototype figures have been converted and visually checked in this session.

## Interactive and client-specific evidence

The archive includes JSX-like SVG wrappers, component controls, DIL state declarations, and nine messages with nonempty saved UI state. The manifest identifies the enclosing source for each controlled figure and stores its declarations and control settings. For publication, the code default is reproducible where specified. A saved state can also matter, for example the conclusion checklist in #10 has its first item checked. Unmapped component IDs and external client features have no demonstrated static equivalent. Keep the archived UI source and metadata with the transcript.

The three missing image requests are adjacent in #67, IV-D §6.1, at lines 982, 987 and 992, under the negatively skewed, symmetric and positively skewed panels. The corresponding hidden child repeats the queries. No image payload, asset URL or screenshot accompanies them. A later reconstruction would require the original rendered references or an explicit replacement decision.

## Prototype recovery log

| Printed figure | Source #58 lines | Vector evidence and print treatment |
|---|---:|---|
| Fig. 1 · Volatility clustering | 11–25 | Original two-panel SVG template and 180-point deterministic trajectories. Shaded intervals, labels, colors and caption retained. |
| Fig. 2 · Return and squared-return ACF | 49–66 | Original two-panel SVG template. Twenty source lag bars per panel, four original tick labels and original caption. |
| Fig. 3 · GARCH components | 257–269 | SVG template retains all three input boxes, connectors, output, colors and Unicode mathematical labels. Added a short print caption. |
| Fig. 4 · GARCH shock persistence | 342–376 | Source curve \(1+3p^h\), with \(p=a+b\), at each integer \(h=0,\ldots,40\). Panels use 0.50, 0.90 (source default), and 0.99 (source upper bound). Original half-life and 20-period remaining-shock readouts become a small table. |
| Fig. 5 · Normal and standardized \(t_3\) densities | 410–426 | Curves use the source density formulas at the original 241 points, x-axis and tick labels. The original legend and caption sit beneath the SVG. |
| Fig. 6 · Five-standard-deviation probabilities | 437–459 | Original nested component bars reproduced as vector rectangles. The scale and very short normal bar follow the archived 0.0177% relative width. Values and ratio are retained as selectable text. |

The prototype SVG renderer evaluates an allowlisted set of translated expressions in the local Python script. It retains the exact source component alongside each output. The source JSX/JavaScript is archived as text and was never evaluated. SVGs are parsed, tag checked and rendered to PDF. Each resulting asset was verified to contain vector drawing objects and text, with zero raster images. Figures were placed at their source positions in the text flow.
