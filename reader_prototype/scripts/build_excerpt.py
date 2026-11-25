"""Convert the selected source ranges to editable LaTeX and native PDF graphics."""
import ast
import hashlib
import json
import math
import re
import subprocess
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import pymupdf

from inspect_archive import ARCHIVE, FENCE, ROOT, write

LATEX = ROOT / "latex"
FIGURES = LATEX / "figures"
PREVIEW = [
    (11, 25, "volatility", .87, ""),
    (49, 66, "acf", .87, ""),
    (257, 269, "garch-mechanism", .53, "GARCH(1,1) 条件方差的组成"),
    (342, 376, "garch-persistence", .72, ""),
    (410, 426, "densities", .46, ""),
    (437, 459, "tail-probability", .72, ""),
]
PERSISTENCE = (0.50, 0.90, 0.99)
PALETTE = dict(re.findall(r"\\definecolor\{(\w+)\}\{HTML\}\{([0-9A-Fa-f]{6})\}",
                          (ROOT.parent / "palette.tex").read_text(encoding="utf-8-sig")))
SOURCE_COLORS = {
    "#2563eb": "ResearchBlue", "#64748b": "ResearchSlate",
    "#94a3b8": "ResearchSlate", "#d97706": "ResearchPeach", "#0d9488": "ResearchSage",
    "currentColor": "ResearchSlate",
}
MATH_RE = re.compile(r"\\([\[(])(.*?)\\([\])])", re.S)
ATTRIBUTES = {
    "fillOpacity": "fill-opacity", "strokeOpacity": "stroke-opacity",
    "strokeWidth": "stroke-width", "strokeDasharray": "stroke-dasharray",
    "fontSize": "font-size", "fontWeight": "font-weight", "textAnchor": "text-anchor",
}
BACKTICK = chr(96)
SUB = "$" + "{"


def load(number):
    return next((ARCHIVE / "messages").glob(f"{number:02d}-*.md")).read_text(encoding="utf-8")


