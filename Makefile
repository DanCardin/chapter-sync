.PHONY: install test lint format
.DEFAULT_GOAL := help

VERSION=$(shell python -c 'from importlib import metadata; print(metadata.version("chapter-sync"))')

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

.PHONY: docker-build docker-watch docker-publish
docker-build:
	docker build \
	--target final \
	-t chapter-sync \
	.

docker-watch:
	docker run -it --rm -v $(PWD):/app chapter-sync

docker-publish: docker-build
	docker tag chapter-sync dancardin/chapter-sync:latest
	docker tag chapter-sync dancardin/chapter-sync:$(VERSION)
	docker push dancardin/chapter-sync:latest
	docker push dancardin/chapter-sync:$(VERSION)
