"""Render the archived component subset to print, without a browser or remote assets."""
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import pymupdf

from build_excerpt import ATTRIBUTES, PALETTE, pandoc_math, styled_path, tex_inline
from inspect_archive import write

BOOK = Path(__file__).resolve().parents[1]
FIG = BOOK / "figures"
COLORS = {
    "#2563eb": "ResearchBlue", "#d97706": "ResearchPeach", "#0d9488": "ResearchSage",
    "#94a3b8": "ResearchSlate", "#64748b": "ResearchSlate", "#dc2626": "ResearchRose",
    "#ea8c35": "ResearchPeach", "#ffffff": "ResearchIvory", "#b45309": "ResearchPeach",
    "#e2e8f0": "ResearchIvory", "#147d79": "ResearchSage", "#334155": "ResearchSlate",
    "#475569": "ResearchSlate", "currentColor": "ResearchSlate",
}
SVG_TAGS = {"svg", "g", "line", "circle", "rect", "ellipse", "text", "path"}
SVG_ATTRS = set(("viewBox width height x y x1 x2 y1 y2 cx cy rx ry r d fill opacity stroke transform "
                 "stroke-width fill-opacity stroke-opacity stroke-dasharray font-size font-weight text-anchor "
                 "dominant-baseline stroke-linecap stroke-linejoin").split())
ATTR = {**ATTRIBUTES, "dominantBaseline": "dominant-baseline",
        "strokeLinecap": "stroke-linecap", "strokeLinejoin": "stroke-linejoin"}
FOREIGN = {"AsyncImage", "Link", "Cite", "MemoryCite", "Entity"}
INLINE = {"Cite", "MemoryCite", "Link", "Entity"}
CONTROL = {"slider", "input", "radio-group", "segmented-control", "checkbox", "button"}
TEX_DANGEROUS = re.compile(r"\\(?:input|include|openout|read|write|special|directlua|catcode|csname|usepackage)\b")


def color(value):
    name = COLORS.get(value, value if value in PALETTE else None)
    return f"#{PALETTE[name]}" if name else value if value == "none" else f"#{PALETTE['ResearchSlate']}"


def raw_tex(tex):
    return "\n\n" + chr(96)*3 + "{=latex}\n" + tex + "\n" + chr(96)*3 + "\n\n"


def protect(source):
    items = []
    def mask(match):
        items.append(match[0])
        return f"@{len(items)-1}@"
    expression = r"\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]"
    return re.sub(expression, mask, source), items


def render_components(jobs):
    # The child receives a clean environment, a temporary working directory and a
    # JS context containing only standard language intrinsics and archived values.
    program = BOOK / "scripts" / "components.mjs"
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required for the component renderer.")
    with tempfile.TemporaryDirectory(prefix="reader-components-") as folder:
        child = subprocess.run([node, "--max-old-space-size=192", str(program)],
                               cwd=folder, env={k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ},
                               input="\n".join(json.dumps(j, ensure_ascii=False) for j in jobs).encode("utf-8"),
                               capture_output=True, check=True, timeout=240)
    responses = [json.loads(s) for s in child.stdout.decode("utf-8").splitlines()]
    assert len(responses) == len(jobs), (len(responses), len(jobs))
    return responses


def tree(events, items):
    root = ("root", {}, [])
    stack = [root]
    def restore(value):
        return re.sub(r"@(\d+)@", lambda m: items[int(m[1])] if int(m[1]) < len(items) else m[0], value)
    for op, *args in events:
        if op == "t":
            stack[-1][2].append(restore(args[0]))
        elif op == "o":
            tag, attrs, closed = args
            attrs = {k: restore(v) if isinstance(v, str) else v for k,v in attrs.items()}
            node = (tag, attrs, [])
            stack[-1][2].append(node)
            if not closed:
                stack.append(node)
        else:
            assert stack[-1][0] == args[0], (stack[-1][0], args[0])
            stack.pop()
    assert len(stack) == 1
    return root


