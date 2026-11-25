"""Independently reconcile the public LaTeX against the verified private archive."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

BOOK = Path(__file__).resolve().parents[1]
ROOT = BOOK.parent
LOCAL = ROOT / "reader_prototype" / "archive"
sys.path.insert(0, str(ROOT / "reader_prototype" / "scripts"))
from inspect_archive import BODY, FENCE, mask_spans, tags
from build_excerpt import MATH_RE, pandoc_math, run_pandoc
from release_edits import amend

AUDIT = BOOK / "audit"
EXPECTED_ARCHIVE = "87b0e070478274a92d6fab790b974b99b833e706c7cb47a0efe3440b38551d4a"
LATEX_CODE = re.compile(r"(?ms)^\\begin\{verbatim\}\n(.*?)^\\end\{verbatim\}")
LONGTABLE = re.compile(r"(?ms)^\\begin\{longtable\}.*?^\\end\{longtable\}")
INLINE_TAGS = re.compile(r"</?(?:Cite|MemoryCite|Entity|Link|icon)\b[^>\n]*>")
EDITORIAL_PROSE = {
    3: set(),
    7: {"这一次有了完整的项目原文，我们可以更加准确地确定学习范围，而不必仅仅根据标题推测课题的研究内容。",
        "我重新审视了项目描述。这个课题本质上是一个"},
    10: {"确实，", "我们现在将 Part I 压缩成一份 "},
}

DIRECTED = {
    1: ("intellectual brief mapped", "Part I initial roadmap; Parts II–IV teaching sequence; Part V/VI roadmaps",
        "Research questions and constraints are followed in the reading sequence. Personal biography/contact context and requests to the chat remain private."),
    5: ("project description included; intellectual brief mapped", "Part I revised roadmap and project description; Part V/VI roadmaps",
        "Only the project's substantive description is reproduced verbatim. Repeated learning brief is integrated into the existing route. Contact and personal profile are private."),
    9: ("pedagogical request incorporated", "Part I Conclusion & Concept Index",
        "The original conversational wording is held locally. The need to handle cognitive load by reading conclusions before following proof pointers is explicit in the manuscript."),
    54: ("alternate compared", "IV-A preview and IV-B derivation; private alternate",
         "The completion confirmation and progress panel are chat navigation. The SNR result and route are already represented."),
    56: ("alternate compared; distinct material integrated", "IV-A selected continuation §§6.3, 8.3; private alternate",
         "Only the variance inference and ESS-to-generalization qualification were recovered. See alternative-differences.csv for block dispositions."),
    72: ("supporting computation retained locally", "Private tool trace; IV-E numerical examples",
         "Executable support trace, whose associated mathematical findings are presented in the teaching reply."),
    73: ("supporting output retained locally", "Private tool trace; IV-E numerical examples",
         "Machine output supporting the IV-E example is retained with its source computation."),
}
ROUTINE = {11,13,15,18,22,25,29,33,36,39,42,46,50,59,62,65,69,75}
DISPLAY = {53,55,57}
PREAMBLES = {2:3,6:7,19:20,26:27,30:31,43:44,47:48,51:52,66:67,70:71,76:77}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def archive():
    signed = (LOCAL / "SHA256.txt").read_text(encoding="utf-8").split()
    source = next(ROOT.glob("*__6b057087.json"))
    original = source.read_bytes()
    assert signed[0] == digest(original) == EXPECTED_ARCHIVE
    assert (LOCAL / source.name).read_bytes() == original
    raw = json.loads(original)["conversation"]["messages"]
    stored = [json.loads(line) for line in (LOCAL/"normalized-all.jsonl").read_text(encoding="utf-8").splitlines()]
    active = [json.loads(line) for line in (LOCAL/"normalized-path.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(raw) == len(stored) == 78
    identifiers = {row["id"]: index for index, row in enumerate(raw,1)}
    hidden = {index for index,row in enumerate(raw,1)
              if row["metadata"].get("is_visually_hidden_from_conversation")}
    described = {i for i,r in enumerate(stored,1) if r["disposition"]=="hidden"}
    assert hidden==described and len(hidden)==17
    current = max((r for i,r in enumerate(raw,1) if i not in hidden), key=lambda r:r["created_at"])
    ancestry = []
    while current:
        ordinal=identifiers[current["id"]]
        assert ordinal not in ancestry
        ancestry.append(ordinal)
        predecessor=current["parent_id"]
        current=raw[identifiers[predecessor]-1] if predecessor else None
    ancestry.reverse()
    assert ancestry==[r["stored_ordinal"] for r in active] and len(ancestry)==57
    for n,(raw_row,norm) in enumerate(zip(raw,stored,strict=True),1):
        assert n==norm["stored_ordinal"]
        assert all(norm[key]==value for key,value in raw_row.items())
        assert norm["disposition"]==("hidden" if n in hidden else "active" if n in ancestry else "alternate")
    return raw, stored, ancestry


def intervals(lines, expected):
    first, last = expected["first_line"], expected["last_line"]
    for end in (last,last-1):
        sample="".join(lines[first-1:end])
        if digest(sample.encode())==expected["source_sha256"]:
            return first,end,sample
    raise AssertionError(f"Chapter source did not match snapshot: {expected['chapter']}")


def chapter_scope(raw, stored, ancestry):
    chapters=collections.defaultdict(list)
    for path in sorted(AUDIT.glob("part-*.json")):
        record=json.loads(path.read_text(encoding="utf-8"))["chapter"]
        ordinal=record["message"]
        destination=f"chapters/{record['chapter']}.tex"
        assert (BOOK/destination).read_text(encoding="utf-8").startswith(f'% Archive record {ordinal}, line {record["first_line"]}.')
        lines=raw[ordinal-1]["content"][0]["text"].splitlines(keepends=True)
        start,end,source=intervals(lines,record)
        chapters[ordinal].append((start,end,destination,source))
    teaching = {n for n in ancestry if raw[n-1]["role"]=="assistant"
                and raw[n-1]["content"][0]["type"]=="markdown"
                and not raw[n-1]["metadata"].get("is_thinking_preamble_message")}
    assert teaching==chapters.keys() and len(teaching)==22 and sum(map(len,chapters.values()))==23
    assert ancestry[-1]==77
    assert not any(re.search(r"(?m)^#\s+(?:V|VI)-[A-F]\s+[—–-]",raw[n-1]["content"][0]["text"])
                   for n in teaching)
    assert {n for n in ancestry if raw[n-1]["metadata"].get("is_thinking_preamble_message")}==PREAMBLES.keys()

    rows=[]
    for n, entry in enumerate(stored,1):
        total=len(entry["content"][0]["text"].splitlines())
        branch=entry["disposition"]
        source_range=f"1–{total}"
        if n in teaching:
            destinations=sorted(chapters[n])
            count=7 if n==58 else 1
            for start,end,path,_ in destinations:
                assert count==start, (n,start,count)
                count=end+1
            assert count==total+1, (n,count,total)
            disposition="teaching text mapped"
            destination=" | ".join(f"{a}–{b} → {path}" for a,b,path,_ in destinations)
            rationale=("Lines 1–6 are client-display troubleshooting and separator." if n==58
                       else "Source headings and component presentation normalized. See chapter-level audit.")
        elif n in DIRECTED:
            disposition,destination,rationale=DIRECTED[n]
        elif n in ROUTINE or n in DISPLAY:
            disposition,destination="editorial exclusion","Private normalized transcript"
            rationale="Display troubleshooting only." if n in DISPLAY else "Routine request to continue the established sequence."
        elif n in PREAMBLES:
            disposition,destination="preamble held locally",f"Private transcript; full teaching reply in record {PREAMBLES[n]}"
            rationale="Assistant progress announcement or roadmap already followed by the full teaching reply."
        elif branch=="hidden":
            disposition,destination="hidden layer held locally","Private normalized transcript"
            rationale="Archive marks this as visually hidden internal content outside the selected reading path."
        else:
            raise AssertionError(f"Record {n} has no disposition")
        assert destination and rationale
        rows.append([n,entry["role"],branch,"included in ancestry" if n in ancestry else "outside ancestry",
                     source_range,disposition,destination,rationale,"checked"])
    with (AUDIT/"source-coverage-manifest.csv").open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.writer(stream)
        writer.writerow(["stored_ordinal","message_role","branch_classification","reading_path_status","source_range",
                         "editorial_disposition","destination_chapter_or_archival_location",
                         "exclusion_justification","outstanding_verification_status"])
        writer.writerows(rows)
    return chapters


def get_ast(kind, value):
    return json.loads(run_pandoc(["-f",kind,"-t","json"],value))["blocks"]


def without_components(source):
    plain=mask_spans(source,FENCE.finditer(source))
    parsed, unmatched=tags(plain)
    assert not unmatched
    roots=[(a,b) for a,b,tag,depth in parsed if depth==0 and tag!="icon"]
    for a,b in reversed(roots):
        source=source[:a]+("\n" * source[a:b].count("\n"))+source[b:]
    return INLINE_TAGS.sub("",BODY.sub("",source))


def formula_key(value):
    return re.sub(r"\s+","", value)


def sequence_positions(needles, haystack):
    offset=0
    missing=[]
    for item in needles:
        try:
            at=haystack.index(item,offset)
        except ValueError:
            missing.append(item)
        else:
            offset=at+1
    return missing


def prose_key(value):
    return "".join(c.casefold() for c in unicodedata.normalize("NFKC",value) if c.isalnum())


def prose(node, mode="text"):
    if isinstance(node,list):
        return "".join(prose(x,mode) for x in node)
    if not isinstance(node,dict):
        return ""
    tag,value=node["t"],node.get("c")
    if tag=="Math":
        return "﹝"+formula_key(value[1])+"﹞" if mode=="table" else ""
    if tag=="Str":
        return prose_key(value)
    if tag=="Code":
        return prose_key(value[-1])
    if tag in {"CodeBlock","RawBlock","RawInline"}:
        return ""
    return prose(value,mode)


def table_rows(block):
    t=block["c"]
    return t[3][1]+[row for body in t[4] for row in body[2]+body[3]]+t[5][1]


def split_tex_row(line):
    math_ranges=[m.span() for m in MATH_RE.finditer(line)]
    starts=[0]+[m.end() for m in re.finditer(r"(?<!\\)&",line)
                if not any(a<=m.start()<b for a,b in math_ranges)]
    ends=[pos-1 for pos in starts[1:]]+[len(line)]
    return [line[a:b].strip() for a,b in zip(starts,ends,strict=True)]


def latex_tables(tex):
    table_sizes=[]
    payload=[]
    for block in LONGTABLE.finditer(tex):
        cells=[]
        for line in block[0].splitlines():
            if line.endswith(r"\\") and not line.lstrip().startswith(("\\caption","\\multicolumn")):
                cells.append(split_tex_row(line[:-2]))
        if not cells:
            continue
        for row in cells:
            for cell in row:
                # Prefix with a neutral key to preserve empty cells and trailing numbers
                # in the standalone LaTeX readback.
                payload.append("Celltoken "+cell)
        table_sizes.append(list(map(len,cells)))
    values=iter(prose(b,"table").removeprefix("celltoken") for b in get_ast("latex","\n\n".join(payload))
                if prose(b,"table").startswith("celltoken")) if payload else iter(())
    return [[tuple(next(values) for _ in range(size)) for size in sizes] for sizes in table_sizes]


def subsequence_text(needles, full):
    cursor=0
    misses=[]
    for needle in needles:
        index=full.find(needle,cursor)
        if index<0:
            misses.append(needle)
        else:
            cursor=index+len(needle)
    return misses


def chapter_checks(chapters):
    evidence=[]
    base_commit="18cabb5196b804904b551fc79d4bfb060dc6bbeb"
    for ordinal, spans in sorted(chapters.items()):
        for first,last,path,source in spans:
            tex=(BOOK/path).read_text(encoding="utf-8")
            baseline=subprocess.check_output(
                ["git","show",base_commit+":book/"+path],cwd=ROOT).decode("utf-8").replace("\r\n","\n")
            assert amend(Path(path).stem,baseline)==tex, f"Unreviewed manuscript change: {path}"
            baseline_math=[formula_key(m[2]) for m in MATH_RE.finditer(mask_spans(baseline,LATEX_CODE.finditer(baseline)))]
            code=[match[2].strip("\n") for match in FENCE.finditer(source) if match[1].strip()!="mermaid"]
            target_code=[m[1].strip("\n") for m in LATEX_CODE.finditer(tex)]
            missing_code=sequence_positions(code,target_code)
            plain=without_components(source)
            for old in EDITORIAL_PROSE.get(ordinal,set()):
                plain=plain.replace(old,"",1)
            if ordinal==10:
                plain=plain.replace("保留核心定义、数学结论、成立条件及研究意义，具体证明直接索引回前面的章节。","",1)
                plain=plain.replace("\n\n**Conclusion & Concept Index**。\n\n","\n\n",1)
            wanted=[formula_key(m[2]) for m in MATH_RE.finditer(mask_spans(plain,FENCE.finditer(plain)))]
            found=[formula_key(m[2]) for m in MATH_RE.finditer(mask_spans(tex,LATEX_CODE.finditer(tex)))]
            assert not sequence_positions(baseline_math,found), f"Baseline formula changed: {path}"
            missing_math=sequence_positions(wanted,found)

            # Switch displays out of the Pandoc Markdown prose/table input. Their
            # complete text is checked separately above.
            clean=MATH_RE.sub(lambda m: "\n\n§§DISPLAY§§\n\n" if m[1]=="[" else m[0],plain)
            src=get_ast("markdown-smart-raw_html-raw_tex",pandoc_math(clean))
            source_tables=[[tuple(prose(cell[-1],"table") for cell in cells) for _,cells in table_rows(t)]
                           for t in src if t["t"]=="Table"]
            rendered_tables=latex_tables(tex)
            # LaTeX may repeat headers for continuations. Treat a source table
            # as an ordered set of rows within exactly one destination table.
            ti=0
            table_misses=[]
            for tab in source_tables:
                for j in range(ti,len(rendered_tables)):
                    if not sequence_positions(tab,rendered_tables[j]):
                        ti=j+1
                        break
                else:
                    table_misses.append(tab)

            visible=tex
            visible=LONGTABLE.sub("",visible)
            visible=re.sub(r"(?m)^\\bookgraphic.*$","",visible)
            visible=re.sub(r"(?m)^\\(?:begin|end)\{(?:readerfigure|readertable|samepage)\}.*$","",visible)
            visible=LATEX_CODE.sub("",visible)
            in_tex=prose(get_ast("latex",visible))
            paragraphs=[key for block in src
                        if block["t"] in {"Para","Plain","BlockQuote","BulletList","OrderedList"}
                        and (key:=prose(block)) and key!="display"]
            misses=subsequence_text(paragraphs,in_tex)
            evidence.append({"chapter":path,"record":ordinal,"math":len(wanted),"code_blocks":len(code),
                             "tables":len(source_tables),"table_cells":sum(len(r) for t in source_tables for r in t),
                             "additional_release_formulae":len(found)-len(baseline_math),
                             "prose_blocks":len(paragraphs),"unmatched_math":len(missing_math),
                             "unmatched_code":len(missing_code),"unmatched_tables":len(table_misses),
                             "unmatched_prose":len(misses)})
            if missing_math or missing_code or table_misses or misses:
                print(path,"math",len(missing_math),"code",len(missing_code),"table",len(table_misses),"prose",len(misses),flush=True)
                # Diagnostics are kept in the ignored build tree because source
                # paragraphs can contain details not approved for public release.
                (BOOK/"build"/(Path(path).stem+"-reconciliation.json")).write_text(
                    json.dumps({"math":missing_math,"code":missing_code,"tables":table_misses,"prose":misses},ensure_ascii=False,indent=2),encoding="utf-8")
    (AUDIT/"release-fidelity-checks.json").write_text(json.dumps({"archive_sha256":EXPECTED_ARCHIVE,
                                                               "chapters":evidence},indent=2)+"\n",encoding="utf-8")
    print({key:sum(row[key] for row in evidence) for key in evidence[0] if key not in {"chapter","record"}})
    assert not any(any(row[key] for key in ("unmatched_math","unmatched_code","unmatched_tables","unmatched_prose")) for row in evidence)


if __name__=="__main__":
    chapter_checks(chapter_scope(*archive()))
