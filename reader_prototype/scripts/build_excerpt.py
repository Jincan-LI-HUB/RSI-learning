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
    (11, 25, "volatility", 0.72, ""),
    (49, 66, "acf", 0.72, ""),
    (257, 269, "garch-mechanism", 0.80, "GARCH(1,1) 条件方差的组成"),
    (342, 376, "garch-persistence", 0.77, ""),
    (410, 426, "densities", 0.70, ""),
    (437, 459, "tail-probability", 0.73, ""),
]
PERSISTENCE = (0.50, 0.90, 0.99)
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
            lambda: path_data(densities(p["kind"])),
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
    text = text.replace("currentColor", "#253037")
    for component, standard in ATTRIBUTES.items():
        text = re.sub(r"\b"+component+r"=", standard+"=", text)
    # The web component inherits its font from the client. Use a selectable
    # serif for figure text while preserving positions, weights and labels.
    text = text.replace("<text ", '<text font-family="serif" ')
    return text + "\n"


def tail_bars(raw):
    values = re.findall(r"<text tabularNums=\{true\}>([^<]+)</text>", raw)
    names = re.findall(r"(?m)^\s*\*\*(.*?)\*\*\s*$", raw)
    width_percent, first = re.search(r'width="([0-9.]+)%" background="(#[0-9a-f]+)"', raw).groups()
    second = re.search(r'<box height="14px" background="(#[0-9a-f]+)" radius="sm"/>', raw)[1]
    result = ['<svg viewBox="0 0 340 95" width="100%">']
    for y, label, number, width, color in zip(
        (19, 61), names, values, (320*float(width_percent)/100, 320), (first, second), strict=True
    ):
        result.extend([
            f'<text x="10" y="{y}" fontSize="13">{escape(label)}</text>',
            f'<text x="330" y="{y}" fontSize="12" textAnchor="end">{number}</text>',
            f'<rect x="10" y="{y+7}" width="320" height="14" rx="2" fill="#e6ebee"/>',
            f'<rect x="10" y="{y+7}" width="{width:.4f}" height="14" rx="2" fill="{color}"/>',
        ])
    return "\n".join(result + ["</svg>"])


def save_vector(stem, svg):
    tree = ET.fromstring(svg)
    allowed = {"svg", "line", "path", "rect", "text"}
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
        source_svg = re.search(r"<svg\b[\s\S]+?</svg>", raw)[0]
        for p in PERSISTENCE:
            svg = svg_document("\n".join(expand(source_svg.splitlines(), {"p": p})))
            svg = svg.replace('font-size="10"', 'font-size="18"').replace('font-size="11"', 'font-size="19.5"')
            save_vector(f"{stem}-{p:.2f}", svg)
        panels = [
            rf"\begin{{minipage}}[t]{{.318\linewidth}}\centering "
            rf"\textbf{{\(a+b={p:.2f}\)}}{'（默认）' if p == .9 else ''}\par\smallskip"
            rf"\includegraphics[width=\linewidth]{{figures/{stem}-{p:.2f}.pdf}}\end{{minipage}}"
            for p in PERSISTENCE
        ]
        graphic = r"\hfill".join(panels)
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
            fragment = tail_bars(raw)
            footer = r"\par\medskip\textcolor{tailgold}{\textbf{" + tex_inline(headings[1]) + "}}\n"
        else:
            source_svg = re.search(r"<svg\b[\s\S]+?</svg>", raw)[0]
            fragment = "\n".join(expand(source_svg.splitlines(), {}))
        save_vector(stem, svg_document(fragment))
        graphic = rf"\includegraphics[width={width}\linewidth]{{figures/{stem}.pdf}}"
    if stem == "densities":
        footer = (r"\par\smallskip \legendmark{figureblue}\enspace " + tex_inline(captions[0])
                  + r"\qquad \legendmark{tailgold}\enspace " + tex_inline(captions[1]) + "\n")
    caption = tex_inline(captions[-1] if captions else fallback_title)
    return (r"\begin{readerfigure}" + "\n"
            + (r"\figuretitle{" + tex_inline(title) + "}\n" if title else "")
            + graphic + "\n" + footer
            + r"\captionof{figure}{" + caption + "}\n"
            + r"\end{readerfigure}" + "\n")


def captions_in_table(ast_document):
    column_widths = [(0.16, .67, .17), (.23, .77), (.43, .25, .32),
                     (.32, .19, .22, .27), (.32, .32, .36)]
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
    captions_in_table(ast_doc)
    tex = run_pandoc(["-f", "json", "-t", "latex", "--wrap=none"], json.dumps(ast_doc, ensure_ascii=False))
    # TeX keeps a display with its lead-in when they form one paragraph. The
    # Markdown blank line is a block boundary and carries no wording.
    tex = re.sub(r"(?m)^([^\\\n].*[：:])\n\n(?=\\\[)", r"\1\n", tex)
    # Keep the short §7.2 setup with its criterion and the §7.3 opening with
    # its comparison table when one of these headings lands near a page foot.
    tex = re.sub(r"(?m)^(\\hypertarget\{[^\n]+\}\{%\n\\subsection\{7\.([23])\b)",
                 lambda m: rf"\Needspace{{{10 if m[2] == '2' else 13}\baselineskip}}" + "\n" + m[1], tex)
    equations = [m[2].strip() for m in MATH_RE.finditer("\n".join(lines[6:587]))
                 if m[1] == "["]
    converted_equations = [m[2].strip() for m in MATH_RE.finditer(tex) if m[1] == "["]
    assert equations == converted_equations, "Display math mismatch"
    expected_inline = [m[2] for m in MATH_RE.finditer("\n".join(lines[6:587]))
                       if m[1] == "("]
    actual_inline = [m[2] for m in MATH_RE.finditer(tex) if m[1] == "("]
    for expr in set(expected_inline):
        assert actual_inline.count(expr) >= expected_inline.count(expr), expr
    write(LATEX / "excerpt.tex", "% Generated by scripts/build_excerpt.py\n" + tex)
    revised = load(5).splitlines()
    assert revised[84] == "- 为什么金融模型的样本外评估更困难？"
    assert revised[75].startswith("### Part IV")
    question_md = "\n".join(revised[77:87])
    request = load(57)
    write(LATEX / "reader-questions.tex",
          "% Original passages from source messages 05 (78–87) and 57 (complete).\n"
          + r"\begin{readerquestion}{研究准备中的提问}" + "\n" + tex_inline(question_md)
          + "\n" + r"\end{readerquestion}" + "\n\n"
          + r"\begin{readerquestion}{续读请求}" + "\n" + tex_inline(request)
          + "\n" + r"\end{readerquestion}" + "\n")
    evidence = {
        "display_equations_compared": len(equations), "equation_payloads_equal_after_boundary_trim": True,
        "inline_expressions_meeting_source_multiplicity": len(expected_inline),
        "table_count": 5, "graphics_count": 6, "svg_and_pdf_files_each": 8,
        "prose_source_lines": "58:7–587",
        "source_prose_sha256": hashlib.sha256("\n".join(lines[6:587]).encode("utf-8")).hexdigest(),
    }
    write(ROOT / "reports" / "prototype-conversion.json", json.dumps(evidence, ensure_ascii=False, indent=2)+"\n")
    print(f"{len(equations)} display equations verified, five source tables and six graphics placed.")


if __name__ == "__main__":
    main()