def make_svg(node, overrides=None):
    tag, attrs, children = node
    assert tag in SVG_TAGS
    clean = {}
    for key, value in attrs.items():
        key = ATTR.get(key, key)
        if key in SVG_ATTRS:
            clean[key] = color((overrides or {}).get(value,value)) if key in {"fill","stroke"} else str(value)
    if tag == "svg":
        coords = str(attrs.get("viewBox", "0 0 340 200")).split()
        clean.update(xmlns="http://www.w3.org/2000/svg", width=coords[-2], height=coords[-1])
    if tag == "text":
        clean["font-family"] = "serif"
        clean.setdefault("fill", color("currentColor"))
    props = "".join(" "+k+"="+quoteattr(v) for k,v in clean.items())
    content = "".join(escape(child if tag == "text" else child.strip())
                      if isinstance(child,str) else make_svg(child,overrides) for child in children)
    return f"<{tag}{props}>{content}</{tag}>"


def export_svg(stem, svg):
    FIG.mkdir(exist_ok=True)
    target = FIG / f"{stem}.pdf"
    write(FIG / f"{stem}.svg", svg+"\n")
    with pymupdf.open("svg", svg.encode("utf-8")) as graphic:
        target.write_bytes(graphic.convert_to_pdf())
    with pymupdf.open(target) as vector:
        page = vector[0]
        assert page.get_drawings() and not page.get_image_info(), stem
        return page.rect.width, page.rect.height


