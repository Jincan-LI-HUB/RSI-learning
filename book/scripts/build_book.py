"""Build the approved private transcript into public, source-aligned print files."""
import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
PROJECT = BOOK.parent
sys.path.insert(0,str(PROJECT/"reader_prototype"/"scripts"))
from inspect_archive import FENCE, BODY, tags, mask_spans, write
from build_excerpt import MATH_RE

from build_excerpt import pandoc_math, run_pandoc
from visuals import (convert_tree, protect, raw_tex, render_components, tree, TEX_DANGEROUS,
                     export_svg, flowchart, slider_variant, variant_figures)

ARCHIVE=PROJECT/"reader_prototype/archive/normalized-path.jsonl"
CHAPTERS=BOOK/"chapters"
PATTERNS=re.compile(r"<(?:Cite|MemoryCite|Entity)\b[^\n]*?/>|<Link\b[^\n]*?</Link>")
RUNTIME_LINK=re.compile(r"(\[[^\]\n]+\])\(\{(turn\w+)\.url\.uri\}\)")
STAGE=re.compile(r"^((?:II|III|IV)-[A-F]) [—–-] ")
GROUPS={
    1:((3,"研究问题初探"),(7,"根据项目说明细化研究问题"),(10,"Conclusion & Concept Index")),
    2:tuple((n,None) for n in (12,14,16,20,23,27)),
    3:tuple((n,None) for n in (31,34,37,40,44,48)),
    4:tuple((n,None) for n in (52,58,60,63,67,71,77)),
}
PART_NAMES={
    1:"Understanding the Research Problem",
    2:"Statistical Learning Theory",
    3:"Agentic AI and Recursive Self-Improvement",
    4:"Financial AI & Quantitative Research",
}
STATUS=BOOK/"audit"
READER="markdown-smart-raw_html-raw_tex+raw_attribute"
BODY_LINE=re.compile(r"(?m)^[ \t]*(?:---+)[ \t]*\n")
# Preserve the tested six recovered figures in their original locations.
PROTOTYPE=PROJECT/"reader_prototype/latex"
PROTOTYPE_GRAPHICS={
    (PROTOTYPE/"figures"/f"{stem}.source.txt").read_text(encoding="utf-8").strip(): block[2]
    for stem,block in zip(
        ("volatility","acf","garch-mechanism","garch-persistence","densities","tail-probability"),
        FENCE.finditer((PROTOTYPE/"excerpt.md").read_text(encoding="utf-8")), strict=True)
}


def reading_rows():
    rows=[json.loads(line) for line in ARCHIVE.read_text(encoding="utf-8").splitlines()]
    return {r["stored_ordinal"]:r for r in rows}


def reference_urls(message):
    result={}
    for group in message["metadata"].get("search_result_groups") or []:
        for item in group.get("entries",[]):
            ref=item.get("ref_id") or {}
            url=item.get("url","")
            if ref and url.startswith(("https://","http://")):
                result[f'turn{ref["turn_index"]}{ref["ref_type"]}{ref["ref_index"]}']=url
    return result


def make_plans(rows):
    plans=[]
    for part,chapters in GROUPS.items():
        for n,title in chapters:
            original=rows[n]["content"][0]["text"]
            limit=None
            if n==52:
                marker="## 6.2 Volatility Clustering"
                start=original.index(marker)
                limit=original.count("\n",0,start)
                plans.append((part,n,"IV-A — Financial Time Series & Data Generating Process",1,original[:start]))
                # Preserve the initial exposition of overlapping sections as a
                # complementary reading. Its code, figures and derivation variants
                # are not equivalent to the continuation at the block level.
                plans.append((part,n,"IV-A — 初稿中的补充推导与例图",limit+1,original[start:]))
                continue
            if n==58:
                start=original.index("## 6.2 Volatility Clustering")
                plan=(part,n,"IV-A — 波动率聚集、厚尾与时间依赖",original.count("\n",0,start)+1,original[start:])
            else:
                if title is None:
                    title=next(line.lstrip("# ") for line in original.splitlines()
                               if re.match(r"^#\s+(?:II|III|IV)-[A-F]\s+[—–-]",line))
                plan=(part,n,title,1,original)
            plans.append(plan)
    return plans