def run_pandoc(arguments, value):
    result = subprocess.run(["pandoc", *arguments], input=value.encode("utf-8"),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout.decode("utf-8").replace("\r", "")


def pandoc_math(markdown):
    """Map delimiters to Pandoc syntax while retaining each TeX math payload."""
    def convert(segment):
        def delimit(match):
            token = "$$" if match[1] == "[" else "$"
            return token + match[2].strip() + token
        return MATH_RE.sub(delimit, segment)
    parts, offset = [], 0
    for fence in FENCE.finditer(markdown):
        parts.extend([convert(markdown[offset:fence.start()]), fence[0]])
        offset = fence.end()
    return "".join(parts + [convert(markdown[offset:])])


def path_data(points):
    return " ".join(f"{'L' if i else 'M'}{x:.8f} {y:.8f}" for i, (x, y) in enumerate(points))


def styled_path(points, dash=None):
    """Encode dash geometry explicitly for SVG-to-PDF engines that drop dash attributes."""
    if dash is None:
        return path_data(points)
    result = []
    drawn, remaining = True, dash[0]
    iterator = iter(points)
    start = next(iterator)
    for finish in iterator:
        length = math.dist(start, finish)
        offset = 0.0
        while offset < length:
            advance = min(remaining, length-offset)
            if drawn:
                result.append(path_data([
                    tuple(a+(b-a)*position/length for a, b in zip(start, finish))
                    for position in (offset, offset+advance)
                ]))
            offset += advance
            remaining -= advance
            if remaining < 1e-8:
                drawn = not drawn
                remaining = dash[0 if drawn else 1]
        start = finish
    return " ".join(result)


def volatility(panel):
    for i in range(180):
        u = i / 179
        wave = math.sin(i*7.91) + .7*math.cos(i*3.19) + .35*math.sin(i*.83)
        scale = (15 if panel == 0 else 5 + 24*math.exp(-((u-.32)/.1)**2)
                 + 22*math.exp(-((u-.78)/.11)**2))
        yield 10+330*u, panel*122+67-scale*wave*.8


def densities(kind):
    for i in range(241):
        x = -6 + i*.05
        y = (math.exp(-x*x/2)/math.sqrt(2*math.pi) if kind == 0
             else 2/(math.pi*(1+x*x)**2))
        yield 20+(x+6)*310/12, 194-y*260


def value(expression, env):
    """Resolve only the expressions present in the reviewed five SVG templates."""
    panel, p, h, x, y = (env.get(name, 0) for name in ("panel", "p", "h", "x", "y"))
    mapping = {
        'panel===0?"Returns with constant volatility":"Returns with volatility clustering"':
            lambda: "Returns with constant volatility" if panel == 0 else "Returns with volatility clustering",
        "panel*122+13": lambda: panel*122+13,
        "panel===1": lambda: panel == 1,
        "panel*122+67": lambda: panel*122+67,
        'panel===0?"#64748b":"#2563eb"': lambda: "#64748b" if panel == 0 else "#2563eb",
        "p*118+12": lambda: p*118+12,
        'p===0?"ACF of returns":"ACF of squared returns"':
            lambda: "ACF of returns" if p == 0 else "ACF of squared returns",
        BACKTICK+"M30 "+SUB+"p*118+23} V"+SUB+"p*118+104} H330"+BACKTICK:
            lambda: f"M30 {p*118+23} V{p*118+104} H330",
        "p*118+86": lambda: p*118+86,
        "p*118+80": lambda: p*118+80,
        "30+h*14.5": lambda: 30+h*14.5,
        "p*118+86-65*(p===0?.065*Math.sin(h*2.3):.78*Math.exp(-h*.09)+.035*Math.sin(h*3))":
            lambda: p*118+86-65*(.065*math.sin(h*2.3) if p == 0 else .78*math.exp(-h*.09)+.035*math.sin(h*3)),
        'p===0?"#64748b":"#2563eb"': lambda: "#64748b" if p == 0 else "#2563eb",
        "p*118+115": lambda: p*118+115,
        "p.x": lambda: p["x"],
        "p.x+51": lambda: p["x"]+51,
        "p.a": lambda: p["a"],
        "p.b": lambda: p["b"],
        BACKTICK+"M"+SUB+"p.x+51} 62 V87 H170 V103"+BACKTICK: lambda: f'M{p["x"]+51} 62 V87 H170 V103',
        "170-(y-1)*45": lambda: 170-(y-1)*45,
        "174-(y-1)*45": lambda: 174-(y-1)*45,
        "32+h*7.45": lambda: 32+h*7.45,
        "p.c": lambda: p["c"],
        "20+(x+6)*310/12": lambda: 20+(x+6)*310/12,
        'Array.from({length:180},(_,i)=>{const u=i/179;const wave=Math.sin(i*7.91)+.7*Math.cos(i*3.19)+.35*Math.sin(i*.83);const scale=panel===0?15:5+24*Math.exp(-Math.pow((u-.32)/.1,2))+22*Math.exp(-Math.pow((u-.78)/.11,2));return(i===0?"M":"L")+(10+330*u)+" "+(panel*122+67-scale*wave*.8)}).join(" ")':
            lambda: path_data(volatility(panel)),
        'Array.from({length:41},(_,h)=>(h===0?"M":"L")+(32+h*7.45)+" "+(170-135*p**h)).join(" ")':
            lambda: path_data((32+lag*7.45, 170-135*p**lag) for lag in range(41)),
        'Array.from({length:241},(_,i)=>{const x=-6+i*.05;const y=p.kind===0?Math.exp(-x*x/2)/Math.sqrt(2*Math.PI):2/(Math.PI*(1+x*x)**2);return (i===0?"M":"L")+(20+(x+6)*310/12)+" "+(194-y*260)}).join(" ")':
            lambda: styled_path(densities(p["kind"]), (6, 4) if p["kind"] else None),
    }
    return env[expression] if expression in env else mapping[expression]()


def loop_values(expression):
    if expression == "Array.from({length:20},(_,i)=>i+1)":
        return range(1, 21)
    # Parse only literals after quoting object keys. No archived JS is executed.
    return ast.literal_eval(re.sub(r'([{,])([a-z]+):', r"\1'\2':", expression))


def substitute(line, env):
    result, cursor = [], 0
    while (start := line.find("{", cursor)) != -1:
        result.append(line[cursor:start])
        depth, quote = 1, ""
        for i in range(start+1, len(line)):
            char = line[i]
            if quote:
                if char == quote and line[i-1] != "\\":
                    quote = ""
            elif char in "\"'" + BACKTICK:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    break
        else:
            raise ValueError(f"Unclosed template expression: {line}")
        evaluated = escape(str(value(line[start+1:i], env)), {'"': "&quot;"})
        result.append(f'"{evaluated}"' if start and line[start-1] == "=" else evaluated)
        cursor = i+1
    result.append(line[cursor:])
    return "".join(result)


def expand(lines, env):
    output = []
    next_line = 0
    while next_line < len(lines):
        line = lines[next_line]
        control = re.match(r"\s*\{#(each|if) (.+)\}\s*$", line)
        if not control:
            output.append(substitute(line, env))
            next_line += 1
            continue
        depth, end = 1, next_line+1
        while end < len(lines):
            marker = lines[end].strip()
            depth += marker.startswith("{#")
            depth -= marker.startswith("{/")
            if depth == 0:
                break
            end += 1
        assert end < len(lines) and lines[end].strip() == "{/" + control[1] + "}"
        sublines = lines[next_line+1:end]
        if control[1] == "each":
            expression, name = control[2].rsplit(" as ", 1)
            for item in loop_values(expression):
                output.extend(expand(sublines, {**env, name: item}))
        elif value(control[2], env):
            output.extend(expand(sublines, env))
        next_line = end+1
    return output


def svg_document(fragment):
    viewbox = re.search(r'viewBox="([\d. ]+)"', fragment)
    _, _, width, height = viewbox[1].split()
    text = fragment.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    text = text.replace('width="100%"', f'width="{width}" height="{height}"', 1)
    for source_color, name in SOURCE_COLORS.items():
        text = text.replace('="' + source_color + '"', '="palette:' + name + '"')
    text = re.sub(r'palette:(\w+)', lambda m: "#" + PALETTE[m[1]], text)
    for component, standard in ATTRIBUTES.items():
        text = re.sub(r"\b"+component+r"=", standard+"=", text)
    # The web component inherits its font from the client. Use a selectable
    # serif for figure text while preserving positions, weights and labels.
    text = text.replace("<text ", '<text font-family="serif" ')
    return text + "\n"


def tail_plot(raw):
    values = re.findall(r"<text tabularNums=\{true\}>([^<]+)</text>", raw)
    names = re.findall(r"(?m)^\s*\*\*(.*?)\*\*\s*$", raw)
    assert values == ["0.0000573%", "0.324%"]
    x_at = lambda percent: 104 + 63*(math.log10(percent)+5)
    result = ['<svg viewBox="0 0 440 100" width="100%">']
    for power in range(-5, 1):
        x = x_at(10**power)
        result += [
            f'<line x1="{x}" y1="8" x2="{x}" y2="65" stroke="currentColor" opacity=".31"/>',
            f'<text x="{x}" y="79" textAnchor="middle" fontSize="12">{10**power:g}</text>',
        ]
    for y, label, number, color in zip((18, 43), names, values, ("ResearchSlate", "ResearchBlue"), strict=True):
        x = x_at(float(number[:-1]))
        result += [
            f'<text x="2" y="{y+4}" fontSize="13">{escape(label)}</text>',
            f'<circle cx="{x}" cy="{y}" r="3.5" fill="palette:{color}"/>',
            f'<text x="{x+9 if y == 18 else x-9}" y="{y+4}" textAnchor="{"start" if y == 18 else "end"}" fontSize="12">{number}</text>',
        ]
    result += ['<path d="M104 65H419" stroke="currentColor"/>',
               '<text x="262" y="96" textAnchor="middle" fontSize="12">Tail probability (%) · log scale</text>']
    return "\n".join(result + ["</svg>"])


def persistence_plot(raw):
    assert "170-135*p**h" in raw and "DIL.useState(0.9)" in raw
    result = ['<svg viewBox="0 0 430 134" width="100%">']
    for tick in (1, 2, 3, 4):
        y = 99 - (tick-1)*24
        result += [
            f'<path d="M28 {y}H405" stroke="currentColor" opacity=".28"/>',
            f'<text x="19" y="{y+4}" textAnchor="end" fontSize="12">{tick}</text>',
        ]
    result += ['<path d="M28 21V99H405" stroke="currentColor" fill="none"/>']
    for tick in (0, 10, 20, 30, 40):
        result.append(f'<text x="{28+tick*9.425}" y="113" fontSize="12" textAnchor="middle">{tick}</text>')
    result += ['<text x="218" y="129" fontSize="12" textAnchor="middle">Periods after shock</text>']
    for p, color, dash, x in zip(
        PERSISTENCE, ("ResearchSlate", "ResearchBlue", "ResearchSage"), ("2 4", "", "8 4"),
        (32, 150, 298), strict=True
    ):
        pattern = tuple(map(int, dash.split())) if dash else None
        points = styled_path(((28+h*9.425, 99-72*p**h) for h in range(41)), pattern)
        lead = styled_path(((x, 10), (x+21, 10)), pattern)
        style = f'stroke="palette:{color}" strokeWidth="2.3"'
        result += [
            f'<path d="{points}" {style} fill="none"/>',
            f'<path d="{lead}" {style}/>',
            f'<text x="{x+27}" y="14" fontSize="12">a+b = {p:.2f}{" (default)" if p == .90 else ""}</text>',
        ]
    return "\n".join(result + ["</svg>"])


def spread_panels(stem, source_svg):
    # Reuse each panel's marks at their original scale and move the second
    # panel next to the first. Keep the source's shared time label.
    lines = source_svg.splitlines()
    inner = lines[2:-3] if stem == "volatility" else lines[2:-2]
    offset = 122 if stem == "volatility" else 118
    variable = "panel" if stem == "volatility" else "p"
    width = 710 if stem == "volatility" else 690
    height = 142 if stem == "volatility" else 124
    content = [f'<svg viewBox="0 0 {width} {height}" width="100%">']
    for panel in (0, 1):
        content += [f'<g transform="translate({panel*(width//2)} {-panel*offset})">']
        content += expand(inner, {variable: panel})
        content += ["</g>"]
    if stem == "volatility":
        content += ['<text x="355" y="135" fontSize="13" textAnchor="middle" fill="currentColor">Time</text>']
    return "\n".join(content + ["</svg>"])


def save_vector(stem, svg):
    tree = ET.fromstring(svg)
    allowed = {"svg", "line", "path", "rect", "text", "g", "circle"}
    for node in tree.iter():
        assert node.tag.split("}")[-1] in allowed
        assert not any(key.startswith("on") or "href" in key for key in node.attrib)
    write(FIGURES / f"{stem}.svg", svg)
    with pymupdf.open("svg", svg.encode("utf-8")) as document:
        result = document.convert_to_pdf()
    with pymupdf.open("pdf", result) as document:
        page = document[0]
        assert page.get_drawings() and page.get_text().strip() and not page.get_images(), stem
    (FIGURES / f"{stem}.pdf").write_bytes(result)


def tex_inline(markdown):
    return run_pandoc(["-f", "markdown-smart+tex_math_single_backslash", "-t", "latex", "--wrap=none"],
                      markdown).strip()


def graphic_code(stem, raw, width, fallback_title):
    captions = re.findall(r"<caption>([^<{}]+)</caption>", raw)
    headings = re.findall(r"<title(?: [^>]*)?>([^<{}]+)</title>", raw)
    title = headings[0] if headings else ""
    footer = ""
    if stem == "garch-persistence":
        fragment = persistence_plot(raw)
        footer = r"""
\smallskip
\begin{tabular}{@{}lrrr@{}}
\toprule
\(a+b\) & 0.50 & 0.90 & 0.99 \\
\midrule
""" + tex_inline(captions[0]) + " & " + " & ".join(f"{math.log(.5)/math.log(p):.2f}" for p in PERSISTENCE) + r" \\" + "\n" + tex_inline(captions[2]) + " & " + " & ".join(f"{100*p**20:.1f}\\%" for p in PERSISTENCE) + r" \\" + "\n" + r"\bottomrule\end{tabular}" + "\n"
        footer = footer.replace("Shock half-life（连续插值）", "Shock half-life（连续插值，Periods）")
    else:
        if stem == "tail-probability":
            fragment = tail_plot(raw)
            footer = r"\par\textbf{" + tex_inline(headings[1]) + "}\n"
        else:
            source_svg = re.search(r"<svg\b[\s\S]+?</svg>", raw)[0]
            if stem in {"volatility", "acf"}:
                fragment = spread_panels(stem, source_svg)
                for size in ('9', '11'):
                    fragment = fragment.replace(f'fontSize="{size}"', 'fontSize="14"')
                if stem == "volatility":
                    fragment = fragment.replace('opacity=".09"', 'opacity=".24"')
            else:
                fragment = "\n".join(expand(source_svg.splitlines(), {}))
            if stem == "garch-mechanism":
                fragment = fragment.replace('340 176', '340 162')
            if stem == "densities":
                fragment = fragment.replace('stroke="#d97706"', 'stroke="palette:ResearchSlate"')
                fragment = fragment.replace('fontSize="10"', 'fontSize="13"').replace('fontSize="11"', 'fontSize="14"')
    save_vector(stem, svg_document(fragment))
    graphic = rf"\includegraphics[width=\linewidth]{{figures/{stem}.pdf}}"
    if stem == "densities":
        footer = (r"\par \legendmark{ResearchBlue}\," + tex_inline(captions[0])
                  + r"\enspace \legenddash{ResearchSlate}\," + tex_inline(captions[1]) + "\n")
    caption = tex_inline(captions[-1] if captions else fallback_title)
    return (rf"\begin{{readerfigure}}{{{width}}}" + "\n"
            + (r"\figuretitle{" + tex_inline(title) + "}\n" if title else "")
            + graphic + "\n" + footer
            + r"\captionof{figure}{" + caption + "}\n"
            + r"\end{readerfigure}" + "\n")


def captions_in_table(ast_document):
    column_widths = [(.12, .48, .12), (.15, .40), (.25, .19, .25),
                     (.24, .14, .15, .19), (.25, .26, .34)]
    names = ["ARCH 与 GARCH", "GARCH 模型的参数", "双侧理论尾部概率",
             "Student’s t Distribution 的矩", "厚尾对统计工具的影响"]
    tables = [block for block in ast_document["blocks"] if block["t"] == "Table"]
    assert len(tables) == len(names)
    for table, widths, name in zip(tables, column_widths, names):
        c = table["c"]
        assert len(c[2]) == len(widths)
        for column, width in zip(c[2], widths):
            column[1] = {"t": "ColWidth", "c": width}
        c[1] = [None, [{"t": "Plain", "c": [{"t": "Str", "c": name}]}]]


def compact_prose(tex):
    # These are ordinal positions within the frozen 39 displays in #58:7–587.
    # The converter rejects any changed formula payload before this runs.
    inline_positions = {0, 1, 2, 3, 4, 5, 8, 9, 10, 16, 17, 19, 20, 28, 30, 32, 34, 36, 37}
    matches = [m for m in MATH_RE.finditer(tex) if m[1] == "["]
    for index, match in reversed(list(enumerate(matches))):
        if index in inline_positions:
            tex = tex[:match.start()] + r"\(" + match[2].strip() + r"\)" + tex[match.end():]
    lead = r"(?:但|或者|这意味着|设|并定义|首先，由独立性|由于|所以|因此|于是|进一步|其中|最终得到|对于|即|由平稳性|我们可能有)"
    tex = re.sub(r"(?m)^(" + lead + r"[^：\n]{0,30}：)\n\n(?!\\hypertarget|\\begin)", r"\1 ", tex)
    tex = re.sub(r"(?m)^([^\\\n].*[：:])\n\n(?=\\[\[(])", r"\1 ", tex)
    tex = re.sub(r"(?m)([。；：]|\u005c\u0029)\n\n(?=" + lead + r"[^：\n]{0,30}：)", r"\1 ", tex)
    return tex, len(inline_positions)


def main():
    lines = load(58).splitlines()
    selection = lines[6:587]
    fence = BACKTICK * 3
    for lo, hi, stem, width, fallback in reversed(PREVIEW):
        raw = "\n".join(lines[lo-1:hi])
        insert = graphic_code(stem, raw, width, fallback)
        write(FIGURES / f"{stem}.source.txt", raw + "\n")
        selection[lo-7:hi-6] = ["", fence+"{=latex}", insert.strip(), fence, ""]
    part_six = load(52).splitlines()[643]
    assert part_six == "# 6. Stylized Facts of Financial Returns"
    selected_md = part_six + "\n\n" + "\n".join(line for line in selection if line != "---") + "\n"
    assert not re.search(r"<(?:svg|box|card|slider)\b|\{@body", selected_md)
    write(LATEX / "excerpt.md", selected_md)
    reader = "markdown-smart+tex_math_single_backslash+raw_attribute"
    ast_doc = json.loads(run_pandoc(["-f", reader, "-t", "json"], pandoc_math(selected_md)))
    original_cells = [block["c"][3:] for block in ast_doc["blocks"] if block["t"] == "Table"]
    captions_in_table(ast_doc)
    assert original_cells == [block["c"][3:] for block in ast_doc["blocks"] if block["t"] == "Table"]
    tex = run_pandoc(["-f", "json", "-t", "latex", "--wrap=none"], json.dumps(ast_doc, ensure_ascii=False))
    equations = [m[2].strip() for m in MATH_RE.finditer("\n".join(lines[6:587]))
                 if m[1] == "["]
    converted_equations = [m[2].strip() for m in MATH_RE.finditer(tex) if m[1] == "["]
    assert equations == converted_equations, "Display math mismatch"
    expected_inline = [m[2].strip() for m in MATH_RE.finditer("\n".join(lines[6:587])) if m[1] == "("]
    original_tex = tex
    tex, promoted = compact_prose(tex)
    canonical = lambda value: re.sub(r"\s+", "", MATH_RE.sub(lambda m: r"\(" + m[2] + r"\)", value))
    assert canonical(original_tex) == canonical(tex), "Prose, equation or table content changed"
    actual_inline = [m[2].strip() for m in MATH_RE.finditer(tex) if m[1] == "("]
    for expr in set(expected_inline):
        assert actual_inline.count(expr) >= expected_inline.count(expr), expr
    tex = tex.replace(r"\begin{longtable}", "\\begin{readertable}\n\\begin{longtable}")
    tex = tex.replace(r"\end{longtable}", "\\end{longtable}\n\\end{readertable}")
    # This short argument occupies less than a quarter page and concludes in
    # a boxed criterion. Keep the heading, calculation and criterion together.
    tex = re.sub(r"(\\hypertarget\{proof-sketch\}.*?)(?=\\hypertarget\{)",
                 r"\\begin{samepage}\n\1\\end{samepage}\n\n", tex, count=1, flags=re.S)
    write(LATEX / "excerpt.tex", "% Generated by scripts/build_excerpt.py\n" + tex)
    evidence = {
        "display_equations_compared": len(equations), "equation_payloads_equal_after_boundary_trim": True,
        "moved_inline": promoted, "remaining_displays": len(equations) - promoted,
        "prose_and_math_tokens_equal_after_whitespace_and_delimiter_normalization": True,
        "table_cell_ast_unchanged": True,
        "inline_expressions_meeting_source_multiplicity": len(expected_inline),
        "table_count": 5, "graphics_count": 6, "svg_and_pdf_files_each": 6,
        "prose_source_lines": "58:7–587",
        "source_prose_sha256": hashlib.sha256("\n".join(lines[6:587]).encode("utf-8")).hexdigest(),
    }
    write(ROOT / "reports" / "prototype-conversion.json", json.dumps(evidence, ensure_ascii=False, indent=2)+"\n")
    print(f"{len(equations)} original displays verified, {promoted} set inline. Five source tables and six graphics placed.")


if __name__ == "__main__":
    main()
