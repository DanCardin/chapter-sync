.PHONY: install test lint format
.DEFAULT_GOAL := help

WORKER_COUNT ?= 4

install:
	poetry install

test:
	coverage run -m pytest -vv src tests
	coverage report -i
	coverage xml

lint:
	ruff --fix src tests || exit 1
	ruff format -q src tests || exit 1
	mypy src tests || exit 1
	ruff format --check src tests

format:
	ruff src tests --fix
	ruff format src tests

.PHONY: docker-build docker-watch
docker-build:
	docker build \
	--target final \
	-t chapter-sync \
	.

docker-watch:
	docker run -it --rm -v $(PWD):/app chapter-sync
