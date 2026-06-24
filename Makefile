# Diwanic Management

.PHONY: install lint format test run-api run-flow docker-up docker-down build-docker clean launch-ui setup qdrant-up qdrant-down

install:
	pip install -e ".[dev]"

lint:
	truff check diwanic/ tests/

format:
	truff format diwanic/ tests/

test:
	pytest tests/ --disable-warnings

run-api:
	./venv/bin/python run_api.py

qdrant-up:
	@if [ ! -f qdrant ]; then \
		echo "Downloading Qdrant..."; \
		curl -L -o qdrant.tar.gz https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz && \
		tar xzf qdrant.tar.gz && rm qdrant.tar.gz; \
	fi
	@mkdir -p storage
	@echo "Starting Qdrant on :6333..."
	@nohup ./qdrant > qdrant.log 2>&1 & echo "PID: $$!"
	@sleep 2 && curl -sf http://localhost:6333/healthz && echo "✅ Qdrant ready" || echo "⚠️  Qdrant may not be ready yet"

qdrant-down:
	@-pkill qdrant 2>/dev/null && echo "Qdrant stopped" || echo "Qdrant not running"

run-flow:
	@if [ -n "$(PREFECT_ACCOUNT_ID)" ] && [ -n "$(PREFECT_WORKSPACE_ID)" ]; then \
		PREFECT_API_URL=https://api.prefect.cloud/api/accounts/$(PREFECT_ACCOUNT_ID)/workspaces/$(PREFECT_WORKSPACE_ID) ./venv/bin/python3 -c "from diwanic.pipelines.flows.full_pipeline_flow import full_pipeline_flow; full_pipeline_flow()"; \
	else \
		./venv/bin/python3 -c "from diwanic.pipelines.flows.full_pipeline_flow import full_pipeline_flow; full_pipeline_flow()"; \
	fi

run-flow-skip:
	@if [ -n "$(PREFECT_ACCOUNT_ID)" ] && [ -n "$(PREFECT_WORKSPACE_ID)" ]; then \
		PREFECT_API_URL=https://api.prefect.cloud/api/accounts/$(PREFECT_ACCOUNT_ID)/workspaces/$(PREFECT_WORKSPACE_ID) ./venv/bin/python3 -c "from diwanic.pipelines.flows.full_pipeline_flow import full_pipeline_flow; full_pipeline_flow(skip_existing=True)"; \
	else \
		./venv/bin/python3 -c "from diwanic.pipelines.flows.full_pipeline_flow import full_pipeline_flow; full_pipeline_flow(skip_existing=True)"; \
	fi

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
	./venv/bin/python run.py

setup:
	./venv/bin/python setup_env.py
