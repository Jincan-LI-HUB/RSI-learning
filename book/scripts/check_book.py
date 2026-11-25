"""Verify content and navigation, then render pages for the editorial review."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw
import pymupdf

BOOK=Path(__file__).resolve().parents[1]


def audit(pdf):
    logs=(BOOK/"build/main.log").read_text(encoding="utf-8",errors="replace")
    diagnostics=[line for line in logs.splitlines() if re.search(
        r"^!|Missing character|Overfull|multiply defined|undefined references|undefined citations",line)]
    conversion=[json.loads(path.read_text(encoding="utf-8")) for path in sorted((BOOK/"audit").glob("part-*.json"))]
    assert all(c["chapter"]["source_math"]==c["chapter"]["matched_math"] for c in conversion)
    assets=[a for c in conversion for a in c["components"]]
    assert not [a for a in assets if a["state"]=="fallback"]
    result={
        "pdf_sha256":hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "part_checks":[{"part":part,
                        "source_math":sum(c["chapter"]["source_math"] for c in conversion if c["chapter"]["part"]==part),
                        "matched_math":sum(c["chapter"]["matched_math"] for c in conversion if c["chapter"]["part"]==part),
                        "tables":sum(c["chapter"]["tables"] for c in conversion if c["chapter"]["part"]==part)}
                       for part in range(1,5)],
        "math_payloads":sum(c["chapter"]["matched_math"] for c in conversion),
        "tables":sum(c["chapter"]["tables"] for c in conversion),
        "vectors":sum(a["graphics"] for a in assets),
        "interactive_components_with_multiple_print_states":sum(a.get("print_states",0)>1 for a in assets)+1,
        "missing_assets":[{"record":a["message"],"line":a.get("line"),**g}
                          for a in assets for g in a.get("gaps",[])],
        "unresolved_citation_or_context_markers":sum(a.get("unresolved_citations",0) for a in assets),
        "diagnostics":diagnostics,
    }
    release_citations=BOOK/"audit/citation-reconciliation.csv"
    if release_citations.exists():
        with release_citations.open(encoding="utf-8-sig",newline="") as stream:
            citations=list(csv.DictReader(stream))
        with (BOOK/"audit/figure-manifest.csv").open(encoding="utf-8-sig",newline="") as stream:
            figure_rows=list(csv.DictReader(stream))
        result["vectors"]=sum(int(row["print_vector_placements"]) for row in figure_rows)
        result["original_academic_markers_reconciled"]=sum(bool(row["verified_target"]) for row in citations)
        result["context_pointers_without_archived_targets"]=sum(row["classification"]=="context pointer" for row in citations)
        result.pop("unresolved_citation_or_context_markers")
        fidelity=json.loads((BOOK/"audit/release-fidelity-checks.json").read_text(encoding="utf-8"))
        result["additional_source_and_editorial_math_payloads"]=sum(
            chapter["additional_release_formulae"] for chapter in fidelity["chapters"])
    directory=BOOK/"build/qa"
    directory.mkdir(parents=True,exist_ok=True)
    with pymupdf.open(pdf) as document:
        toc=document.get_toc()
        assert len([entry for entry in toc if entry[0]==1 and re.match(r"^(?:I|II|III|IV) ",entry[1])])==4
        opening={page for level,_,page in toc if level<=2}
        raster=[]
        sparse=[]
        vector_pages=[]
        bounds=[]
        links=0
        for page in document:
            number=page.number+1
            text=page.get_text()
            assert text.strip(), number
            text_boxes=[p[:4] for p in page.get_text("blocks") if p[6]==0]
            if any(not page.rect.contains(pymupdf.Rect(rect)) for rect in text_boxes):
                bounds.append(number)
            if page.get_image_info():
                raster.append(number)
            if page.get_xobjects():
                vector_pages.append(number)
            if len(text)<320 and number>1 and number not in vector_pages:
                sparse.append(number)
            for link in page.get_links():
                if link["kind"] in {pymupdf.LINK_GOTO,pymupdf.LINK_NAMED}:
                    assert link["page"] in range(len(document)), (number,link)
                    links+=1
                assert link["kind"] != pymupdf.LINK_LAUNCH, (number,link)
        picks=sorted({1,2,len(document),*opening,*vector_pages,*sparse})
        result.update(page_count=len(document),bookmarks=len(toc),internal_links=links,
                      figure_pages=len(vector_pages),pages_reviewed_by_render=picks,
                      sparse_text_pages=sparse,raster_pages=raster,text_outside_page=bounds)
        for start in range(0,len(picks),20):
            subset=picks[start:start+20]
            sheet=Image.new("RGB",(1200,352*((len(subset)+4)//5)),"#e8ebec")
            draw=ImageDraw.Draw(sheet)
            for i,number in enumerate(subset):
                pix=document[number-1].get_pixmap(matrix=pymupdf.Matrix(.39,.39),alpha=False)
                thumbnail=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
                x=5+(i%5)*240
                y=17+(i//5)*352
                sheet.paste(thumbnail,(x,y))
                draw.text((x,y-14),str(number),fill="#253037")
            sheet.save(directory/f"sheet-{start//20+1:02d}.png")
        for page in sorted({*opening,*sparse,1,2,len(document)}):
            document[page-1].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2),alpha=False).save(
                directory/f"page-{page:03d}.png")
    (directory/"verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                                               encoding="utf-8")
    print({k:v for k,v in result.items() if k!="pages_reviewed_by_render"})
    assert links>0 and not diagnostics and not bounds and not raster


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("pdf",type=Path,nargs="?",default=BOOK/"build/main.pdf")
    audit(parser.parse_args().pdf)
