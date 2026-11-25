# Source inspection

## Archive identity and schema

| Field | Observed |
|---|---|
| File | 科研准备学习路线__6b057087.json |
| Size | 8,344,568 bytes |
| SHA-256 | 87b0e070478274a92d6fab790b974b99b833e706c7cb47a0efe3440b38551d4a |
| Format | UTF-8 JSON, schema_version 1.0.0 |
| Provider and import type | openai_chatgpt · save_current |
| Conversation | 科研准备学习路线 · [archival ID withheld] |
| Creation and update, Asia/Shanghai | 24 November 2026, 19:10:00 → 25 November 2026, 10:56:58 |
| Import, Asia/Shanghai | 25 November 2026, 10:58:04 |
| Top level | schema_version, source, conversation |
| Records | conversation.messages, a list of 78 entries |

Each message records an ID, parent ID, role, timestamp, content array and metadata. Assistant and tool entries can carry a model field. In this export each message has one content block. The 78 blocks comprise 60 Markdown, 17 internal and one tool call. Chart specifications, SVG templates and interactive controls can occur inside Markdown, alongside citation, chart, code and UI metadata. The byte-identical copy and its checksum are in archive. Text files and JSONL preserve the archived wording and identifiers for deterministic retrieval.

The metadata header declares 58 messages, 22 user messages and 35 assistant messages. The underlying array contains 24 user, 53 assistant and one tool records. Header totals cannot determine which response the reader saw. The archive provides no explicit current-node field.

## Path selection and branch disposition

The parent graph has one root, 78 distinct IDs and no missing parent. The three visible terminal replies are #54, #56 and #77. Following parent IDs back from the latest visible reply, #77, produces the only path that proceeds through the rest of Part IV after the IV-A branch. It has 57 records, including 22 reader messages, 22 full teaching replies, 11 assistant preambles, and the one assistant tool call plus one tool result used during IV-E. The tree file records the complete ancestry and dispositions. Archive ordinals refer to JSON array positions and are independent of reading order.

- #3 and #7 are consecutive visible teaching replies on the same path, with the revised reader brief #5 between them. Their overlap is part of the original progression.
- #52 is the full archived IV-A reply. The reader subsequently reported an apparent display stop at §6.2. The selected continuation follows #57 → #58. The other branches terminate at #54 (a completion confirmation) and #56 (an interrupted partial continuation that ends mid-table). Neither alternate was substituted for the active continuation.
- #72 and #73 are parents in the chain leading to #71, even though the array stores #71 first. The Python tool call and numerical result are retained as supporting trace.
- The 17 records marked visually hidden are child leaves, including the final stored array element #78. They are retained in the normalized archive. Direct comparison found each of their 118 SVG occurrences verbatim in its visible parent, so this internal visual layer adds no distinct SVG template.
- #77 reaches the Part V transition and ends normally in the export. Parts V and VI appear in the original roadmap. No full teaching replies for them follow in this archive.

| Layer | Records | Disposition |
|---|---:|---|
| Latest visible ancestry | 57 | Normalized in parent-chain order |
| Sibling alternate branches | 4 | Preserved with alternate designation |
| Visually hidden internal child records | 17 | Preserved with hidden designation |

Full paths, ordinals, roles, IDs, children and finish metadata are in the message tree. The normalized transcript follows the chosen ancestry. All records retain the exported order, metadata and raw content including alternatives.

## Content and presentation inspection

| Structure | Active ancestry | Alternate | Hidden |
|---|---:|---:|---:|
| Text characters, including markup and code | 829,466 | 9,504 | 564,069 |
| Markdown headings outside fenced code | 890 | 13 | 583 |
| Display math blocks delimited by backslash brackets | 1,357 | 24 | 842 |
| Aligned-family TeX environments | 79 | 5 | 47 |
| Inline math delimited by backslash parentheses | 960 | 21 | 628 |
| Markdown pipe tables | 273 | 4 | 186 |
| Fenced blocks | 38 | 0 | 34 |

These are counts of indexed occurrences in the source. They include repetitions, previews and tool material where present. The heading index gives the original depth and text. The mathematical index points to every display formula, Markdown table and fenced block with source lines and a locator excerpt. Inline math counts are by delimiter, with the complete expressions available in the normalized text. The content records retain the original headings as anchors for definitions, arguments, proofs, examples and transitions.

- [Content inventory by message](content-inventory.csv)
- [Source headings and hierarchy](source-headings.csv)
- [Display mathematics, tables and code index](math-tables-code-index.csv)
- [Proposed table of contents](proposed-contents.md)

The archive has Markdown, LaTeX, code fences, HTML-like layout primitives, JSX-style attributes, SVG, Mermaid, chart JSON, and interactive expressions and UI state. It also carries search-result groups, safe URLs, client content references, and inline citation components. The export reports no file or image uploads. A separate component-level inspection found three query-based image placeholders despite the false top-level image flag. The share endpoint timed out in the web reader and returned an empty HTTP 503 response on direct retrieval. No supplementary rendered reference was available during this session. 

Run [inspect_archive.py](../scripts/inspect_archive.py) to reproduce the extraction, inventories and structural map. The extraction statistics record graph forks and cross-check totals. The extractor uses archived text as data and does not run embedded code.
