# API Guide

This guide is for people who want to use this template to build new API endpoints quickly and consistently.

## Mental Model

The API stack is intentionally layered:

- `app/api`: HTTP concerns only
- `app/services`: business rules
- `app/db/repositories`: persistence
- `app/db/models`: database tables
- `app/schemas`: request/response contracts

Normal request flow:

```text
Client -> Route -> Dependencies -> Service -> Repository -> Database
                                      |
                                      -> ServiceResult -> API response
```

Important rule:

- routes should not contain business logic
- services should not know about HTTP
- repositories should own persistence details

## Where To Add A New API Resource

If you want to add a new resource such as `orders`, the usual touch points are:

- `app/schemas/orders.py`
- `app/db/models/order.py`
- `app/db/repositories/order.py`
- `app/services/order_service.py`
- `app/api/v1/orders.py`
- `app/api/v1/router.py`
- `alembic/versions/*.py`
- tests under `tests/unit` and `tests/integration`

## Step-By-Step: Add A New Resource

1. Define request/response schemas in `app/schemas/<resource>.py`.
2. Add or extend SQLModel tables in `app/db/models/<resource>.py`.
3. Register model imports through `app/db/models/__init__.py` and `app/db/base.py` if needed for Alembic discovery.
4. Create repository functions in `app/db/repositories/<resource>.py`.
5. Create service functions in `app/services/<resource>_service.py`.
6. Return `ServiceResult` from the service layer instead of raising `HTTPException`.
7. Create endpoints in `app/api/v1/<resource>.py`.
8. Register the router in `app/api/v1/router.py`.
9. Generate and review an Alembic migration.
10. Add unit and integration tests.

## Step-By-Step: Add A New Endpoint

Not every endpoint needs a brand-new resource. Sometimes you are just adding:

- a new action on an existing model
- a filtered list endpoint
- a summary or report endpoint
- a protected ops endpoint
- a feature-specific write flow

Use this checklist before you write code:

1. define what the endpoint does
2. define its input and output
3. decide whether auth or role checks are required
4. decide whether it changes the database
5. decide whether it triggers worker, outbox, or entitlement logic

Then follow the normal implementation order:

1. add request and response schemas first
2. add or extend models only if persisted data really changes
3. add or extend repositories if new queries or writes are needed
4. add business logic in the service layer
5. add the route in `app/api/v1`
6. register the router if it is a new router file
7. add tests
8. update docs if this becomes part of the public or team-facing API

Recommended mental model:

```text
schema -> model/repository -> service -> route -> router -> tests -> docs
```

If there is no schema change, skip the model and migration work. If there is no new persistence behavior, skip repository changes and keep the work in the service and route layers.

## What Routes Should Do

Routes should stay thin. A route should usually:

1. accept input through a schema
2. resolve dependencies such as DB session or current user
3. call a service function
4. return `unwrap_result(...)`

Current examples:

- [`app/api/v1/users.py`](../app/api/v1/users.py)
- [`app/api/v1/items.py`](../app/api/v1/items.py)
- [`app/api/v1/auth.py`](../app/api/v1/auth.py)

The `items` route is also the example for entitlement enforcement. Its create path passes `request_id` into the service layer so the service can reserve and commit quota usage without moving billing logic into the route.

When you add a new endpoint, the route is the last place business decisions should appear. Keep it focused on:

- input parsing
- dependency resolution
- calling the service
- returning a response model

## What Services Should Do

Services should own:

- business decisions
- orchestration across repositories
- translating repository failures into service-level outcomes

Services should not:

- return FastAPI responses
- raise `HTTPException`
- read request headers directly

Current examples:

- [`app/services/user_service.py`](../app/services/user_service.py)
- [`app/services/item_service.py`](../app/services/item_service.py)
- [`app/services/auth_service.py`](../app/services/auth_service.py)

`ItemService.create_item_for_user(...)` is the best reference if you need to add usage-gated features. It shows the recommended pattern:

1. resolve the feature key in the service
2. reserve usage against the current account
3. perform the business write
4. commit usage only after the write succeeds

If you are adding an endpoint that is not a simple CRUD read, start by asking whether the business rule belongs here. In this template, it usually does.

## What Repositories Should Do

Repositories should own:

- queries
- insert/update/delete behavior
- commit/refresh/rollback details

Current examples:

- [`app/db/repositories/user.py`](../app/db/repositories/user.py)
- [`app/db/repositories/item.py`](../app/db/repositories/item.py)
- [`app/db/repositories/revoked_token.py`](../app/db/repositories/revoked_token.py)

