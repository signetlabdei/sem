.PHONY: docs

docs:
	pipenv run $(MAKE) -C docs/ html;
