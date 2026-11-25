"""Record release dispositions and generate a visual diff against the accepted PDF."""
import csv
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import subprocess

import pymupdf
from PIL import Image, ImageDraw

from release_fidelity import archive
from release_edits import CONT, REVISIT, STOP

BOOK = Path(__file__).resolve().parents[1]
AUDIT = BOOK / "audit"
BUILD = BOOK / "build"
BASELINE = "18cabb5196b804904b551fc79d4bfb060dc6bbeb"
BASELINE_PDF = "bcb2d6367a4168c4ee7cd7de8d10d6a58237fdc7feb08b0e6bf02f850df2d23a"

CITATIONS = [
    (31,860,860,"context pointer","No archived payload. Surrounding substantive prose is present.",""),
    (37,429,429,"academic","Algorithm 1 and §4 support the improver recursion. Primary author-hosted paper linked.",STOP+"#page=5"),
    (37,577,577,"academic","Figure 4 and §§5.1, 5.3 support the reported results and run variability. Primary paper linked.",STOP+"#page=5"),
    (40,1470,1470,"context pointer","No archived payload. The preceding transition remains in the text.",""),
    (52,384,384,"academic group","The DOI links recorded in the archive and the verified primary works support the stylized-facts description.",CONT+" | "+REVISIT),
    (52,650,650,"academic group","Cont's survey and its modern replication support the historical account and qualification.",CONT+" | "+REVISIT),
    (52,917,917,"academic group","Cont supports heavier empirical tails. No archived match for the second transient alias was found; no speculative second link was inserted.",CONT),
    (52,1248,1255,"academic in component","Original explicit DOI already links the identified Cont paper. Redundant transient marker closed.",CONT),
    (52,1248,1263,"academic in component","Original explicit DOI already links the identified replication. Redundant transient marker closed.",REVISIT),
]
# Meaningful blocks and adjacent connective lines account for every line in the
# two alternate replies. The active references are source, not PDF, coordinates.
ALTERNATES = [
    (54,1,13,"Completion acknowledgment and topic recap","52,58 | IV-A and IV-B preview","Excluded chat status and redundant topic list."),
    (54,14,24,"Progress/navigation component","52 | IV-A roadmap; 77 | Part IV knowledge map","Excluded progress state. All stage names are represented."),
    (54,25,33,"Law of Total Variance preview and optimal R² formula","52:1369–1405; 58:1263–1318; 60 | Proof of optimal prediction limit","Covered. Derivation is explicit in IV-B."),
    (56,1,22,"Client-display diagnosis, importance table, resumed opening","52,58 | IV-A; 58 | Conclusion Index and Proof Index","Excluded status, new chat heading and ad hoc star rankings. Topics and proof references are preserved."),
    (56,23,37,"IID normal product construction","52:723–798; 58:70–94","Covered with the same independence and marginal distribution assumptions."),
    (56,38,44,"Zero mean and unit variance of the return","58:86–94,135–139 | IV-A §6.3","Zero mean and unit second moment already shown. Recovered explicit unit-variance inference."),
    (56,45,58,"Adjacent linear covariance; factors written in a different order","52:723–798; 58:95–118","Covered, including expectations factorized by independence."),
    (56,59,98,"Gaussian moments, squared-return covariance, paired conclusion, explanatory prose","58:119–201","Covered. The active proof retains the fuller factorization and correlation calculation."),
    (56,99,138,"ARCH/GARCH definitions, innovation and parameter table","52:799–847; 58:205–269","Covered. Expanded GARCH name also appears in the active literature index."),
    (56,139,160,"Finite stationary GARCH mean-variance equation and its solution","52:799–910; 58:273–330","Covered. Active derivation explicitly uses finite second moments and iterated expectation."),
    (56,161,170,"Three-series GARCH shock-persistence chart","58:332–376 | Shared-axes GARCH figure","Covered. All 27 archived values were checked against the retained three curves at h=0,5,…,40."),
    (56,171,182,"Time-dependent conditional variance compatible with constant unconditional variance","52:899–910; 58:378–398","Covered with weak-stationarity context and unchanged distinction."),
    (56,183,204,"Normal versus standardized t₃ densities and interpretation","52:911–955; 58:404–461","Covered. Both use the same density expressions and interpretation; the active plots also provide tail probabilities."),
    (56,205,237,"Absolute moments and degrees-of-freedom table","52:956–981; 58:465–539","Covered. Active edition includes the integral convergence argument."),
    (56,238,250,"Finite variance of returns versus the fourth moment needed for squared returns; research implication","52:982–990; 58:543–587","Covered. Active example gives the same moment identity for squared loss and connects noise to evaluation."),
    (56,251,294,"Finite-sample variance, definition of ESS, and scope limited to the mean","52:992–1038; 58:595–699","Covered, including finite-lag weighting. The scope is reiterated with the recovered qualification below."),
    (56,295,321,"Stationary AR(1), infinite-sum calculation, large-n approximation","52:1039–1066; 58:701–740","Covered with the |φ|<1 and large-n conditions."),
    (56,322,360,"ESS widget, standard-error multiplier, and interpretation near 112 independent observations","52:1067–1120; 58:741–804","Covered. Uses the same finite-sample formula and input defaults. The manuscript prints the finite-n result and multiplier."),
    (56,361,374,"ESS and selection-risk connection; no automatic Hoeffding extension","58 | IV-A §8.3 after ESS example; II-B","Recovered the connection and the explicit warning against substituting ESS into an IID bound without assumptions and proof."),
    (56,375,386,"Overfitting risk table and interrupted final row","52:1124–1180; 58:921–979","Complete active comparison covers the visible rows and identifies the single-historical-path issue."),
]