## How Errors Flow

Service failures are converted to API errors through:

- [`app/services/result.py`](../app/services/result.py)
- [`app/api/errors.py`](../app/api/errors.py)
- centralized handlers in [`app/main.py`](../app/main.py)

This gives you:

- consistent status codes
- consistent error payloads
- consistent logging

## Useful Existing Endpoints

Examples already in the template:

- `POST /api/v1/users/`
- `GET /api/v1/users/{user_id}`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/items/`
- `GET /api/v1/items/`

`POST /api/v1/items/` is quota-protected by the sample entitlement policy:

- feature key: `items.create`
- resource key: `item_create`
- units per successful call: `1`

## Best Practices For New API Work

- define schemas before writing route logic
- decide the endpoint contract before choosing where code lives
- add repository functions before wiring services
- prefer explicit response models
- use `request_id` and standardized errors as part of your API contract
- write integration tests for endpoint behavior, not just unit tests
- update docs when the endpoint is something another developer, operator, or client should discover

## Endpoint PR Checklist

Use this as a quick pre-PR checklist when adding an endpoint:

```text
[ ] I can describe the endpoint input, output, and auth requirement clearly.
[ ] Request and response schemas were added or updated first.
[ ] Business logic lives in the service layer, not in the route.
[ ] Repository changes were added only when new persistence behavior was needed.
[ ] Alembic migration was added if the schema changed.
[ ] The route returns explicit response models or standardized errors.
[ ] The router was registered if a new router file was introduced.
[ ] Integration tests cover the endpoint behavior.
[ ] Unit or repository tests were added where the logic is non-trivial.
[ ] Docs were updated if another developer, operator, or client should discover this endpoint.
```

If the endpoint includes quota, outbox, worker, or other cross-cutting behavior, add one more check:

```text
[ ] The side effect is enforced in the service layer and tested through the real endpoint flow.
```

## Example Walkthrough: Add A New Endpoint

Here is a practical example of how to think through a new endpoint without jumping straight into route code.

Example goal:

- add `POST /api/v1/items/{item_id}/archive`
- authenticated owner can archive an item
- response should return the updated item
- no new table is required
- the change does affect persisted state

Recommended design sequence:

### 1. Define The Contract

Decide first:

- does the endpoint need a request body, or is the path enough
- what response shape should clients receive
- who is allowed to call it
- what should happen if the item does not exist or is not owned by the caller

In this example:

- path parameter: `item_id`
- no request body needed
- auth required
- owner-only behavior
- response returns the archived item

### 2. Check Whether Schema Changes Are Needed

Ask whether the database needs to store new state.

In this example, you might need:

- a new `is_archived` column on `item`
- optionally an `archived_at` timestamp

That means:

- update the model
- generate a migration
- review and apply the migration

If the endpoint were only a computed summary, you might skip model and migration changes entirely.

### 3. Update Schemas

Before touching the route, define the API shapes.

Possible outcomes:

- keep using the existing `ItemPublic` response schema if it already fits
- or add/update a schema so the archived state is visible in the response

The important point is that the response contract should be intentional, not accidental.

### 4. Add Repository Behavior

If the endpoint needs new query or write behavior, add it in the repository.

For this example, that might mean:

- load item by `id`
- ensure the owner matches the current user
- mark the item archived
- save and refresh the row

### 5. Put The Business Rule In The Service

The service should decide:

- whether the item exists
- whether the current user is allowed to archive it
- whether archiving is idempotent or should fail if already archived
- what service-level error to return on failure

This is the layer where the rule belongs, not in the route.

### 6. Add The Route Last

The route should stay thin:

1. parse `item_id`
2. resolve `current_user` and `session`
3. call the service
4. return the response model

That keeps the route readable and consistent with the rest of the template.

### 7. Add Tests

For this example, useful tests would be:

- owner can archive item successfully
- another user cannot archive it
- missing item returns the expected error
- archived state is reflected in the response

At minimum:

- service tests for the rule
- integration tests for the endpoint behavior

### 8. Update Docs If The Endpoint Matters

If the endpoint is something a client or teammate should know about, update:

- API guide or recipes
- client-facing auth docs if usage changes
- OpenAPI usage examples if needed

## Fast Decision Rule

When you are unsure where a piece of code belongs, use this shortcut:

- request or response shape -> `schemas`
- stored data shape -> `models`
- query or save behavior -> `repositories`
- business decision -> `services`
- HTTP wiring -> `routes`
- discoverability -> `docs`
