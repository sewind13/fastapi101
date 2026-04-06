COMPOSE_BASE=docker compose -f docker-compose.yml
COMPOSE_DEV=docker compose -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_MONITORING=docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.monitoring.yml
COMPOSE_LOADTEST=docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.monitoring.yml -f docker-compose.loadtest.yml
COMPOSE_WORKER_DEV=docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile worker
COMPOSE_WORKER_PROD=docker compose -f docker-compose.yml --profile worker
COMPOSE_REDIS_DEV=docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile redis
COMPOSE_REDIS_PROD=docker compose -f docker-compose.yml --profile redis
COMPOSE_LOADTEST_WORKER=docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.monitoring.yml -f docker-compose.loadtest.yml --profile worker

up:
	$(COMPOSE_DEV) up --build

up-prod:
	$(COMPOSE_BASE) up --build

down:
	$(COMPOSE_DEV) down

up-worker:
	$(COMPOSE_WORKER_DEV) up --build

up-worker-prod:
	$(COMPOSE_WORKER_PROD) up --build

up-redis:
	$(COMPOSE_REDIS_DEV) up --build

up-redis-prod:
	$(COMPOSE_REDIS_PROD) up --build

up-monitoring:
	$(COMPOSE_MONITORING) up --build

down-monitoring:
	$(COMPOSE_MONITORING) down

up-loadtest:
	$(COMPOSE_MONITORING) up --build -d

up-loadtest-worker:
	$(COMPOSE_LOADTEST_WORKER) up --build -d

down-loadtest:
	$(COMPOSE_MONITORING) down

down-loadtest-worker:
	$(COMPOSE_LOADTEST_WORKER) down

down-worker:
	$(COMPOSE_WORKER_DEV) down

down-worker-prod:
	$(COMPOSE_WORKER_PROD) down

down-redis:
	$(COMPOSE_REDIS_DEV) down

down-prod:
	$(COMPOSE_BASE) down

logs:
	$(COMPOSE_DEV) logs -f web

logs-prod:
	$(COMPOSE_BASE) logs -f web

logs-worker:
	$(COMPOSE_WORKER_DEV) logs -f worker

logs-worker-prod:
	$(COMPOSE_WORKER_PROD) logs -f worker

logs-redis:
	$(COMPOSE_REDIS_DEV) logs -f redis

logs-outbox:
	$(COMPOSE_WORKER_DEV) logs -f outbox-dispatcher

logs-outbox-prod:
	$(COMPOSE_WORKER_PROD) logs -f outbox-dispatcher

ps:
	$(COMPOSE_DEV) ps

ps-prod:
	$(COMPOSE_BASE) ps

ps-worker:
	$(COMPOSE_WORKER_DEV) ps

ps-worker-prod:
	$(COMPOSE_WORKER_PROD) ps

ps-redis:
	$(COMPOSE_REDIS_DEV) ps

migrate:
	$(COMPOSE_DEV) exec web uv run alembic upgrade head

migration:
	$(COMPOSE_DEV) exec web uv run alembic revision --autogenerate -m "$(m)"

psql:
	$(COMPOSE_DEV) exec db psql -U app -d app

cleanup-revoked-tokens:
	$(COMPOSE_DEV) exec web python -m app.jobs.cleanup_revoked_tokens

replay-dlq:
	$(COMPOSE_WORKER_DEV) exec worker python -m app.jobs.replay_dead_letter_queue

report-outbox:
	$(COMPOSE_WORKER_DEV) exec outbox-dispatcher python -m app.jobs.report_outbox

bootstrap-admin:
	uv run python -m app.jobs.bootstrap_platform_admin $(args)

bootstrap-admin-in-container:
	$(COMPOSE_DEV) exec web uv run python -m app.jobs.bootstrap_platform_admin $(args)

bootstrap-admin-in-container-env:
	$(COMPOSE_DEV) exec web uv run python -m app.jobs.bootstrap_platform_admin $(args)

shell-web:
	$(COMPOSE_DEV) exec web /bin/sh

psql-web:
	$(COMPOSE_DEV) exec web sh -lc 'echo $$DATABASE__URL'

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy app tests

loadtest-smoke:
	$(COMPOSE_LOADTEST) run --rm k6 run /loadtests/k6/smoke.js

loadtest-read:
	$(COMPOSE_LOADTEST) run --rm k6 run /loadtests/k6/read_baseline.js

loadtest-auth:
	$(COMPOSE_LOADTEST) run --rm k6 run /loadtests/k6/auth_burst.js

loadtest-write:
	$(COMPOSE_LOADTEST_WORKER) run --rm k6 run /loadtests/k6/write_async.js

loadtest-soak:
	$(COMPOSE_LOADTEST) run --rm k6 run /loadtests/k6/soak.js

loadtest-all:
	./scripts/loadtest.sh full
