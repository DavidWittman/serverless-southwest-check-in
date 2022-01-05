CHROMEDRIVER_VERSION := 2.41
SERVERLESS_CHROME_VERSION := v1.0.0-53

TF_BUILD_DIR := ./terraform/build

init:
	terraform init terraform/

plan: lambda/vendor $(TF_BUILD_DIR)/chromedriver.zip
	terraform plan terraform/

apply: lambda/vendor $(TF_BUILD_DIR)/chromedriver.zip
	terraform apply terraform/

deploy: clean apply

lint:
	flake8 --max-line-length=120 lambda/src

test:
	cd lambda/src; python -m unittest discover ../tests

lambda/vendor: lambda/requirements.txt
	sudo docker run --rm -v "$(shell pwd)":/var/task "public.ecr.aws/sam/build-python3.6" /bin/sh -c "pip install -U pip && pip install -r lambda/requirements.txt -t lambda/vendor/python/; exit"
	sudo chown -R $(shell id -u):$(shell id -g) lambda/vendor


$(TF_BUILD_DIR)/chromedriver.zip:
	@mkdir -p $(TF_BUILD_DIR)

	curl -SL https://chromedriver.storage.googleapis.com/$(CHROMEDRIVER_VERSION)/chromedriver_linux64.zip > $(TF_BUILD_DIR)/chromedriver.zip
	unzip $(TF_BUILD_DIR)/chromedriver.zip -d $(TF_BUILD_DIR)/
	perl -pi -e 's/cdc_/swa_/g' $(TF_BUILD_DIR)/chromedriver

	curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/$(SERVERLESS_CHROME_VERSION)/stable-headless-chromium-amazonlinux-2017-03.zip > $(TF_BUILD_DIR)/headless-chromium.zip
	unzip $(TF_BUILD_DIR)/headless-chromium.zip -d $(TF_BUILD_DIR)/

	@rm $(TF_BUILD_DIR)/headless-chromium.zip $(TF_BUILD_DIR)/chromedriver.zip
	cd $(TF_BUILD_DIR); zip -r chromedriver.zip chromedriver headless-chromium

clean:
	-rm -rf lambda/vendor/
	-rm -rf $(TF_BUILD_DIR)/
	-find . -type f -name '*.pyc' -delete

.PHONY: init plan apply deploy lint test clean
