lint:
	-flake8 --max-line-length=120 *.py

test:
	-python -m unittest test_swa

.PHONY: test lint