def source_jobs(source, refs):
    plain=mask_spans(source,FENCE.finditer(source))
    parsed, unmatched=tags(plain)
    if unmatched:
        raise ValueError(f"Unmatched component tags: {unmatched[:10]}")
    declarations=[m.span() for m in BODY.finditer(plain)]
    ranges=[]
    roots=[(lo,hi,tag) for lo,hi,tag,depth in parsed if depth==0]
    for lo,hi,tag in roots:
        begin=lo
        for a,b in reversed(declarations):
            if b<=begin:
                if not plain[b:begin].strip():
                    begin=a
                else:
                    break
        ranges.append((begin,hi,tag))
    for m in PATTERNS.finditer(plain):
        if not any(lo<=m.start()<hi for lo,hi,_ in ranges):
            ranges.append((m.start(),m.end(),"inline"))
    ranges.sort()
    return [(a,b,tag,*protect(source[a:b]),refs) for a,b,tag in ranges]


def structure(source, title, part):
    protected = {}
    def stash(match):
        key = f"\n\n@@@@CODE{len(protected)}@@@@\n\n"
        protected[key.strip()] = match[0]
        return key
    source = FENCE.sub(stash,source)
    headings=[]
    def heading(match):
        depth,label=len(match[1]),match[2].strip()
        part_heading=f"Part {('I','II','III','IV')[part-1]} — {PART_NAMES[part]}"
        if label in {title,"X Program #161 — Research Preparation",part_heading}:
            return ""
        # Original organizing labels are retained. Their Markdown depths were
        # inconsistent between responses, so use the numbering where present.
        decimal=re.match(r"^(?:\d+(?:\.\d+)*)(?:[.\s]|$)",label)
        if decimal:
            numbers=re.match(r"^\d+(?:\.\d+)*",label)[0]
            level = min(4, 2+numbers.count("."))
        elif re.match(r"^(Part [IV0]+|Next\s+[—–-])",label) or STAGE.match(label):
            level=2
        else:
            level=min(5,max(2,depth+1))
        headings.append(label)
        return "#"*level+" "+label
    source=re.sub(r"(?m)^(#{1,6})[ \t]+(.+)$",heading,source)
    source=BODY_LINE.sub("\n",source)
    for key, content in protected.items():
        source=source.replace(key,content)
    return "# "+title+"\n\n"+source


def audit_math(original, converted, note):
    def normalized(value):
        return re.sub(r"\s+", "",value)
    before=collections.Counter(normalized(m[2]) for m in MATH_RE.finditer(original))
    after=collections.Counter(normalized(m[2]) for m in MATH_RE.finditer(converted))
    missing=before-after
    if missing:
        # Public audit locates math by chapter and count, without private IDs.
        note["missing_math_payloads"]=list(missing.items())[:12]
    note["source_math"]=sum(before.values())
    note["matched_math"]=sum((before&after).values())


def protected_displays(markdown):
    # Pandoc can read a standalone minus sign in a multiline display as a
    # simple-table separator. Export complete source displays as raw blocks.
    def convert(segment):
        return MATH_RE.sub(lambda m: raw_tex(r"\[" + m[2].strip() + r"\]")
                           if m[1]=="[" else m[0], segment)
    output=[]
    offset=0
    for match in FENCE.finditer(markdown):
        output.extend([convert(markdown[offset:match.start()]),match[0]])
        offset=match.end()
    return "".join(output+[convert(markdown[offset:])])


def table_widths(table):
    specs=table[2]
    total=len(specs)
    if total<2 or any(spec[1]["t"]!="ColWidthDefault" for spec in specs):
        return
    weights=[3.0]*total
    def measure(item):
        if isinstance(item,str):
            return sum(2 if ord(c)>0x2e80 else 1 for c in item)
        if isinstance(item,list):
            return sum(measure(x) for x in item)
        if isinstance(item,dict):
            return measure(item.get("c",[]))
        return 0
    rows=table[3][1] + [row for body in table[4] for row in body[2]+body[3]]
    for _,cells in rows:
        if len(cells)==total:
            for i,cell in enumerate(cells):
                weights[i]=max(weights[i],min(68,measure(cell[-1]))**.72)
    for spec,weight in zip(specs,weights,strict=True):
        spec[1]={"t":"ColWidth","c":round(.96*weight/sum(weights),4)}


def plain_fallback(template):
    # Preserve literal component labels and math when dynamic evaluation
    # fails. The source location and unrecovered figure are audited.
    template=re.sub(r"(?m)^.*\{@body.*\n?","",template)
    template=re.sub(r"<svg\b[\s\S]*?</svg>", "", template)
    result=[]
    for line in template.splitlines():
        kept=re.sub(r"^\s*\{(?:#|/|:)[^\n]*$", "",line)
        m=re.search(r'<math[^>]*value="([^"]+)"', kept)
        if m:
            result.append(r"\("+m[1].replace("\\\\","\\")+r"\)")
        kept=re.sub(r"</?[\w-]+(?:\s[^<>]*)?/?>", " ", kept)
        kept=re.sub(r"\{[#/:@].*?\}", "", kept)
        if kept.strip():
            result.append(kept.strip())
    return "\n\n"+"\n\n".join(result)+"\n\n"


