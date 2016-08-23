lint:
	flake8 --max-line-length=120 *.py

test:
	python -m unittest test_swa

install_deps:
	mkdir -p vendor
	pip install -r requirements.txt -t vendor

clean:
	-rm -rf vendor/
	-find . -type f -name '*.pyc' -delete

.PHONY: test lint install_deps clean
