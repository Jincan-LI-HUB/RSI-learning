# Final fidelity reconciliation

Accepted production baseline: [18cabb5](https://github.com/Jincan-LI-HUB/RSI-learning/tree/18cabb5196b804904b551fc79d4bfb060dc6bbeb). The release retains its chapter organization, reading layout, and existing vector assets.

## Release changes

- Inserted the supplied bilingual Editorial Note between the title page and the contents. The contents retain the approved fonts and have a slightly tighter paragraph gap to keep their final entries on the preceding page.
- Preserved the reader’s rationale for a conclusion-first index with proof pointers. For IV-A, added the explicit unit-variance inference from the Gaussian-product example and the warning about transferring an IID Hoeffding bound to dependent data by substituting effective sample size. The preceding explanation now connects effective sample size for the sample mean to selection risk.
- Reconciled seven academic citation markers and two non-bibliographic memory pointers. The two markers in the literature card already had explicit DOI links. At the heavy-tail statement, Cont’s verified paper supports the claim. The other transient alias had no identifiable target in the archive. [Citation dispositions](citation-reconciliation.csv)
- Added a labeled three-panel vector reconstruction in IV-D. For \(G\sim\mathrm{Gamma}(4,1)\), the panels use \(-(G-4)/2\), \(\mathcal N(0,1)\), and \((G-4)/2\). The first three central moments of \(G\) are \(0,4,8\). The panels share mean zero and unit variance, with skewness \(-1,0,+1\). The three exact original illustrations remain unavailable. [Figure manifest](figure-manifest.csv)

## Source disposition and verification

The original archive SHA-256 is 87b0e070478274a92d6fab790b974b99b833e706c7cb47a0efe3440b38551d4a. It matches the archival copy and the recorded extraction checksum.

All 78 stored records have an explicit disposition, including 57 active ancestry records, 4 alternatives, and 17 hidden internal records. The check reconstructs ancestry from the original parent links and identifies teaching replies from their roles and content metadata. It then matches source-range hashes to the manuscript chapter records. There are 22 full teaching replies in 23 chapter files. The cut at the start of record 58 covers six lines of display troubleshooting and its separator. The authority path ends at record 77. Parts V and VI remain plans.

- The archive coverage manifest identifies manuscript destinations for full teaching ranges, the project description and intellectual brief in records 1 and 5, and the index motivation in record 9. Continuation prompts, hidden records, private contact material, and execution traces remain local. [Coverage manifest](source-coverage-manifest.csv)
- The alternate comparison accounts for all lines in records 54 and 56. Record 54’s roadmap and SNR result are already covered. Record 56’s proof order, assumptions, data labels, tables, chart samples, and research qualifications were compared with the active versions. All 27 GARCH chart values agree with the published curves within the archived rounding. [Alternate-response comparison](alternative-differences.csv)
- Automated checks matched 2,236 source expressions in order with multiplicity, 4,008 normalized prose blocks, 37 fenced code or text blocks, and all 4,905 cells in 273 source pipe tables. The 278 publication tables also include component-derived and print tables. The release diff permits only the enumerated chapter edits. Prose checks normalize formatting and punctuation. Semantic review focused on the alternate replies, substantive reader requests, and recoverable citations. [Fidelity checks](release-fidelity-checks.json)

## Compiled release

| Measure | Baseline | Release |
|---|---:|---:|
| PDF pages | 349 | 349 |
| Matched source expressions | 2,236 | 2,236 |
| Added source and figure formula occurrences | 0 | 8 |
| Publication tables | 278 | 278 |
| Vector figure placements | 254 | 255 |
| Bookmarks and verified internal links | 323 | 324 |

Final PDF SHA-256: 795a57369b452f65fa3bb4f1588e8ef1782b3092d4a6c474ad0d691d6b22ded3.

The baseline pixel comparison selected 115 changed page interiors. Visual review covered 150 pages including adjacent pages and the contents, with focused review of the note, proof-index introduction, recovered qualification and reconstructed figure. XeLaTeX compiled the release with no missing glyphs, overfull boxes or unresolved internal references. Its log reports regular STIX Two Math substitution when math is placed inside bold text, and an unused table-caption setting from the shared preamble. PDF text bounds and navigation checks passed. [Compile and PDF checks](verification.json) · [Visual scope](release-visual-checks.json)

Both IV-A empirical plotting examples retain their source code. Their market-data inputs and original empirical plots remain unavailable. The two memory-pointer payloads and the unidentified second alias at the heavy-tail statement are recorded above. The audit verifies preservation and reconciliation within the supplied material. Independent validation of every mathematical and empirical claim was outside the audit scope.
