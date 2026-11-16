import sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import matplotlib  # noqa: F401
    HAVE_MPL = True
except ImportError:
    HAVE_MPL = False

from explainbench import analyze, figures, make_explanations, run_experiment


@unittest.skipUnless(HAVE_MPL, "matplotlib not installed")
class FigureTests(unittest.TestCase):
    def test_validation_and_run_figures(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            out = d / "figs"
            figures.main(["--validation", str(ROOT / "outputs" / "validation"), "--out", str(out)])
            self.assertTrue((out / "fig_validation.png").stat().st_size > 1000)
            ex, run = str(d / "expl"), str(d / "run")
            make_explanations.main(["--tasks", str(ROOT / "tasks"), "--out", ex, "--mock"])
            run_experiment.main(["--tasks", str(ROOT / "tasks"), "--explanations", ex,
                                 "--mock", "--seeds", "2", "--out", run])
            analyze.main(["--run", run, "--allow-mock"])
            figures.main(["--run", run, "--out", str(out)])
            for name in ("fig_pass_at_1", "fig_calibration", "fig_reliability"):
                self.assertTrue((out / f"{name}.pdf").exists(), name)


if __name__ == "__main__":
    unittest.main()
