# Database Migrations

This guide explains how database schema changes should be made in this template.

The short version:

- change models first
- generate or edit an Alembic migration
- apply the migration through the running stack
- verify the schema before continuing

Alembic is the schema source of truth. The app should not create tables implicitly at startup.

## Recommended Migration Checklist

If you only want one practical checklist to follow, use this:

```text
[ ] I changed the SQLModel definition first.
[ ] New models were imported in app/db/models/__init__.py and app/db/base.py.
[ ] The local Compose stack is running.
[ ] I created a migration with make migration m="...".
[ ] I reviewed the generated upgrade() and downgrade() code.
[ ] I checked defaults, nullability, and foreign keys carefully.
[ ] I applied the migration with make migrate.
[ ] I verified the schema in Postgres.
[ ] I ran lint, typecheck, and tests.
```

This is the normal happy-path workflow for local development.

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

### Example: Adding Archive Fields To `item`

Suppose you added these model fields:

- `is_archived: bool = False`
- `archived_at: datetime | None = None`

The migration review should answer these questions:

- did Alembic add both columns to the `item` table
- is `is_archived` non-nullable or nullable as intended
- is there a sensible default for existing rows
- is `archived_at` nullable
- does `downgrade()` remove the same columns cleanly

For a change like this, a good review mindset is:

1. existing rows should remain valid
2. new rows should get predictable defaults
3. rollback should not leave partial schema state behind

### Important Pattern: Adding A New Non-Null Column

This is one of the most common migration mistakes.

If a table already contains rows, this will often fail:

```python
op.add_column("item", sa.Column("is_archived", sa.Boolean(), nullable=False))
```

Why it fails:

- the new column is `NOT NULL`
- existing rows do not have a value for it yet
- Postgres rejects the change with a `NotNullViolation`

For a column like `is_archived`, a safer migration pattern is:

```python
op.add_column(
    "item",
    sa.Column(
        "is_archived",
        sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),
    ),
)
op.add_column(
    "item",
    sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
)
op.alter_column("item", "is_archived", server_default=None)
```

Why this works:

- existing rows get `false`
- the column can still end up `NOT NULL`
- `archived_at` stays nullable
- the temporary DB default can be removed after the backfill effect is complete

Another valid pattern is:

1. add the column as nullable
2. backfill old rows with `UPDATE`
3. alter the column to `nullable=False`

Use one of these patterns whenever you add a non-null column to a table that already has data.

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

Useful manual DB verification in `psql`:

```sql
\d item
SELECT id, title, is_archived, archived_at FROM item LIMIT 5;
```

For other tables, use the same idea:

- inspect the table definition with `\d <table_name>`
- inspect a few real rows with `SELECT ... LIMIT ...`

## What To Do After A Successful Migration

Once `make migrate` succeeds, treat that as the start of verification, not the end of the work.

Recommended next steps:

1. inspect the changed table in `psql`
2. inspect a few real rows
3. continue with the schema-dependent code changes
4. run tests or the target workflow

For the `item archive` example, a practical follow-up looks like:

```sql
\d item
SELECT id, title, is_archived, archived_at FROM item LIMIT 5;
```

Then continue with the rest of the feature work:

- response schema updates
- repository behavior
- service logic
- route wiring
- integration tests

The key point is that a successful migration only proves the schema changed. It does not prove the feature is complete.

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

As a rule of thumb:

- try `make migrate` first
- reset the local volume only when the DB is disposable and clearly out of sync

### Migration Fails With `NotNullViolation`

If you see an error like this:

```text
column "is_archived" of relation "item" contains null values
```

that usually does not mean you need to drop the database.

It usually means:

- the migration added a `NOT NULL` column
- existing rows were not given a default or backfill value

The normal fix is:

1. edit the migration file
2. use a safe non-null pattern with `server_default` or backfill
3. run `make migrate` again

In the normal local flow, failed Alembic migrations on Postgres are typically rolled back transactionally, so fixing the migration file and rerunning is usually enough.

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
