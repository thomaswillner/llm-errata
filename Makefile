PYTHON ?= python3

.DEFAULT_GOAL := check
.PHONY: check lint claim test links all help

help: ## Show the available targets
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-8s %s\n", $$1, $$2}'

check: lint claim test ## Everything that must pass before a change is complete

lint: ## Structure, encoding, Markdown, links, licence, release metadata
	$(PYTHON) scripts/validate_repo.py

claim: ## Anchored guard on the bounded novelty claim and its invariants
	$(PYTHON) scripts/claim_guard.py

test: ## Self-tests, including the negative cases each checker must reject
	$(PYTHON) -m unittest discover -s tests -t tests

links: ## Liveness of every cited external URL (network required)
	$(PYTHON) scripts/check_links.py

all: check links ## check plus the network-dependent link liveness run
