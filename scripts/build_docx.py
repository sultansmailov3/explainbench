"""Build paper/manuscript.docx from paper/manuscript.md (needs pandoc and python-docx).
Adds title block, figures, declarations and the alphabetical reference list, then styles the file.
Usage: python scripts/build_docx.py
"""
import pathlib, re, subprocess
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

P = pathlib.Path("paper")
BODY, HEAD = "Times New Roman", "Arial"
INK, ACCENT, RULE = RGBColor(0x1C, 0x23, 0x30), RGBColor(0x1F, 0x4E, 0x8C), "8A93A3"


def markdown():
    s = (P / "manuscript.md").read_text()
    r = (P / "references.md").read_text()
    s = re.sub(r"> DRAFT.*?\n\n", "", s, flags=re.S)
    s = re.sub(r"^# .*?\n\n.*?\n\n", "", s, count=1, flags=re.S)  # title + author line -> title block
    s = s.replace("## Abstract (to finalise, 200-250 words)", "## Abstract").replace("## Abstract\n", "## Abstract\n\n", 1)
    s = s.replace("**Figure 1.** Share of seeded bugs detected by the short and full suites, by category\n(`figures/fig_validation.png`).",
                  "![Fig. 1 Share of seeded bugs detected by the short and full suites, by category](../figures/fig_validation.png){width=5.2in}")
    s = s.replace("**Figures 2-4.** pass@1 by model and condition; over-confidence gap; reliability diagram\n(`figures/fig_pass_at_1.png`, `fig_calibration.png`, `fig_reliability.png`).",
                  "![Fig. 2 pass@1 by model and condition with 95% bootstrap intervals (all 40 instances)](../figures/fig_pass_at_1.png){width=5.2in}\n\n"
                  "![Fig. 3 Over-confidence gap: mean stated confidence minus accuracy](../figures/fig_calibration.png){width=5.2in}\n\n"
                  "![Fig. 4 Reliability diagram by condition, pooled over models](../figures/fig_reliability.png){width=3.4in}")
    s = re.sub(r" ?\(`[^`\n]*`(?:, `[^`\n]*`)*(?:; [^)\n]*)?\)", "", s)  # drop file-path asides from running text
    d = pathlib.Path("DECLARATIONS.md").read_text().split("\n", 2)[2]
    d = re.sub(r" \(TO CONFIRM by the author\.?\)", "", d)
    s = s[:s.index("## Statements and Declarations")] + "## Statements and Declarations\n" + d.replace("## ", "### ")
    refs = [re.sub(r"^\d+\. ", "", l) for l in r.splitlines() if re.match(r"\d+\. ", l)]
    s += "\n## References\n\n" + "\n\n".join(sorted(refs, key=str.lower)) + "\n"
    meta = ("---\ntitle: \"Explanation Context and Bug-Repair Calibration in Open-Weight Code LLMs on Novice Python Tasks\"\n"
            "author: \"Sultan Kalzhigit\"\ndate: \"Astana IT University, Astana, Kazakhstan\"\n---\n\n")
    return meta + s


def font(run_or_style, name, size=None, bold=None, italic=None, color=None):
    f = run_or_style.font
    f.name = name
    rpr = run_or_style.element.get_or_add_rPr() if hasattr(run_or_style.element, "get_or_add_rPr") else run_or_style._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), name)
    if size: f.size = Pt(size)
    if bold is not None: f.bold = bold
    if italic is not None: f.italic = italic
    if color is not None: f.color.rgb = color


def border(cell, **edges):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders"); tcPr.append(b)
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        sz = edges.get(edge, 0)
        el.set(qn("w:val"), "single" if sz else "nil"); el.set(qn("w:sz"), str(sz or 0)); el.set(qn("w:color"), RULE)
        old = b.find(qn(f"w:{edge}"))
        if old is not None: b.remove(old)
        b.append(el)


def style(path):
    doc = Document(path)
    for sec in doc.sections:
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(2.5); sec.top_margin = sec.bottom_margin = Cm(2.5)
        fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = fp.add_run()
        for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
            if tag:
                el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), tag)
            else:
                el = OxmlElement("w:instrText"); el.text = text
            run._r.append(el)
        font(run, BODY, 10, color=INK)
    S = {st.name: st for st in doc.styles}
    for name in ("Normal", "Body Text", "First Paragraph", "Compact"):
        if name in S:
            font(S[name], BODY, 11.5, color=INK)
            pf = S[name].paragraph_format
            pf.line_spacing = 1.25; pf.space_after = Pt(7); pf.space_before = Pt(0)
            if name != "Compact": pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name, size, color, before in (("Heading 1", 15, ACCENT, 18), ("Heading 2", 15, ACCENT, 18), ("Heading 3", 12, INK, 12)):
        font(S[name], HEAD, size, bold=True, italic=False, color=color)
        pf = S[name].paragraph_format; pf.space_before = Pt(before); pf.space_after = Pt(6); pf.keep_with_next = True
    font(S["Title"], HEAD, 20, bold=True, color=INK)
    S["Title"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT; S["Title"].paragraph_format.space_after = Pt(10)
    for name, size in (("Author", 12), ("Date", 11)):
        if name in S:
            font(S[name], BODY, size, color=INK); S[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            S[name].paragraph_format.space_after = Pt(2)
    for name in ("Image Caption", "Caption", "Table Caption"):
        if name in S:
            font(S[name], BODY, 10, italic=False, color=INK)
            S[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER; S[name].paragraph_format.space_after = Pt(12)
    if "Captioned Figure" in S:
        S["Captioned Figure"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        S["Captioned Figure"].paragraph_format.keep_with_next = True
    if "Block Text" in S: font(S["Block Text"], BODY, 10.5, color=INK)

    in_refs = False
    for p in doc.paragraphs:
        if p.style.name.startswith("Heading"):
            in_refs = p.text.strip() == "References"
            continue
        if in_refs and p.text.strip():
            pf = p.paragraph_format
            pf.left_indent = Cm(0.75); pf.first_line_indent = Cm(-0.75); pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.space_after = Pt(4); pf.line_spacing = 1.1
            for r in p.runs: r.font.size = Pt(10)
        if p.text.startswith("Table ") and p.runs and p.runs[0].bold:  # table titles
            p.paragraph_format.keep_with_next = True; p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(10)
            for r in p.runs: r.font.size = Pt(10.5)
        for r in p.runs:  # inline code -> body font
            if r.style is not None and r.style.name == "Verbatim Char":
                font(r, "Consolas", 10)
    for t in doc.tables:
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        n = len(t.rows)
        for i, row in enumerate(t.rows):
            for c in row.cells:
                border(c, top=12 if i == 0 else 0, bottom=6 if i == 0 else (12 if i == n - 1 else 0))
                for p in c.paragraphs:
                    p.paragraph_format.space_after = Pt(2); p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.line_spacing = 1.0; p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for r in p.runs:
                        font(r, BODY, 9.5, color=INK)
                        if i == 0: r.font.bold = True
    doc.save(path)


if __name__ == "__main__":
    (P / "_b.md").write_text(markdown())
    subprocess.run(["pandoc", "_b.md", "-o", "manuscript.docx", "--from", "markdown"], check=True, cwd=P)
    (P / "_b.md").unlink()
    style(P / "manuscript.docx")
    print("built paper/manuscript.docx")
