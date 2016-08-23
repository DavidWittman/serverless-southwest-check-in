deploy: clean install_deps
	serverless deploy

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

.PHONY: deploy lint test install_deps deploy_lambda clean