def write_csv(name, fields, rows):
    with (AUDIT/name).open("w",encoding="utf-8-sig",newline="") as output:
        writer=csv.writer(output)
        writer.writerow(fields)
        writer.writerows(rows)


def reconciliation_records():
    raw, _, _ = archive()
    for n in (54,56):
        covered=[i for ordinal,start,end,*_ in ALTERNATES if ordinal==n for i in range(start,end+1)]
        assert covered==list(range(1,len(raw[n-1]["content"][0]["text"].splitlines())+1))
    assert len(CITATIONS)==9
    keys=set()
    for n,reported,physical,kind,*_ in CITATIONS:
        assert (n,physical) not in keys
        keys.add((n,physical))
        record=raw[n-1]
        line=record["content"][0]["text"].splitlines()[physical-1]
        if kind=="context pointer":
            assert "<MemoryCite" in line and not record["metadata"].get("citations")
        else:
            assert "<Cite" in line
    chart=next(line.strip() for line in raw[55]["content"][0]["text"].splitlines()
               if "<Chart content=" in line)
    values=json.loads(chart.removeprefix("<Chart content={").removesuffix("}/>"))
    for row in values["data"]:
        for key,prob in zip(("a","b","c"),(.5,.9,.99),strict=True):
            assert abs(row[key]-(1+3*prob**row["h"])) < 5.01e-6
    write_csv("alternative-differences.csv",
              ["stored_ordinal","first_line","last_line","block","active_destination","disposition"],ALTERNATES)
    write_csv("citation-reconciliation.csv",
              ["stored_ordinal","inventory_line","physical_line","classification","disposition","verified_target"],CITATIONS)

    figures=[]
    for path in sorted(AUDIT.glob("part-*.json")):
        chapter=json.loads(path.read_text(encoding="utf-8"))
        for entry in chapter["components"]:
            n,line,kind=entry["message"],entry.get("line",""),entry["component"]
            base=chapter["chapter"]["chapter"]
            if entry["graphics"]:
                disposition="partially recovered" if entry.get("print_states") or (n==58 and line==342) else "recovered"
                note="Static print states preserve selected behavior." if disposition.startswith("partially") else "Source vector, data, or component geometry appears in print."
                figures.append([n,line,kind,disposition,entry["graphics"],f"chapters/{base}.tex",note])
            for gap in entry.get("gaps",[]):
                if gap["type"]=="missing-image":
                    figures.append([n,line,"original image","unavailable",0,f"chapters/{base}.tex",
                                    "Archived query only. "+gap["detail"]])
    figures.extend([
        [67,980,"editorial illustration","reconstructed",1,"figures/iv-d-skewness-editorial.svg",
         "Analytic Gamma/Normal comparison; independent of the three unavailable originals."],
        [52,1199,"market data audit","partially recovered",0,"chapters/part-4-52-0680.tex",
         "Plotting code preserved; input data and original empirical figures unavailable."],
        [58,1002,"market data audit","partially recovered",0,"chapters/part-4-58-0007.tex",
         "Plotting code preserved; input data and original empirical figures unavailable."],
    ])
    write_csv("figure-manifest.csv",["stored_ordinal","source_line","component","status",
                                    "print_vector_placements","destination","disposition"],figures)
    return figures


