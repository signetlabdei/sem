.PHONY: docs

docs:
	poetry run $(MAKE) -C docs/ html;
