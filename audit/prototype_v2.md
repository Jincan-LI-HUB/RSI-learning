# Prototype V2 changes and verification

## Scope and typesetting

The reading edition begins with the original mathematical heading for §6. V1 had ten total pages, including nine content pages. V2 has five content pages. The V1 cover, local contents page, reader exchanges and production note were removed. The original order from IV-A §6.2 through §7.3 remains.

The A4 column uses 20 mm side and top margins and a 21 mm bottom margin. XeLaTeX sets STIX Two Text, STIX Two Math and SimSun at 10 pt with 12.2 pt leading. Chinese paragraph indents are 2 em, paragraph spacing is 1.5 pt and nominal display spacing is 3–3.6 pt. Section and subsection space above is 11 and 7 pt. Tables use 9.2 pt with array stretch 1.08, captions use 8.7 pt and running matter uses 8 pt. Short lead-ins run into the exposition. Significant equations and boxed results remain displayed. The moment-existence proof is kept together.

## Mapping and fidelity

The parent heading comes from archive record 52, line 644. The mathematical excerpt comes from record 58, lines 7–587. The [V1 component map](prototype_v1_source_map.csv) gives the source line ranges for the six figures. In V2, figures 1 and 2 are on page 1, figure 3 on page 2, figure 4 on page 3, and figures 5 and 6 on page 4. The two V1 reader blocks fall outside the V2 reading text.

All 39 source display payloads matched the baseline conversion exactly after boundary trimming. Nineteen moved inline and twenty remain displayed. The converter checked unchanged non-whitespace prose and math tokens across the compacting pass and retained all source inline expressions and all five table bodies. There were no mathematical emendations.

The first two paired plots use horizontal panels containing the source data. The mechanism uses a smaller vector footprint. The GARCH graph compares the original three settings on shared axes, with solid, dashed and dotted strokes and the original default labeled. It retains all 41 values per curve from the source expression and the original half-life and 20-period readouts. The tail comparison plots the two printed probabilities on a logarithmic percent axis. Independently evaluating the unrounded Normal and unit-variance Student-t three-degree-of-freedom tails gives a ratio of about 5,649.78, consistent with the printed 5,650. The source ACFs and time series are teaching illustrations and retain those qualifications.

LaTeX imports the supplied palette, and Python reads the same definitions to emit six SVGs with the exact palette colors. All six figures were regenerated as vectors with searchable labels. The current excerpt uses SVG/PDF figures and has no TikZ or PGFPlots figures. The PDF pages are searchable and bookmarked, with no raster images. All five final pages were rendered and visually inspected. The XeLaTeX log showed no font, clipping, box, or reference diagnostics. Each committed preview renders directly from the final PDF.

## Reconciliation for later editorial work

- **Part I overlap.** Compare both delivered passes at the passage level. Preserve distinct motivations, derivation steps, examples and demonstrations in their original pedagogical positions. Condense only duplicated conversational framing or identical repetitions with no instructional purpose.
- **IV-A continuation.** Retain the initial response through the transition into §6.2. Compare the initial discussion and the selected continuation from §6.2 onward, accounting for every unique proof, example or figure. Preserve the interrupted alternatives in the private archive. Choose the continuous reading sequence through the selected continuation and record where any unique earlier material is retained.
- **Pedagogical repetition.** Keep revisits that change viewpoint, reinforce intuition or connect concepts. Document editorial decisions in the source map. Parts V and VI remain roadmap entries where the archive references them.

Full-book reconciliation remains outside this prototype.
