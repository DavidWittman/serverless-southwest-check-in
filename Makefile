deploy: clean install_deps
	serverless deploy

lint:
	flake8 --max-line-length=120 *.py

test:
	PYTHONPATH=tests/ python -m unittest test_swa

install_deps:
	pip install -r requirements.txt -t vendor

clean:
	-rm -rf vendor/
	-find . -type f -name '*.pyc' -delete

.PHONY: deploy lint test install_deps clean
