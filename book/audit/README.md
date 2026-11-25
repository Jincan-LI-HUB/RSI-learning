# Production audit

[Machine verification](verification.json) · [Chapter source and figure records](./) · [Build instructions](../README.md)

The [final release reconciliation](release-reconciliation.md) records the targeted changes after the production baseline, including the [coverage manifest](source-coverage-manifest.csv), [alternate response comparison](alternative-differences.csv), [citation dispositions](citation-reconciliation.csv), and [figure manifest](figure-manifest.csv).

## Editorial reconciliation

- **Part I.** The first explanation, the research-project-based second pass and the concept index retain their order. The project description from source record 5 is reproduced from its description field. Personal background and contact fields are held locally. Where the first and second pass use distinct definitions, examples, proofs or visualizations, both remain in the book. The conclusion index remains in its pedagogical position.
- **IV-A.** The opening chapter uses record 52 through §6.1. The first rendering of §6.2 onward remains as a named complementary chapter, with its distinct derivation variants, earlier illustrations and code sample. The selected continuation from record 58 follows, beginning at §6.2. The two discarded response branches and the display-troubleshooting request remain in the private archive.
- **Repetition and scope.** Formula sheets, stage reviews, previews and repeated explanations remain where they support the learning sequence. Routine continuation requests and assistant status messages were omitted. Part V and VI remain roadmap references only because the archive contains no delivered teaching chapters for them.

## Recovery and fidelity

The per-chapter JSON records show the public archive ordinal, source line range, content hash, formula counts, and disposition of each rendered component. Source formulas outside components were compared with LaTeX across all chapters. Detected ambiguity between a Markdown table separator and a minus sign in a display was corrected at the converter, without changing the mathematical expression. Source pipe tables and component comparisons are typeset as editable tables where their structures support it. Fenced examples and the five text diagrams remain editable text.

The SVG renderer normalizes drawing attributes and uses the supplied palette. The original chart data is rendered to PDF vectors. Color-coded rows such as cross-validation folds and bootstrap blocks retain their ordered cells and color distinctions as print diagrams. The archived Mermaid evaluation chain was converted from its original labels and ordered edges. Where a graphic has a numerical slider, the print pipeline uses the default and a representative state where useful. The approved GARCH panel retains its three settings. The original labels and readouts from the component layer are rendered in source order. Self-assessment checklists retain their individual items. The final progress indicator was omitted, and its roadmap remains.

Three IV-D skewness/symmetry image requests lack original pixels or vector source. A labeled analytical reconstruction now accompanies the mathematical discussion. The two IV-A financial-data audit examples refer to external dataframes. Their plotting code remains. The citation reconciliation records verified academic references and client-dependent pointers whose targets are absent from the archive.

## Mathematical source notes

The initial IV-A volatility SVG contained JavaScript unary-minus syntax that prevented rendering its exponential terms. The renderer made the intended exponent grouping explicit for those two archived expressions. The plot remains synthetic. This was a rendering correction, with no changes to the prose equations. Mathematical claims and numerical model results are reproduced as archived. The fidelity audit does not confer independent validation of every theorem or cited empirical claim.
