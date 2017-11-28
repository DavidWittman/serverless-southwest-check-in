init:
	terraform init terraform/

plan:
	terraform plan terraform/

apply:
	terraform apply terraform/

deploy: clean install_deps apply

lint:
	flake8 --max-line-length=120 lambda/*.py

test:
	cd lambda; python -m unittest discover tests

install_deps:
	pip install -r lambda/requirements.txt -t lambda/vendor

clean:
	-rm -rf lambda/vendor/
	-find . -type f -name '*.pyc' -delete

.PHONY: init plan apply deploy lint test install_deps clean
