# Diwanic Management

.PHONY: install lint format test run-api run-flow docker-up docker-down build-docker clean launch-ui

install:
	pip install -e ".[dev]"

lint:
	ruff check diwanic/ tests/

format:
	ruff format diwanic/ tests/

test:
	pytest -q

run-api:
	uvicorn diwanic.app.main:app --reload

run-flow:
	./venv/bin/python3 -c "from diwanic.pipelines.flows.full_pipeline_flow import full_pipeline_flow; full_pipeline_flow()"

docker-up:
	docker compose up --build

docker-down:
	docker compose down

build-docker:
	docker build -t diwanic .

clean:
	rm -rf __pycache__ **/__pycache__ .pytest_cache
	rm -rf *.egg-info
	rm -rf data/raw/* data/processed/* data/embeddings/*

launch-ui:
	./venv/bin/python diwanic/app/ui.py
