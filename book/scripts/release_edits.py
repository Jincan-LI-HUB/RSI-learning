"""Apply the narrowly scoped release changes to the accepted chapter sources."""
import math
from pathlib import Path
import sys

BOOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOOK.parent / "reader_prototype" / "scripts"))
STOP = "https://xychen5.github.io/papers/originals/2310.02304-self-taught-optimizer.pdf"
CONT = "https://doi.org/10.1080/713665670"
REVISIT = "https://doi.org/10.1080/14697688.2025.2530637"


def replace_once(text, old, new):
    if new in text:
        return text
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def citations(text, paragraphs):
    for ending, refs in paragraphs:
        links = "、".join(r"\href{" + url + "}{" + title + "}" for url, title in refs)
        text = replace_once(text, ending + "\n", ending + "（" + links + "）\n")
    return text


def amend(stem, text):
    if stem == "part-1-10-0001":
        old = r"\textbf{Conclusion \& Concept Index} 汇集核心定义、数学结论、成立条件及研究意义。具体证明见前文。"
        paragraph = (r"为减轻多段推导集中阅读时的信息负担，\textbf{Conclusion \& Concept Index} "
                     r"先汇集核心定义、数学结论、成立条件及研究意义。读者可按 Proof Index 回到相应段落查阅完整推导。")
        text = replace_once(text, old, paragraph)
    elif stem == "part-3-37-0001":
        text = citations(text, [
            ("STOP 原论文 Algorithm 1 正是采用了这一递归结构。", [(STOP + "#page=5", "STOP, Algorithm 1")]),
            ("作者也指出，即使是 GPT-4，单次独立运行中的改进也不一定单调。",
             [(STOP + "#page=5", "STOP, Figure 4 and §§5.1, 5.3")]),
        ])
    elif stem == "part-4-52-0001":
        refs = [(CONT, "Cont, 2001"), (REVISIT, "Revisiting Cont’s Stylized Facts, 2025")]
        text = citations(text, [
            ("在许多金融市场中，收益率方向和条件均值较难预测，而波动率具有更加明显的时间依赖结构。", refs),
            ("后续研究也强调，不同资产、市场和时间尺度未必同时满足全部特征。", refs),
        ])
    elif stem == "part-4-52-0680":
        text = citations(text, [("但真实金融收益率往往比正态分布产生更多极端观测值，这也是经典金融 Stylized Facts 之一。",
                                 [(CONT, "Cont, 2001")])])
    elif stem == "part-4-58-0007":
        old = r"\[\mathbb E[r_t^2]=1.\]"
        text = replace_once(text, old, old + "\n\n" +
                            r"结合 \(\mathbb E[r_t]=0\)，可得 \(\operatorname{Var}(r_t)=1\)。")
        old = "因此，较强的正向时间依赖可能显著降低有效样本信息量。负自相关则可能使针对样本均值定义的有效样本量超过原始样本量。"
        paragraph = (
            "这里的有效样本量是按样本均值的方差定义的。结合 II-B 中的泛化误差规模 "
            r"\(O\left(\sqrt{\frac{\log M}{n}}\right)\)，"
            "时间依赖性可能降低有效统计信息量，而大量候选搜索进一步增加选择风险。"
            r"不过，不能直接将 Hoeffding Bound 中的 \(n\) 替换为 \(n_{\mathrm{eff}}\)，"
            "并声称获得了严格的时间序列泛化界。后者需要额外的依赖结构假设及理论证明。"
        )
        text = replace_once(text, old, old + "\n\n" + paragraph)
    elif stem == "part-4-67-0001":
        old = "\n\n".join([
            r"\textbf{Negative Skewness}", "左尾较长", r"\textbf{Symmetric}", "左右对称",
            r"\textbf{Positive Skewness}", "右尾较长",
        ])
        figure = (
            r"\bookgraphic{.88}{iv-d-skewness-editorial}{编者重建示意。"
            r"左：标准化的反射 Gamma(4,1)，左尾较长。中：标准正态分布，左右对称。"
            r"右：标准化的 Gamma(4,1)，右尾较长。"
            r"三者均值均为 \(0\)、方差均为 \(1\)，偏度依次为 \(-1,0,+1\)。}"
        )
        text = replace_once(text, old, figure)
    return text


def render_skewness():
    # Gamma(4,1) has mean 4, standard deviation 2, and skewness 1.
    # Thus (G-4)/2 and its reflection have mean zero and unit variance.
    from visuals import export_svg
    from build_excerpt import PALETTE, path_data
    moments=[math.factorial(3+k)//math.factorial(3) for k in range(4)]
    mean=moments[1]
    variance=moments[2]-mean**2
    third=moments[3]-3*mean*moments[2]+2*mean**3
    assert (mean,variance,third)==(4,4,8)

    ink = "#" + PALETTE["ResearchSlate"]
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="528" height="145" viewBox="0 0 528 145">']

    def label(x, y, message, size=10, weight="normal"):
        elements.append(f'<text x="{x}" y="{y}" font-family="serif" font-size="{size}" '
                        f'font-weight="{weight}" text-anchor="middle" fill="{ink}">{message}</text>')

    def gamma_density(z):
        x = 2*z+4
        return 0 if x < 0 else x**3 * math.exp(-x)/3

    panels = [
        ("Negative Skewness", "−1", "ResearchSlate", lambda z: gamma_density(-z)),
        ("Symmetric", "0", "ResearchBlue", lambda z: math.exp(-z*z/2)/math.sqrt(2*math.pi)),
        ("Positive Skewness", "+1", "ResearchSage", gamma_density),
    ]
    for slot, (name, coefficient, shade, density) in enumerate(panels):
        left = 176*slot+13
        xp = lambda x: left+15*(x+5)
        yp = lambda y: 108-164*y
        label(left+75, 13, name, 12, "bold")
        label(left+75, 27, f"Skewness = {coefficient}")
        elements.append(f'<path d="M{left} 35V108H{left+150}" fill="none" stroke="{ink}" stroke-opacity=".65"/>')
        elements.append(f'<path d="M{xp(0)} 35V108" fill="none" stroke="{ink}" stroke-opacity=".27"/>')
        for x in (-4,-2,0,2,4):
            label(xp(x), 121, f"{x}".replace("-", "−"), 9)
        label(left+75, 138, "Standardized value")
        points = [(xp(-5+i/32), yp(density(-5+i/32))) for i in range(321)]
        elements.append(f'<path d="{path_data(points)}" fill="none" stroke="#{PALETTE[shade]}" stroke-width="2.35"/>')
    export_svg("iv-d-skewness-editorial", "".join(elements + ["</svg>"]))


def main():
    for stem in ("part-1-10-0001", "part-3-37-0001", "part-4-52-0001",
                 "part-4-52-0680", "part-4-58-0007", "part-4-67-0001"):
        file = BOOK / "chapters" / f"{stem}.tex"
        source = file.read_text(encoding="utf-8")
        adjusted = amend(stem, source)
        if adjusted != source:
            file.write_text(adjusted, encoding="utf-8", newline="\n")
    render_skewness()


if __name__ == "__main__":
    main()
