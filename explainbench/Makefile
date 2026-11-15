export PYTHONPATH := src

test:
	python -m unittest discover -s tests -v

validate:
	python -m explainbench.validate --generated

mock:        # plumbing test only, NEVER research data
	python -m explainbench.make_explanations --mock --out outputs/mock/explanations
	python -m explainbench.run_experiment --mock --explanations outputs/mock/explanations --seeds 2
	python -m explainbench.analyze --run outputs/mock --allow-mock
