# RSI Learning — Mathematical Exploration

**科研准备学习路线 · Personal Reader Edition**

A 349-page mathematical reader developed from an extended AI-assisted learning dialogue on recursive self-improvement (RSI), statistical learning theory, and out-of-sample performance decay in financial research.

The project preserves the original mathematical motivations, derivations, examples, conceptual explanations, and visualizations in a permanent, professionally typeset reading edition. It is intended for sustained personal study and research preparation, rather than as a condensed summary or a newly authored research paper.

**[Read the complete PDF](book/Mathematical_Exploration_Personal_Edition.pdf)** · [Canonical edition (v1.0)](https://github.com/Jincan-LI-HUB/RSI-learning/tree/v1.0-personal-edition) · [Build instructions](book/README.md) · [Final audit](book/audit/release-reconciliation.md)

## Contents

| Part | Subject | Focus |
| :--- | :--- | :--- |
| I | Understanding the Research Problem | Mathematical formulation, research motivation, and the conclusion-first concept and proof index |
| II | Statistical Learning Theory | Statistical inference, generalization, model selection, and the mathematical foundations of overfitting |
| III | Agentic AI and Recursive Self-Improvement | Iterative improvement, evaluation, and the risks of adaptive research processes |
| IV | Financial AI & Quantitative Research | Financial time series, data-generating processes, distributional properties, and financial model evaluation |

The reader contains the completed Parts I–IV of the original learning sequence. Parts V and VI remain roadmap entries, not completed chapters. Both Part I teaching passes and distinct material from the IV-A continuation are retained.

## Edition at a glance

| Metric | Final edition |
| :--- | ---: |
| PDF pages | 349 |
| Matched original mathematical expressions | 2,236 |
| Matched normalized prose blocks | 4,008 |
| Publication tables | 278 |
| Vector figure placements | 255 |
| PDF bookmarks | 324 |

The book uses compact A4 single-column typesetting, STIX Two Text and STIX Two Math, SimSun, and a consistent custom visualization palette. Interactive illustrations are adapted into static vector graphics and representative parameter states.

## Editorial principles and verification

The guiding principle is **preserve the intellectual content and pedagogical progression; refine the presentation**. The conversion uses deterministic extraction and typesetting wherever possible, with source mapping and targeted editorial reconciliation rather than summarization.

The release audit records the disposition of all 78 archived records, matches original mathematical expressions in order and with multiplicity, and checks prose, code blocks, and source table cells. Missing resources and editorial reconstructions are explicitly documented.

| Reference | Description |
| :--- | :--- |
| [Final release reconciliation](book/audit/release-reconciliation.md) | Scope, editorial changes, verification results and remaining limitations |
| [Machine verification](book/audit/verification.json) | Compilation, mathematical coverage and PDF checks |
| [Source coverage manifest](book/audit/source-coverage-manifest.csv) | Source-to-manuscript traceability |
| [Figure manifest](book/audit/figure-manifest.csv) | Visualization recovery and reconstruction |
| [Production audit index](book/audit/README.md) | Supporting editorial and technical records |

## Repository structure

| Path | Purpose |
| :--- | :--- |
| [book/](book/) | Final PDF, editable LaTeX, chapter files, vector assets, and production scripts |
| [book/audit/](book/audit/) | Fidelity, reconciliation, and verification records |
| [reader_prototype/](reader_prototype/) | Earlier design prototypes and shared typesetting configuration |
| [palette.tex](palette.tex) | Authoritative color definitions |
| [AGENTS.md](AGENTS.md) | Project editorial and production instructions |

## Build from the publication source

Use TeX Live with XeLaTeX, latexmk, STIX Two Text, STIX Two Math, SimSun, SimHei, KaiTi and Consolas. Keep the repository structure intact, as the book shares its layout and several figure assets with the prototype.

```bash
cd book
latexmk -norc -xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

The compiled document is written to `book/build/main.pdf` (relative to the repository root). See [book/README.md](book/README.md) for the source regeneration and verification workflow. Regenerating from the original conversation requires the separately retained private archive; compiling the committed manuscript does not.

## Version and archival status

The canonical reading edition is frozen at [`v1.0-personal-edition`](https://github.com/Jincan-LI-HUB/RSI-learning/tree/v1.0-personal-edition), commit [`b910f66`](https://github.com/Jincan-LI-HUB/RSI-learning/commit/b910f665b4b3115b378a9796d3f5aade3c1a1c26).

PDF SHA-256:

```text
795a57369b452f65fa3bb4f1588e8ef1782b3092d4a6c474ad0d691d6b22ded3
```

Earlier design checkpoints remain available for archival reference: [Prototype V1](https://github.com/Jincan-LI-HUB/RSI-learning/tree/f4a9c44c5823d803bd66aeb9badd187531557e90) and [Prototype V2](https://github.com/Jincan-LI-HUB/RSI-learning/tree/9f5e3a3d133bed40fd9eaec040578192fd0801f3).

## Scope and attribution

This is an AI-assisted personal learning resource, prepared from a conversation conducted for research preparation. It does not represent an official publication or the formal research conclusions of any university, laboratory, or research group.

The fidelity audit verifies preservation of the supplied material, not the independent mathematical or empirical validity of every claim. Three original illustrations, two empirical plotting inputs, and certain citation or context targets could not be recovered; the accompanying audit documents their treatment. No missing empirical results are fabricated.

The raw conversation archive and private metadata are retained separately. Repository availability should not be interpreted as an open-source license or permission to redistribute third-party material.
