"""Build paper/manuscript.docx from paper/manuscript.md (needs pandoc).
Adds figures, declarations and an alphabetical list of the cited references.
Usage: python scripts/build_docx.py
"""
import pathlib, re, subprocess
P = pathlib.Path("paper")
s = (P / "manuscript.md").read_text()
r = (P / "references.md").read_text()
s = re.sub(r"> DRAFT.*?\n\n", "", s, flags=re.S)
s = s.replace("**Figure 1.** Share of seeded bugs detected by the short and full suites, by category\n(`figures/fig_validation.png`).",
              "![Figure 1. Share of seeded bugs detected by the short and full suites, by category.](../figures/fig_validation.png){width=5.5in}")
s = s.replace("**Figures 2-4.** pass@1 by model and condition; over-confidence gap; reliability diagram\n(`figures/fig_pass_at_1.png`, `fig_calibration.png`, `fig_reliability.png`).",
              "![Figure 2. pass@1 by model and condition (95% bootstrap CI; all 40 instances).](../figures/fig_pass_at_1.png){width=5.5in}\n\n"
              "![Figure 3. Over-confidence gap (mean confidence minus accuracy).](../figures/fig_calibration.png){width=5.5in}\n\n"
              "![Figure 4. Reliability diagram by condition, pooled over models.](../figures/fig_reliability.png){width=3.5in}")
d = pathlib.Path("DECLARATIONS.md").read_text().split("\n", 2)[2]
s = s[:s.index("## Statements and Declarations")] + "## Statements and Declarations\n" + d.replace("## ", "### ")
refs = [re.sub(r"^\d+\. ", "", l) for l in r.splitlines() if re.match(r"\d+\. ", l) and "(not cited)" not in l]
s += "\n## References\n\n" + "\n\n".join(sorted(refs, key=str.lower)) + "\n"
(P / "_b.md").write_text(s)
subprocess.run(["pandoc", "_b.md", "-o", "manuscript.docx"], check=True, cwd=P)
(P / "_b.md").unlink()
print("built paper/manuscript.docx")
