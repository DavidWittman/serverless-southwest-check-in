deploy: clean install_deps
	terraform apply

lint:
	flake8 --max-line-length=120 lambda/*.py

test:
	PYTHONPATH=lambda/tests:lambda python -m unittest test_swa test_handler

install_deps:
	pip install -r lambda/requirements.txt -t lambda/vendor

clean:
	-rm -rf lambda/vendor/
	-find . -type f -name '*.pyc' -delete

.PHONY: deploy lint test install_deps clean
