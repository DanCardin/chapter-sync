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

.PHONY: docker-tag docker-build docker-watch docker-publish
docker-build:
	docker build \
	--target final \
	-t chapter-sync \
	.

docker-watch:
	docker run -it --rm -v $(PWD):/app chapter-sync

docker-tag:
	docker tag chapter-sync dancardin/chapter-sync:latest
	docker tag chapter-sync dancardin/chapter-sync:$(VERSION)

docker-publish: docker-build docker-tag
	docker push dancardin/chapter-sync:latest
	docker push dancardin/chapter-sync:$(VERSION)


.PHONY: run run-web init-css watch-css

run:
	chapter-sync watch

run-web:
	uvicorn chapter_sync.web.__main__:create_app --reload

init-css:
	npm install tailwindcss flowbite

watch-css:
	npx tailwindcss -i src/chapter_sync/web/static/styles.css -o src/chapter_sync/web/static/app.css --watch
