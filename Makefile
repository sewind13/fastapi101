up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose exec web uv run alembic upgrade head