def render_plan(plan,rows):
    part,n,title,first,source=plan
    stem=f"part-{part}-{n:02d}-{first:04d}"
    refs={key:url for message in rows.values() for key,url in reference_urls(message).items()}
    jobs=source_jobs(source,refs)
    defaults=render_components([{"source":job[3],"refs":refs} for job in jobs])
    variants={}
    requests=[]
    for index,(job,response) in enumerate(zip(jobs,defaults,strict=True),1):
        if n==58 and source[job[0]:job[1]].strip() in PROTOTYPE_GRAPHICS:
            continue
        state=slider_variant(job[3],response)
        if state is not None:
            slot,name,value=state
            requests.append((index,name,value,{"source":job[3],"refs":refs,"overrides":{slot:value}}))
    for request,response in zip(requests,render_components([q[3] for q in requests]),strict=True):
        index,name,value,_=request
        if "error" not in response:
            variants[index]=(name,value,response)
    replacements=[]
    records=[]
    for index,(job,res) in enumerate(zip(jobs,defaults,strict=True),1):
        lo,hi,tag,protected,items,_=job
        line=first+source.count("\n",0,lo)
        identifier=f"{stem}-{index:03d}"
        rec={"part":part,"message":n,"line":line,"component":tag}
        source_component=source[lo:hi].strip()
        reused=PROTOTYPE_GRAPHICS.get(source_component) if n==58 else None
        if n==77 and "已完成 4 / 6 个 Part。" in source_component:
            md=""
            rec.update(state="navigation omitted",graphics=0)
        elif reused:
            md=raw_tex(reused.replace("{figures/","{../reader_prototype/latex/figures/"))
            rec.update(state="approved vector",graphics=1)
        elif "error" not in res:
            try:
                def establish(type_,detail):
                    if type_ not in {"citation-target-missing","memory-citation-missing"}:
                        rec.setdefault("gaps",[]).append({"type":type_,"detail":detail})
                    else:
                        rec["unresolved_citations"]=rec.get("unresolved_citations",0)+1
                md,figures=convert_tree(tree(res["events"],items),identifier,refs,establish)
                rec.update(state="converted", graphics=len(figures))
                if res["states"]:
                    rec["defaults"]=[item if not isinstance(item,(dict,list)) else type(item).__name__
                                     for item in res["states"]]
                if index in variants and figures:
                    name,value,response=variants[index]
                    fragment,num=variant_figures(tree(response["events"],items),identifier+"-state",
                                                 name,value,limit=2)
                    md+=fragment
                    rec["graphics"]+=num
                    if num:
                        rec["print_states"]=2
            except (AssertionError,ValueError,KeyError,RuntimeError,TypeError) as error:
                rec.update(state="fallback", reason=str(error)[:180],graphics=0)
                md=plain_fallback(source_component)
        else:
            rec.update(state="fallback",reason=res["error"][:180],graphics=0)
            md=plain_fallback(source_component)
        replacements.append((lo,hi,md))
        records.append(rec)
    content=source
    for lo,hi,md in reversed(replacements):
        content=content[:lo]+md+content[hi:]
    def resolve_link(match):
        label,identifier=match.groups()
        if identifier in refs:
            return label+"("+refs[identifier]+")"
        records.append({"part":part,"message":n,"component":"link","state":"label preserved",
                        "graphics":0,"unresolved_citations":1})
        return label[1:-1]
    content=RUNTIME_LINK.sub(resolve_link,content)
    def mermaid(match):
        if match[1].strip().lower()!="mermaid":
            return match[0]
        variant=f"{stem}-evaluation-pipeline"
        export_svg(variant,flowchart(match[2]))
        write(BOOK/"figures"/f"{variant}.mmd",match[2])
        records.append({"part":part,"message":n,"component":"mermaid","state":"converted","graphics":1})
        return raw_tex(r"\bookgraphic{.62}{"+variant+"}{}")
    content=FENCE.sub(mermaid,content)
    if n==7:
        # The author's project brief is substantive. Import the description
        # field only. Contact information and the reader's profile are private.
        brief=next(line for line in rows[5]["content"][0]["text"].splitlines()
                   if line.startswith("| 161 |")).split("|")[8].strip()
        assert brief.startswith("Recursive") and brief.endswith("typical in finance.")
        content=content.replace(
            "这一次有了完整的项目原文，我们可以更加准确地确定学习范围，而不必仅仅根据标题推测课题的研究内容。",
            "> "+" ".join(brief.split()),1)
        content=content.replace("我重新审视了项目描述。这个课题本质上是一个","这个课题是一个",1)
    elif n==10:
        content=content.removeprefix("确实，").replace(
            "我们现在将 Part I 压缩成一份 **Conclusion & Concept Index**。保留核心定义、数学结论、成立条件及研究意义，具体证明直接索引回前面的章节。",
            "**Conclusion & Concept Index** 汇集核心定义、数学结论、成立条件及研究意义。具体证明见前文。",1)
    content=structure(content,title,part)
    if TEX_DANGEROUS.search(" ".join(m[2] for m in MATH_RE.finditer(content))):
        raise ValueError("Unsafe control sequence in source math")
    ast=json.loads(run_pandoc(["-f",READER,"-t","json"],pandoc_math(protected_displays(content))))
    table_count=sum(1 for block in ast["blocks"] if block["t"]=="Table")
    # The publication uses the source's table cells. Consistent counter labels
    # introduce tables that were untitled in the chat, without invented captions.
    for block in ast["blocks"]:
        if block["t"]=="Table":
            table_widths(block["c"])
            if not block["c"][1][1]:
                block["c"][1]=[None,[{"t":"Plain","c":[]}]]
    tex=run_pandoc(["-f","json","-t","latex","--no-highlight","--wrap=none"],json.dumps(ast,ensure_ascii=False))
    tex=re.sub(r"(?m)^([^\\\n].*[：:])\n\n(?=\\\[)",r"\1\n",tex)
    lead=r"(?:因此|于是|其中|所以|进一步|即|注意|设|也就是说)"
    tex=re.sub(r"(?m)([。；])\n\n(?="+lead+r"[：:])",r"\1 ",tex)
    tex=tex.replace(r"\begin{longtable}", "\\begin{readertable}\n\\begin{longtable}")
    tex=tex.replace(r"\end{longtable}", "\\end{longtable}\n\\end{readertable}")
    tex=re.sub(r"(\\(?:hypertarget|hyperlink|label)\{)([^}]+)",rf"\g<1>{stem}-\2",tex)
    if n==77:
        tex=re.sub(r"(?m)^(\\hypertarget\{[^}\n]+next-part-v-literature-research-frontier\})",
                   r"\\Needspace{.34\\textheight}\n\1",tex,count=1)
    note={"part":part,"message":n,"first_line":first,"last_line":first+source.count("\n"),
          "chapter":stem,"chosen_title":title,"tables":table_count,
          "source_sha256":hashlib.sha256(source.encode("utf-8")).hexdigest()}
    # Compare text outside components separately so interactive expressions
    # and figure labels cannot be mistaken for dropped narrative formulas.
    prose=source
    for lo,hi,_ in reversed(replacements):
        prose=prose[:lo]+"\n\n"+prose[hi:]
    audit_math(mask_spans(prose,FENCE.finditer(prose)),tex,note)
    for rec in records:
        rec.pop("defaults",None)  # print values are in the manuscript, private UI state is not published
    write(CHAPTERS/f"{stem}.tex",f"% Archive record {n}, line {first}.\n"+tex)
    write(STATUS/f"{stem}.json",json.dumps({"chapter":note,"components":records},ensure_ascii=False,indent=2)+"\n")
    return stem,note,records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--part",type=int,choices=range(1,5))
    args=parser.parse_args()
    rows=reading_rows()
    by_part=collections.defaultdict(list)
    for plan in make_plans(rows):
        if args.part and plan[0]!=args.part:
            continue
        stem,note,recs=render_plan(plan,rows)
        by_part[plan[0]].append(stem)
        print(stem, f'{note["matched_math"]}/{note["source_math"]} math', note["tables"],"tables",
              sum(r["graphics"] for r in recs),"vectors",sum(r["state"]=="fallback" for r in recs),"fallbacks",flush=True)
    for part,stems in by_part.items():
        lines=[r"\part{"+PART_NAMES[part].replace("&",r"\&")+"}"]
        lines+=[r"\input{chapters/"+stem+"}" for stem in stems]
        write(CHAPTERS/f"part-{part}.tex","\n".join(lines)+"\n")


if __name__=="__main__":
    main()
