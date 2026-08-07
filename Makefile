PYTHON ?= python3

.DEFAULT_GOAL := check
.PHONY: check lint claim test links all help

help: ## Show the available targets
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-8s %s\n", $$1, $$2}'

check: lint claim test ## Everything that must pass before a change is complete

lint: ## Structure, encoding, Markdown, links, licence, release metadata
	$(PYTHON) scripts/validate_repo.py

# make exits 2 for any failed recipe, which would collide with the guard's own
# exit 2 for "inconclusive". The exit code is echoed so the two stay
# distinguishable from the terminal, and a wrapper that needs to branch on it
# should call scripts/claim_guard.py directly.
claim: ## Anchored guard on the bounded novelty claim and its invariants
	@$(PYTHON) scripts/claim_guard.py; \
	status=$$?; \
	if [ $$status -eq 2 ]; then \
		echo "claim_guard.py exit 2: INCONCLUSIVE. This is not a pass."; \
	elif [ $$status -ne 0 ]; then \
		echo "claim_guard.py exit $$status: FAILED."; \
	fi; \
	exit $$status

test: ## Self-tests, including the negative cases each checker must reject
	$(PYTHON) -m unittest discover -s tests -t tests

links: ## Liveness of every cited external URL (network required)
	$(PYTHON) scripts/check_links.py

all: check links ## check plus the network-dependent link liveness run
