PYTHON ?= python3
.PHONY: check tests models publication hygiene

check: tests models publication hygiene

tests:
	$(PYTHON) -m unittest discover -s tests -v

models:
	$(PYTHON) scripts/check_models.py

publication:
	$(PYTHON) scripts/check_publication.py

hygiene:
	$(PYTHON) scripts/check_hygiene.py
