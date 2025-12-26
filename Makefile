IMAGE ?= agentic-changescribe:latest

.PHONY: build
build:
	docker build -t $(IMAGE) .

.PHONY: run
run:
	# Usage: make run REPO=/path/to/repo TITLE="..." SUMMARY="..."
	@if [ -z "$(REPO)" ]; then echo "Set REPO=/path/to/git-repo"; exit 1; fi
	docker run --rm \
		-e LLM_BASE_URL \
		-e LLM_API_KEY \
		-e LLM_MODEL \
		-v "$(REPO)":/repo \
		-v "$(REPO)/docs/change-packs":/out \
		-w /repo \
		$(IMAGE) generate --repo /repo --diff auto --outdir /out --title "$(TITLE)" --summary "$(SUMMARY)"
