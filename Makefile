PROJECT_NAME := visitor-tracker
REGION ?= ap-northeast-2

.PHONY: help install domain deploy remove logs info test test-prod

help:
	@echo ""
	@echo "Usage:"
	@echo "  make install       Install Serverless Framework locally (npm)"
	@echo "  make domain        Create a custom domain for the service"
	@echo "  make deploy        Deploy the service to AWS"
	@echo "  make remove        Remove the deployed service"
	@echo "  make logs          Tail logs from the Lambda function"
	@echo "  make info          Show deployed service info"
	@echo "  make test          Run tests (if applicable)"
	@echo "  make test-prod     Run tests for the production service"
	@echo ""

install:
	npm install -g serverless
	npm install serverless-domain-manager --save-dev

domain:
	sls create_domain --region $(REGION)

deploy:
	sls deploy --region $(REGION)

remove:
	sls remove --region $(REGION)

logs:
	sls logs -f countVisitor --region $(REGION) --tail

info:
	sls info --region $(REGION)

test:
	uv run python -m unittest test_handler.py

test-prod:
	uv run python -m unittest test_post_deploy.py
