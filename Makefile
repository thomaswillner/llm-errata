PYTHON ?= python3

.DEFAULT_GOAL := check
.PHONY: check lint claim readiness test demo cli-demo links all help

help: ## Show the available targets
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-8s %s\n", $$1, $$2}'

check: lint claim readiness test demo ## Everything that must pass before a change is complete

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

readiness: ## Validate production-readiness evidence without upgrading the verdict
	$(PYTHON) scripts/check_readiness.py

test: ## Self-tests, including the negative cases each checker must reject
	$(PYTHON) -m unittest discover -s tests -t .

demo: ## Run the Phase 1 conformance demo (exits 2 on purpose)
	@$(PYTHON) -m prototype.demo; \
	status=$$?; \
	if [ $$status -ne 2 ]; then \
		echo "DEMO ERROR: expected exit 2 (repair incomplete, reported honestly),"; \
		echo "            got exit $$status. Exit 0 means the aggregate went green"; \
		echo "            with an opaque store in scope; anything else is a crash."; \
		exit 1; \
	fi

cli-demo: ## Drive a full lifecycle through the CLI in a scratch workspace
	@rm -rf .cli-demo && mkdir -p .cli-demo
	@set -e; cd .cli-demo; \
	 export PYTHONPATH=..; \
	 run() { $(PYTHON) -m prototype.cli --workspace ws "$$@"; }; \
	 run init >/dev/null; \
	 run export --root mem_01HX --artifact fact:diet --content "is vegetarian" >/dev/null; \
	 run export --root mem_02KP --artifact fact:venue --content "prefers quiet restaurants" >/dev/null; \
	 run derive --artifact summary:dining --inputs fact:diet fact:venue --content "is vegetarian; prefers quiet restaurants" >/dev/null; \
	 run publish --root mem_01HX --operation supersede --replacement "eats meat again" --negative vegetarian --positive "eats meat again" --preserve "quiet restaurants"; \
	 set +e; \
	 run repair; status=$$?; \
	 run audit; \
	 run verify; verified=$$?; \
	 set -e; \
	 if [ $$verified -ne 0 ]; then \
		echo "CLI DEMO ERROR: a receipt failed signature or schema verification"; \
		exit 1; \
	 fi; \
	 if [ $$status -ne 2 ]; then \
		echo "CLI DEMO ERROR: repair should exit 2 (repaired, not verified), got $$status"; \
		exit 1; \
	 fi
	@rm -rf .cli-demo
	@echo "cli-demo: repair exited 2 and every receipt verified, as required"

links: ## Liveness of every cited external URL (network required)
	$(PYTHON) scripts/check_links.py

all: check links ## check plus the network-dependent link liveness run
