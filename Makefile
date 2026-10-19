# mdportal
PYTHON  ?= python3
CONFIG  ?= roots.test.yaml
PORT    ?= 5000
IMAGE   ?= mdportal

.PHONY: help models validate test run docker clean

help:
	@echo "targets:"
	@echo "  models    regenerate roots_models.py from roots.linkml.yaml"
	@echo "  validate  validate $(CONFIG) (Pydantic / LinkML)"
	@echo "  test      validate + boot app + HTTP smoke checks"
	@echo "  run       validate then Flask dev server on :$(PORT)"
	@echo "  docker    build image and run with ./data mounted at /data"
	@echo "  clean     remove __pycache__"

models:
	@sh regenerate_models.sh

validate:
	$(PYTHON) validate_roots.py $(CONFIG)

test: validate
	MDPORTAL_CONFIG=$(CONFIG) $(PYTHON) test_mdportal.py

run: validate
	MDPORTAL_CONFIG=$(abspath $(CONFIG)) \
	$(PYTHON) -c "from app import create_app; create_app().run(debug=True, port=$(PORT))"

docker:
	@sh run.sh

clean:
	rm -rf __pycache__ .pytest_cache
