"""Extract this save_current export without running archived code."""
import bisect
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
ARCHIVE = ROOT / "archive"
SOURCE = ROOT.parent / "科研准备学习路线__6b057087.json"
TAGS = (
    "AsyncImage Chart box card caption grid grid-item row title text icon math "
    "spacer divider label line slider rect circle path svg g ellipse table table-cell "
    "table-row list list-item badge checkbox radio radio-group input button "
    "segmented-control"
).split()
TAG = re.compile(r"</?(" + "|".join(sorted(TAGS, key=len, reverse=True)) + r")(?=[\s/>])")
CONTROLS = re.compile(r"<(?:slider|checkbox|radio-group|segmented-control|button|input)\b")
FENCE = re.compile(r"^ {0,3}" + chr(96) + r"{3}([^\n]*)\n(.*?)^ {0,3}" + chr(96) + r"{3}[ \t]*(?=\n|$)", re.M | re.S)
HEAD = re.compile(r"^(#{1,6})[ \t]+(.+)$", re.M)
DISPLAY = re.compile(r"\\\[(.*?)\\\]", re.S)
INLINE = re.compile(r"\\\((.*?)\\\)", re.S)
TABLE = re.compile(r"^ *\|[^\n]+\n *\|(?:[ |:\-]+\|) *\n(?: *\|[^\n]+\n?)+", re.M)
BODY = re.compile(r"^[ \t]*\{@body(?: .*)?\}[ \t]*$", re.M)
SOURCE_FILES = ROOT / "archive" / "messages"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def jsonl(path, records):
    write(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


def csv_file(path, records):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def mask_spans(text, spans):
    chars = list(text)
    for match in spans:
        lo, hi = match.span()
        chars[lo:hi] = [c if c == "\n" else " " for c in text[lo:hi]]
    return "".join(chars)


def tag_end(text, start):
    """Find > outside quoted strings and balanced component attribute expressions."""
    brace = 0
    quote = ""
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = ""
        elif char in "\"'" + chr(96):
            quote = char
        elif char == "{":
            brace += 1
        elif char == "}":
            brace -= 1
        elif char == ">" and brace == 0:
            return index + 1
    raise ValueError(f"Unterminated tag at offset {start}")


def tags(text):
    stack, result, unmatched = [], [], []
    cursor = 0
    while match := TAG.search(text, cursor):
        lo, name = match.start(), match[1]
        cursor = hi = tag_end(text, match.end())
        if text[lo + 1] == "/":
            if stack and stack[-1][0] == name:
                _, start, level = stack.pop()
                result.append((start, hi, name, level))
            else:
                unmatched.append((lo, name))
        elif text[hi - 2 : hi] == "/>":
            result.append((lo, hi, name, len(stack)))
        else:
            stack.append((name, lo, len(stack)))
    unmatched.extend((lo, name) for name, lo, _ in stack)
    return sorted(result), unmatched


def one_line(text):
    return " ".join(text.split())


def labels(raw):
    found = re.findall(r"<(?:text|caption|label|title)\b[^>]*>(.*?)</(?:text|caption|label|title)>", raw, re.S)
    return list(dict.fromkeys(one_line(item) for item in found if one_line(item)))


def state_data(raw):
    declarations = [line.strip() for line in BODY.findall(raw)]
    controls = [m.group(0) for m in re.finditer(
        r"<(?:slider|checkbox|radio-group|segmented-control|button|input)\b[^>\n]*(?:>|$)", raw
    )]
    return declarations, controls


def component_plan(kind, raw, interaction):
    if kind == "AsyncImage":
        return "Missing original asset", "Keep the query and seek the original rendered image or response payload"
    if kind == "svg":
        if interaction == "parameterized":
            return "Source-backed vector states", "Evaluate source geometry and render default plus representative states"
        if re.search(r"\{[#/]|=[{]", raw):
            return "Source-backed vector", "Resolve deterministic template expressions and export SVG to PDF"
        return "Direct vector", "Validate and reuse native SVG geometry"
    if kind == "Chart":
        return "Source-backed vector", "Replot archived values, axes and series labels as native PDF vectors"
    if kind == "mermaid":
        return "Source-backed vector", "Render the archived diagram specification"
    if kind == "fenced-diagram":
        return "Source-backed text diagram", "Preserve text geometry and monospace alignment"
    if kind == "plot-code":
        return "Original plot output unverified", "Archive code and list data or runtime dependencies before reproducing output"
    if interaction == "parameterized":
        return "Source-backed print representation", "Select default and meaningful parameter states from archived declarations"
    if re.search(r'width="[\d.]+%"|width=\{[^}]*%|<box[^>\n]*(?:background=.*height=|height=.*background=)|<table\b', raw):
        return "Source-backed print representation", "Reproduce comparisons as vector geometry or typeset tables"
    return "Source-backed structured layout", "Typeset original wording, labels, hierarchy and meaningful relationships"


def main():
    source_bytes = SOURCE.read_bytes()
    doc = json.loads(source_bytes)
    conv = doc["conversation"]
    messages = conv["messages"]
    by_id = {m["id"]: m for m in messages}
    assert len(messages) == len(by_id)
    numbers = {m["id"]: n for n, m in enumerate(messages, 1)}
    children = defaultdict(list)
    for message in messages:
        parent = message["parent_id"]
        assert parent is None or parent in by_id
        children[parent].append(message["id"])
    visible_leaves = [
        m for m in messages
        if m["role"] == "assistant"
        and any(c["type"] == "markdown" for c in m["content"])
        and not any(not by_id[i]["metadata"].get("is_visually_hidden_from_conversation")
                    for i in children[m["id"]])
    ]
    tip = max(visible_leaves, key=lambda m: m["created_at"])
    path = []
    while tip:
        assert tip["id"] not in path
        path.append(tip["id"])
        tip = by_id.get(tip["parent_id"])
    path.reverse()
    path_set = set(path)
    ordered = {identifier: i for i, identifier in enumerate(path, 1)}
    assert [numbers[i] for i in path][-8:] == [69, 70, 72, 73, 71, 75, 76, 77]
    SOURCE_FILES.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, ARCHIVE / SOURCE.name)
    digest = hashlib.sha256(source_bytes).hexdigest()
    write(ARCHIVE / "SHA256.txt", f"{digest}  {SOURCE.name}\n")
    rows, content_rows, sources, figures, headings, table_rows, parse_notes = [], [], [], [], [], [], []
    transcript = []
    for n, m in enumerate(messages, 1):
        identifier = m["id"]
        metadata = m["metadata"]
        branch = ("hidden" if metadata.get("is_visually_hidden_from_conversation")
                  else "active" if identifier in path_set else "alternate")
        if identifier in path_set:
            kind = ("supporting tool trace" if m["role"] == "tool"
                    or m["content"][0]["type"] == "tool_call"
                    else "assistant preamble" if metadata.get("is_thinking_preamble_message")
                    else "reading path")
        else:
            kind = ""
        filename = f"{n:02d}-{identifier}"
        rows.append(dict(
            stored_ordinal=n, ancestry_ordinal=ordered.get(identifier, ""),
            message_id=identifier, parent_id=m["parent_id"] or "",
            children=" ".join(children[identifier]), role=m["role"], disposition=branch,
            reading_role=kind, created_at=m["created_at"],
            content_types=" ".join(c["type"] for c in m["content"]),
            complete=metadata.get("is_complete", ""),
            finish_type=(metadata.get("finish_details") or {}).get("type", ""),
        ))
        transcript.append({
            "stored_ordinal": n, "ancestry_ordinal": ordered.get(identifier),
            "disposition": branch, "reading_role": kind, **m,
        })
        for part, block in enumerate(m["content"], 1):
            original = block["text"]
            name = filename + ("" if part == 1 else f"-block{part}") + ".md"
            write(SOURCE_FILES / name, original)
            locator = {"stored_ordinal": n, "message_id": identifier, "branch": branch,
                       "reading_role": kind, "block": part, "message_file": name}

            newlines = [i for i, char in enumerate(original) if char == "\n"]
            line = lambda pos: bisect.bisect_left(newlines, pos) + 1
            fences = list(FENCE.finditer(original))
            prose = mask_spans(original, fences)
            parsed, unmatched = tags(prose)
            if unmatched:
                parse_notes.append({**locator, "unmatched": [(line(i), tag) for i, tag in unmatched]})
            found_headings = list(HEAD.finditer(prose))
            heads_at = [h.start() for h in found_headings]
            for match in found_headings:
                headings.append({**locator, "line": line(match.start()), "depth": len(match[1]), "heading": match[2]})
            components = [(lo, hi) for lo, hi, tag, level in parsed
                          if level == 0 and tag in {"box", "row", "grid", "card"}]
            declaration_spans = [(i.start(), i.end()) for i in BODY.finditer(prose)]
            contexts = {}
            for lo, hi in components:
                start = lo
                for a, b in reversed(declaration_spans):
                    if b <= start and not prose[b:start].strip():
                        start = a
                    elif b < start:
                        break
                contexts[lo] = (start, hi)

            def context(lo, hi):
                return next(((a, b, start) for a, (start, b) in contexts.items() if a <= lo and hi <= b),
                            (lo, hi, lo))

            def add(lo, hi, tag, component_level=0):
                a, b, start = context(lo, hi)
                raw, surrounding = original[lo:hi], original[start:b]
                control_start = re.search(r"<(?:input|slider|checkbox|radio-group|segmented-control|button)\b", surrounding)
                if tag in {"svg", "Chart", "AsyncImage"} and control_start:
                    default_state = "parameterized"
                elif tag == "Chart":
                    default_state = "static data / client tooltips"
                elif tag in {"box", "row", "grid", "card"} and CONTROLS.search(raw):
                    default_state = "parameterized"
                else:
                    default_state = "static"
                declarations, controls = state_data(surrounding)
                head_index = bisect.bisect_right(heads_at, lo) - 1
                nearest = found_headings[head_index][2] if head_index >= 0 else "(opening)"
                extracted = labels(surrounding)
                parameters = declarations or []
                if tag == "Chart":
                    chart = re.match(r'<Chart\s+content=\{(.+)\}\s*/>', raw, re.S)
                    if chart:
                        props = json.loads(chart[1])
                        parameters = [f'{props.get("chartType")} · x: {props.get("xKey")} · rows: {len(props.get("data", []))}',
                                      *[f'{key}: {props[key]}' for key in ("yAxisMin", "yAxisMax") if key in props]]
                        extracted = [*extracted, *[s.get("label", s.get("dataKey", "")) for s in props.get("series", [])]]
                elif tag == "svg" and not parameters:
                    parameters = [m.group(0) for m in re.finditer(r'viewBox="[^"]+"', raw)]
                elif tag == "AsyncImage":
                    extracted += re.findall(r'query="([^"]*)"', raw)
                    parameters += re.findall(r'\b(?:aspectRatio|fit)="[^"]+"', raw)
                if controls and default_state == "parameterized":
                    parameters += controls
                if tag in {"box", "row", "grid", "card"}:
                    extracted += re.findall(r"(?m)^\s*\*\*([^*\n]+)\*\*\s*$", raw)
                status, plan = component_plan(tag, raw, default_state)
                if status == "Direct vector":
                    ET.fromstring(raw)
                # The caption or title states the purpose more precisely than a
                # surrounding section heading when both are available.
                primary = re.findall(r"<(?:title|caption)\b[^>]*>([^<{}\n]+)</(?:title|caption)>", surrounding)
                purpose = " · ".join(dict.fromkeys(one_line(v) for v in primary)) or nearest
                key = f"{n:02d}.{part}:{line(lo)}:{lo - (newlines[line(lo)-2] + 1 if line(lo)>1 else 0) + 1}"
                figures.append({
                    **locator, "asset_id": key, "line_start": line(lo), "line_end": line(hi - 1),
                    "context_start": line(start), "context_end": line(b - 1),
                    "kind": tag, "heading": nearest, "label_or_annotation": " · ".join(dict.fromkeys(extracted))[:520],
                    "mathematical_context": purpose[:550],
                    "parameters_or_controls": " · ".join(parameters),
                    "behavior": default_state, "source_status": status, "print_plan": plan,
                })
                sources.append({"asset_id": key, **locator, "source": raw,
                                "source_start_offset": lo, "source_end_offset_exclusive": hi,
                                "containing_component_start_offset": start, "containing_component_end_offset_exclusive": b,
                                "all_labels": list(dict.fromkeys(extracted)), "parameters": parameters,
                                "declarations_and_controls": [declarations, controls]})

            for lo, hi, tag, level in parsed:
                if tag in {"svg", "Chart", "AsyncImage"} or (level == 0 and tag in {"box", "row", "grid", "card"}):
                    add(lo, hi, tag, level)
            for fence in fences:
                language, code = fence[1].strip().lower(), fence[2]
                if language == "mermaid":
                    add(fence.start(), fence.end(), "mermaid")
                elif language == "text" and re.search(r"[─│┌└┬┐┼↓→←↑]|-->|\\--|└─", code):
                    add(fence.start(), fence.end(), "fenced-diagram")
                elif re.search(r"\b(?:plt\.|plot_acf\(|plotly|sns\.)", code):
                    add(fence.start(), fence.end(), "plot-code")
            displays = list(DISPLAY.finditer(prose))
            tables = list(TABLE.finditer(prose))
            for kind_name, items in (("display equation", displays), ("Markdown table", tables), ("fenced block", fences)):
                for match in items:
                    h = bisect.bisect_right(heads_at, match.start()) - 1
                    table_rows.append({**locator, "kind": kind_name, "line_start": line(match.start()),
                                       "line_end": line(match.end()-1),
                                       "heading": found_headings[h][2] if h >= 0 else "(opening)",
                                       "locator_excerpt": one_line(match[0])[:180]})
            refs = metadata.get("content_references") or []
            content_rows.append({
                **locator, "role": m["role"], "content_type": block["type"], "characters": len(original),
                "line_count": 1 + original.count("\n"), "heading_count": len(found_headings),
                "display_math": len(displays), "aligned_math": len(re.findall(r"\\begin\{(?:align(?:ed|at)?|split|gather(?:ed)?)\*?\}", prose)),
                "inline_parenthetical_math": len(INLINE.findall(prose)),
                "tables": len(tables), "fences": len(fences),
                "fence_languages": " ".join(f[1].strip() or "(plain)" for f in fences),
                "widget_reference_categories": json.dumps(Counter(
                    r.get("category", r["type"]) for r in refs), ensure_ascii=False),
                "structural_anchor": found_headings[0][2] if found_headings else one_line(original)[:145],
            })

    by_num = {r["stored_ordinal"]: r for r in rows}
    csv_file(REPORTS / "message-tree.csv", rows)
    csv_file(REPORTS / "content-inventory.csv", content_rows)
    csv_file(REPORTS / "source-headings.csv", headings)
    csv_file(REPORTS / "math-tables-code-index.csv", table_rows)
    figures.sort(key=lambda r: (r["stored_ordinal"], r["block"], r["line_start"], r["asset_id"]))
    csv_file(REPORTS / "figure-manifest.csv", figures)
    jsonl(ARCHIVE / "visualization-sources.jsonl", sources)
    jsonl(ARCHIVE / "normalized-all.jsonl", transcript)
    jsonl(ARCHIVE / "normalized-path.jsonl",
          sorted((r for r in transcript if r["ancestry_ordinal"]), key=lambda r: r["ancestry_ordinal"]))
    by_heading = defaultdict(list)
    for h in headings:
        by_heading[h["stored_ordinal"]].append(h)

    # Message groups are the source's own Parts and ordered passes. All heading
    # depths and line positions survive in the CSV if typesetting needs adjustment.
    groups = [
        ("Part 0 / I — Initial and revised passes", [1, 3, 5, 7, 9, 10]),
        ("Part II — Statistical Learning Theory", [12, 14, 16, 20, 23, 27]),
        ("Part III — Agentic AI and Recursive Self-Improvement", [31, 34, 37, 40, 44, 48]),
        ("Part IV — Financial AI & Quantitative Research", [52, 57, 58, 60, 63, 67, 71, 77]),
    ]
    structure = [
        "# Proposed table of contents",
        "",
        "Proposed front matter comprises a title page, editorial note and navigable contents. "
        "The body follows the active ancestry. The groups below retain both opening passes and the "
        "IV-A continuation. Stage headings and body headings come from the archived Markdown. "
        "The detailed locator below includes source subheadings and previews for manuscript navigation.",
    ]
    for title, members in groups:
        structure += ["", f"## {title}"]
        for n in members:
            row = by_num[n]
            current = by_heading[n]
            is_user = row["role"] == "user"
            descriptor = {
                1: "Original research-preparation brief (reader)",
                3: "First exposition",
                5: "Revised research-preparation brief with project wording (reader)",
                7: "Revised exposition",
                9: "Request for a conclusions and proof index (reader)",
                52: "IV-A initial exposition",
                57: "Request to resume at §6.2 (reader)",
                58: "IV-A continuation",
            }.get(n, current[0]["heading"] if current else "Reader exchange")
            filename = f'{n:02d}-{row["message_id"]}.md'
            structure += ["", f'### {descriptor}', "",
                          f'Source message {n:02d} · [{row["message_id"]}](../archive/messages/{filename})']
            if current:
                for h in current:
                    level = max(0, h["depth"] - 1)
                    title_safe = h["heading"].replace("<", "&lt;").replace(">", "&gt;")
                    structure.append(f'{"  " * level}- {title_safe} (line {h["line"]})')
            elif is_user:
                structure.append("")
                structure.append("Question or request retained at this position.")
    structure += ["", "## Material mentioned in the roadmap",
                  "", "Part V and Part VI are proposed in the source. The archive ends at the transition from IV-F to Part V. "
                  "Their roadmap entries and previews stay where they occur. No delivered chapters for those parts were found.", ""]
    write(REPORTS / "proposed-contents.md", "\n".join(structure))
    stats = {
        "sha256": digest, "file_bytes": len(source_bytes), "schema": doc["schema_version"],
        "provider": doc["source"], "conversation": {k: v for k, v in conv.items() if k != "messages"},
        "ancestry": [numbers[i] for i in path],
        "roots": [numbers[i] for i in children[None]],
        "visible_leaves": [numbers[m["id"]] for m in visible_leaves],
        "forks": {str(numbers[k]): [numbers[i] for i in v] for k, v in children.items() if k and len(v)>1},
        "dispositions": Counter(r["disposition"] for r in rows),
        "reading_roles": Counter(r["reading_role"] for r in rows if r["disposition"] == "active"),
        "roles": Counter(r["role"] for r in rows),
        "content_types": Counter(r["content_type"] for r in content_rows),
        "on_ancestry_roles": Counter(r["role"] for r in rows if r["disposition"] == "active"),
        "content_counts": {branch: {key: sum(r[key] for r in content_rows if r["branch"] == branch)
                            for key in ("characters", "heading_count", "display_math", "aligned_math",
                                        "inline_parenthetical_math", "tables", "fences")}
                           for branch in ("active", "alternate", "hidden")},
        "figures": {branch: Counter(r["kind"] for r in figures if r["branch"] == branch)
                    for branch in ("active", "alternate", "hidden")},
        "svg_by_status": Counter(r["source_status"] for r in figures if r["branch"] == "active" and r["kind"] == "svg"),
        "active_parameterized_containers": sum(r["behavior"] == "parameterized"
                                        and r["kind"] in {"box", "row", "grid", "card"}
                                        and r["branch"] == "active" for r in figures),
        "reference_types": Counter(r.get("category", r["type"]) for m in messages for r in m["metadata"].get("content_references", []) or []),
        "malformed_component_candidates": parse_notes,
    }
    write(REPORTS / "extraction-statistics.json", json.dumps(stats, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(messages)} stored messages, {len(path)} on latest visible ancestry, {len(figures)} asset/container rows.")
    print(f"{len(parse_notes)} messages with component scanner notices.")
    assert hashlib.sha256((ARCHIVE / SOURCE.name).read_bytes()).hexdigest() == digest


if __name__ == "__main__":
    main()
