# Database Migrations

This guide explains how database schema changes should be made in this template.

The short version:

- change models first
- generate or edit an Alembic migration
- apply the migration through the running stack
- verify the schema before continuing

Alembic is the schema source of truth. The app should not create tables implicitly at startup.

## Files Involved

The main files involved in schema changes are:

- [`app/db/models`](../app/db/models): SQLModel tables
- [`app/db/models/__init__.py`](../app/db/models/__init__.py): model imports
- [`app/db/base.py`](../app/db/base.py): metadata discovery for Alembic
- [`alembic/env.py`](../alembic/env.py): Alembic environment wiring
- [`alembic/versions`](../alembic/versions): migration history
- [`Makefile`](../Makefile): local helper commands such as `make migrate` and `make migration`

## Normal Local Workflow

Use this flow whenever you add, remove, or change a table or column.

### 1. Update The Models

Change the SQLModel definitions under [`app/db/models`](../app/db/models).

Common examples:

- add a new table
- add a new column
- change indexes or uniqueness
- add new foreign keys

If you add a brand-new model, also make sure it is imported in:

- [`app/db/models/__init__.py`](../app/db/models/__init__.py)
- [`app/db/base.py`](../app/db/base.py)

If Alembic cannot see the model metadata, it cannot generate the migration correctly.

### 2. Start The Local Stack

If the development stack is not already running:

```bash
make up
make ps
```

The normal development flow expects migrations to run from inside the `web` container so the app, Alembic, and Postgres all use the same runtime configuration.

### 3. Generate A Migration

Create a new Alembic revision:

```bash
make migration m="describe the schema change"
```

Example:

```bash
make migration m="add invoice table"
```

This runs:

```bash
uv run alembic revision --autogenerate -m "..."
```

inside the running `web` container.

### 4. Review The Generated Migration

Open the new file in [`alembic/versions`](../alembic/versions) and review it carefully.

Check at least these things:

- the right table names are being changed
- foreign keys point at the expected tables
- indexes and uniqueness match the model intent
- `upgrade()` and `downgrade()` are both reasonable
- destructive operations are intentional

Autogenerate is a helper, not the final authority. You should expect to edit the migration file when the change is non-trivial.

### 5. Apply The Migration

Apply the latest schema to the running local database:

```bash
make migrate
```

This runs:

```bash
uv run alembic upgrade head
```

inside the `web` container.

### 6. Verify The Result

After applying the migration, verify the schema before moving on.

Useful checks:

```bash
make ps
make logs
make psql
```

Then run the normal checks:

```bash
make lint
make typecheck
uv run pytest -q
```

If the change is tied to a route or service, also test the affected workflow through Swagger or integration tests.

## When To Create A New Initial Migration

For an actively used environment, add forward-only migrations.

For a newly cloned template that has not been deployed anywhere yet, you may decide to replace the initial migration entirely so it matches the real schema of the new product.

That is common when:

- removing the sample `items` module
- replacing example tables before the first real deploy
- starting a product from a clean schema baseline

The key rule is consistency:

- before first deploy, a clean initial migration is fine
- after a shared environment exists, add normal incremental migrations instead

## Deployment Flow

Production-like environments should follow the same basic rule:

1. ship code and migration together
2. run `alembic upgrade head`
3. start or roll the application

Do not rely on `create_all()` or startup-time implicit table creation.

For this template, the API app, background worker, outbox dispatcher, and maintenance jobs all assume the DB schema is already at the expected Alembic revision.

## Common Local Problems

### The App Code Is Newer Than The Database

Typical errors look like:

- `column user.email_verified does not exist`
- `column user.account_id does not exist`
- relation or foreign key errors after adding new models

This usually means:

- the code changed
- the local Postgres volume still contains an older schema
- the migration has not been applied yet

First try:

```bash
make migrate
```

### `make migrate` Runs But The Schema Still Looks Wrong

If this is a disposable local database and the schema history is badly out of sync, reset the local Postgres volume and recreate the DB from scratch.

Typical reset flow:

```bash
make down
docker volume rm fastapi101_postgres_data
make up
make migrate
```

Only do this when the local data can be discarded safely.

### Running Commands From The Host Uses The Wrong Database Host

If you run app commands directly on your machine, you may see errors like:

```text
failed to resolve host 'db'
```

That happens because `db` is the Compose service hostname, not a hostname available from your host shell.

When your stack is running through Compose, prefer container-aware commands such as:

```bash
make migrate
make bootstrap-admin-in-container
make bootstrap-admin-in-container-env
```

### Alembic Did Not See A New Table

Check that the model was imported in:

- [`app/db/models/__init__.py`](../app/db/models/__init__.py)
- [`app/db/base.py`](../app/db/base.py)

If the metadata import path is incomplete, autogenerate may silently miss the table.

## Recommended Team Habit

For every schema change:

1. change the model
2. generate the migration
3. review the migration
4. apply it locally
5. run tests
6. only then continue with the feature

This keeps schema drift small and makes failures much easier to debug.