def chart_svg(props):
    """Replot the archived series, using original axis limits when given."""
    data, series = props["data"], props["series"]
    kind = props["chartType"]
    assert kind in {"line","bar"}
    values = [row[s["dataKey"]] for row in data for s in series if isinstance(row.get(s["dataKey"]),(int,float))]
    assert values
    lo = props.get("yAxisMin", min(values) if kind == "line" else min(0,*values))
    hi = props.get("yAxisMax", max(values))
    if hi == lo:
        lo, hi = lo-.5, hi+.5
    pad = .06*(hi-lo)
    lo = lo-pad if "yAxisMin" not in props and not (kind=="bar" and lo==0) else lo
    hi = hi+pad if "yAxisMax" not in props else hi
    width, height = 420, 171 + 15*((len(series)-1)//2)
    x0, x1, y0, y1 = 45, 407, 14, 122
    x = lambda i: x0+(x1-x0)*(i+.5)/len(data) if kind == "bar" else x0+(x1-x0)*i/max(1,len(data)-1)
    y = lambda value: y1-(y1-y0)*(value-lo)/(hi-lo)
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">']
    ink = color("ResearchSlate")
    def label(xv,yv,text,anchor="middle",size=10):
        pieces.append(f'<text x="{xv}" y="{yv}" text-anchor="{anchor}" font-size="{size}" font-family="serif" fill="{ink}">{escape(str(text))}</text>')
    def line(a,b,c,d,ink,opacity=1, weight=1):
        pieces.append(f'<path d="M{a} {b} L{c} {d}" stroke="{ink}" stroke-width="{weight}" opacity="{opacity}"/>')
    line(x0,y0,x0,y1,ink,.6)
    line(x0,y1,x1,y1,ink,.6)
    for index in range(5):
        n=lo+(hi-lo)*index/4
        line(x0,y(n),x1,y(n),ink,.16)
        label(x0-5,y(n)+3,f"{n:.4g}","end")
    step=max(1,math.ceil(len(data)/9))
    for i,row in enumerate(data):
        if i % step == 0 or i == len(data)-1:
            text=str(row[props["xKey"]])
            label(x(i),y1+11+(i%2*10 if len(text)>7 else 0),text,size=9)
    sequence = ["ResearchBlue","ResearchSlate","ResearchSage","ResearchRose","ResearchPeach","ResearchMint"]
    score_colors={"val":"ResearchBlue","is":"ResearchBlue","test":"ResearchPeach","oos":"ResearchPeach",
                  "audit":"ResearchPeach","pop":"ResearchSage","same":"ResearchPeach","shift":"ResearchRose"}
    for index,s in enumerate(series):
        ink_series=color(score_colors.get(s["dataKey"],sequence[index%len(sequence)]))
        points = [(x(i),y(row[s["dataKey"]])) for i,row in enumerate(data)
                  if isinstance(row.get(s["dataKey"]),(int,float))]
        style = None if index%3 == 0 else (6,3) if index%3 == 1 else (2,3)
        if kind=="line":
            pieces.append(f'<path d="{styled_path(points,style)}" fill="none" stroke="{ink_series}" stroke-width="1.8"/>')
            for xv,yv in points:
                pieces.append(f'<circle cx="{xv}" cy="{yv}" r="1.45" fill="{ink_series}"/>')
        else:
            bar = (x1-x0)/len(data)*.77/len(series)
            zero=y(max(lo,min(hi,0)))
            for xv,yv in points:
                pieces.append(f'<rect x="{xv+bar*(index-len(series)/2)}" y="{min(yv,zero)}" '
                              f'width="{bar*.94}" height="{abs(zero-yv)}" fill="{ink_series}"/>')
        mark_x=23+index%2*202
        mark_y=159+index//2*15
        pieces.append(f'<path d="{styled_path(((mark_x,mark_y),(mark_x+16,mark_y)), style if kind=="line" else None)}" stroke="{ink_series}" stroke-width="2"/>')
        label(mark_x+22,mark_y+3,s.get("label",s["dataKey"]),"start")
    return "".join(pieces+["</svg>"])


def flowchart(code):
    """The archive's Mermaid figure is a single top-to-bottom chain."""
    lines=code.strip().splitlines()
    assert lines[0].strip()=="flowchart TD"
    labels={}
    edges=[]
    for line in lines[1:]:
        found=re.fullmatch(r"\s*(\w+)(?:\[([^\]]+)\])?\s*-->\s*(\w+)(?:\[([^\]]+)\])?\s*",line)
        assert found, line
        first,left,second,right=found.groups()
        edges.append((first,second))
        if left:
            labels[first]=left
        if right:
            labels[second]=right
    order=[edges[0][0]]+[b for _,b in edges]
    assert edges==list(zip(order,order[1:])) and set(order)==set(labels)
    # The direction remains top-to-bottom. Native SVG text remains selectable.
    w,h=354,len(order)*32
    ink, fill=color("ResearchBlue"),color("ResearchMint")
    result=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">']
    for i,key in enumerate(order):
        y=2+i*32
        result.append(f'<rect x="55" y="{y}" width="244" height="21" rx="3" fill="{fill}" fill-opacity=".32" stroke="{ink}"/>')
        result.append(f'<text x="177" y="{y+14}" text-anchor="middle" font-size="11" font-family="serif" fill="{ink}">{escape(labels[key])}</text>')
        if i+1<len(order):
            result.append(f'<path d="M177 {y+21}v10 m-3 -4 l3 4 3 -4" fill="none" stroke="{ink}"/>')
    return "".join(result+["</svg>"])


def slider_variant(source, response):
    """Select a meaningful endpoint from the first numeric control of a plot."""
    if "error" in response or not any(e[:2]==["o","svg"] for e in response["events"]):
        return None
    states=re.findall(r"const\s+\[\s*(\w+)\s*,[^\]]+\]\s*=\s*DIL\.useState",source)
    names=re.findall(r"<slider\b[^\n>]*?\bvalue=\{(\w+)\}",source)
    sliders=[event[2] for event in response["events"] if event[:2]==["o","slider"]]
    for name,control in zip(names,sliders):
        if name not in states or not all(isinstance(control.get(k),(int,float)) for k in ("min","max","value")):
            continue
        lo,hi,current=(control[k] for k in ("min","max","value"))
        if hi<=lo:
            continue
        alternate=lo if current-lo>hi-current else hi
        return states.index(name),name,alternate
    return None


def scalar(value):
    if isinstance(value,bool):
        return str(value).lower()
    if isinstance(value,float):
        return f"{value:g}"
    return str(value)


def flatten(node):
    if isinstance(node,str):
        return node
    return "".join(flatten(child) for child in node[2])


def color_strip(node):
    if isinstance(node,str) or node[0]!="row":
        return None
    cells=[child for child in node[2] if not isinstance(child,str) or child.strip()]
    if len(cells)<3 or any(isinstance(cell,str) or cell[0] not in {"box","text","caption"} for cell in cells):
        return None
    output=[]
    for cell in cells:
        _,attrs,_=cell
        value=" ".join(flatten(cell).split())
        background=str(attrs.get("background",""))
        if not value or len(value)>16 or any(c in value for c in ("\\","*","[",chr(96))):
            return None
        output.append((value,background if background.startswith("#") else None))
    return output if sum(background is not None for _,background in output)>=2 else None


def strips_svg(rows):
    width=402
    height=len(rows)*25+2
    ink=color("ResearchSlate")
    ivory=color("ResearchIvory")
    body=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    for index,row in enumerate(rows):
        label=not row[0][1] and any(background for _,background in row[1:])
        lead=66 if label else 0
        step=(width-lead)/(len(row)-int(label))
        left=0
        for i,(text,background) in enumerate(row):
            cellwidth=lead if label and i==0 else step
            y=25*index+1
            fill=color(background) if background else "none"
            body.append(f'<rect x="{left+1}" y="{y}" width="{cellwidth-3}" height="21" rx="2" fill="{fill}" fill-opacity=".90"/>')
            fg=ivory if background in {"#2563eb","#64748b"} else ink
            body.append(f'<text x="{left+cellwidth/2}" y="{y+14}" font-family="serif" font-size="12" text-anchor="middle" fill="{fg}">{escape(text)}</text>')
            left+=cellwidth
    return "".join(body+["</svg>"])


def convert_tree(root, stem, refs, establish):
    """Convert content and graphics in source order, including structured readouts."""
    graphics = []
    text=flatten(root)
    overrides={"#d97706":"ResearchSlate"} if "Standard Normal" in text and "Student" in text else {}
    def contains_checkbox(node):
        return not isinstance(node,str) and (
            node[0]=="checkbox" or any(contains_checkbox(child) for child in node[2]))
    checklist=contains_checkbox(root)
    def graphic(svg, tag, caption=""):
        name = f"{stem}-{len(graphics)+1:02d}"
        width,height = export_svg(name,svg)
        ratio=height/width
        use_width=min(.9, .83 if width>305 else .58, .32/max(ratio,.01))
        graphics.append({"stem":name,"type":tag})
        return raw_tex(r"\bookgraphic{" + f"{use_width:.3f}" + "}{" + name + "}{" + caption + "}")
    def graph(tag, attrs, node, caption=""):
        svg=make_svg(node,overrides) if tag=="svg" else chart_svg(attrs["content"])
        return graphic(svg,tag,caption)
    def walk(node):
        if isinstance(node,str):
            return node
        tag, attrs, children = node
        if tag in {"svg","Chart"}:
            return graph(tag,attrs,node)
        if tag == "AsyncImage":
            establish("missing-image",attrs.get("query",""))
            return ""
        if tag in CONTROL:
            # Preserve the default state and the adjustable limits in print.
            if tag in {"slider","input"}:
                value=scalar(attrs.get("value",""))
                if "min" in attrs and "max" in attrs:
                    value += "（范围 " + scalar(attrs["min"]) + "–" + scalar(attrs["max"]) + "）"
                return " " + value + " "
            if tag in {"checkbox","button"}:
                return "\n- "+" ".join(flatten(node).split())+"\n" if tag=="checkbox" else ""
            if tag=="segmented-control":
                return " " + " / ".join(str(option["label"]) for option in attrs.get("options",[])) + " "
        if tag == "math":
            value=str(attrs.get("value","")).replace("\\\\","\\")
            if TEX_DANGEROUS.search(value):
                raise ValueError("Unsafe TeX in component math")
            return ("\n\n\\[" + value + "\\]\n\n") if attrs.get("block") else r"\(" + value + r"\)"
        if tag == "Cite":
            ids=attrs.get("refs") or [attrs.get("ref")]
            values=[refs.get(i) for i in ids if i]
            if not values or None in values:
                establish("citation-target-missing", " ".join(i for i in ids if i))
            return "".join(f" [来源 {index}]({url})" for index,url in enumerate(filter(None,values),1))
        if tag == "MemoryCite":
            establish("memory-citation-missing","")
            return ""
        if tag == "Entity":
            return str(attrs.get("value",""))
        if tag == "Link":
            text="".join(walk(child) for child in children).strip()
            url=attrs.get("url","")
            return f"[{text}]({url})" if str(url).startswith(("https://","http://")) else text
        if tag == "icon":
            arrows={"arrow-right":" → ","arrow-down":" ↓ ","arrow-left":" ← ","arrow-up":" ↑ ",
                    "chevron-right":" → ","chevron-down":" ↓ "}
            return arrows.get(attrs.get("name"),"")
        if tag in {"divider","spacer"}:
            return "\n" if tag=="divider" else " "
        if tag == "table":
            rows = []
            def collect(n):
                if not isinstance(n,str):
                    if n[0]=="table-row":
                        rows.append([" ".join(walk(cell).split()).replace("|",r"\|") for cell in n[2]
                                     if not isinstance(cell,str) and cell[0]=="table-cell"])
                    else:
                        for q in n[2]:
                            collect(q)
            collect(node)
            if rows and len(rows[0]) and len(set(map(len, rows))) == 1:
                pipe = lambda cells: "| " + " | ".join(cells) + " |\n"
                return "\n\n" + pipe(rows[0])+pipe(["---"]*len(rows[0]))+"".join(map(pipe,rows[1:]))+"\n"
        pieces=[]
        children=[child for child in children if not isinstance(child,str) or child.strip()]
        index=0
        while index<len(children):
            child=children[index]
            strip=color_strip(child)
            if strip:
                strips=[strip]
                while index+1<len(children) and (following:=color_strip(children[index+1])):
                    strips.append(following)
                    index+=1
                pieces.append(graphic(strips_svg(strips),"component strip"))
            elif not isinstance(child,str) and child[0] in {"svg","Chart"}:
                adjacent=index+1
                caption=""
                if adjacent<len(children):
                    following=children[adjacent]
                    if not isinstance(following,str) and following[0]=="caption":
                        wording=" ".join(walk(following).split())
                        if wording:
                            caption=tex_inline(pandoc_math(wording))
                        index=adjacent
                pieces.append(graph(child[0],child[1],child,caption))
            else:
                pieces.append(walk(child))
            index+=1
        content="".join(pieces).strip()
        if not content:
            return ""
        if checklist and tag=="caption" and re.fullmatch(r"\d+\s*/\s*\d+",content):
            return ""
        if tag == "title":
            return "\n\n**"+content+"**\n\n"
        if tag in {"caption","label","table-cell","list-item","radio"}:
            return " "+content+" " if tag=="label" else "\n\n"+content+"\n\n"
        return "\n\n"+content+"\n\n"
    content=walk(root)
    return content,graphics


def variant_figures(root, stem, name, value, limit):
    """Extract only the vector state panels. The default supplies the prose."""
    figures=[]
    def visit(node):
        if isinstance(node,str):
            return
        if node[0]=="svg":
            figures.append(node)
        else:
            for child in node[2]:
                visit(child)
    visit(root)
    if not figures or len(figures)>limit:
        return "",0
    result = f"\n\n{name} = {scalar(value)}\n\n"
    text, assets=convert_tree(("root",{},figures),stem,{},lambda *_:None)
    return result+text,len(assets)
