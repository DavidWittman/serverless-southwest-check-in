init:
	terraform init terraform/

plan: lambda/vendor
	terraform plan terraform/

apply: lambda/vendor
	terraform apply terraform/

deploy: clean apply

lint:
	flake8 --max-line-length=120 lambda/*.py

test:
	cd lambda/src; python -m unittest discover ../tests

lambda/vendor: lambda/requirements.txt
	pip install -r lambda/requirements.txt -t lambda/vendor/python

clean:
	-rm -rf lambda/vendor/
	-rm -rf terraform/build/
	-find . -type f -name '*.pyc' -delete

.PHONY: init plan apply deploy lint test clean