def visual_comparison():
    source=subprocess.check_output(["git","show",BASELINE+":book/Mathematical_Exploration_Personal_Edition.pdf"],cwd=BOOK.parent)
    assert hashlib.sha256(source).hexdigest()==BASELINE_PDF
    with pymupdf.open("pdf",source) as base, pymupdf.open(BUILD/"main.pdf") as candidate:
        def fingerprints(pdf):
            # Exclude only the running page number, whose value can shift
            # after a page insertion even if the page interior is identical.
            return [hashlib.sha256(page.get_pixmap(matrix=pymupdf.Matrix(.40,.40),
                        clip=pymupdf.Rect(0,0,page.rect.width,790),alpha=False).samples).digest() for page in pdf]
        spans=SequenceMatcher(a=fingerprints(base),b=fingerprints(candidate),autojunk=False).get_opcodes()
        changed={i+1 for action,_,_,lo,hi in spans if action!="equal" for i in range(lo,hi)}
        assert changed
        scope=sorted({j for i in changed for j in (i-1,i,i+1) if 0<j<=len(candidate)})
        first_part=next(page for _,title,page in candidate.get_toc() if title.startswith("I Understanding"))
        scope=sorted(set(scope)|set(range(1,first_part+1)))
        directory=BUILD/"release-qa"
        directory.mkdir(exist_ok=True)
        for start in range(0,len(scope),20):
            group=scope[start:start+20]
            sheet=Image.new("RGB",(1260,355*((len(group)+4)//5)),"#e8ebec")
            draw=ImageDraw.Draw(sheet)
            for i,number in enumerate(group):
                pix=candidate[number-1].get_pixmap(matrix=pymupdf.Matrix(.4,.4),alpha=False)
                thumbnail=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
                x,y=6+(i%5)*252,17+(i//5)*355
                sheet.paste(thumbnail,(x,y))
                draw.text((x,y-14),f"{number}{' *' if number in changed else ''}",fill="#253037")
            sheet.save(directory/f"sheet-{1+start//20:02d}.png")
        anchors=("编者说明", "Negative Skewness", "不能直接将 Hoeffding Bound", "信息负担")
        for number in scope:
            page=candidate[number-1]
            text="".join(page.get_text().split())
            if any("".join(a.split()) in text for a in anchors):
                page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(directory/f"page-{number:03d}.png")
        output={"baseline_pdf_sha256":BASELINE_PDF,"baseline_pages":len(base),"candidate_pages":len(candidate),
                "changed_page_interiors":sorted(changed),"pages_rendered_for_review":scope}
        (AUDIT/"release-visual-checks.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
        print(f"Release {len(candidate)} pages; {len(changed)} changed interiors, {len(scope)} rendered for review.")


if __name__=="__main__":
    reconciliation_records()
    visual_comparison()
