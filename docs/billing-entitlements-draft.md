# Billing / Entitlements Draft

This document is a technical draft for adding reusable usage-based entitlements to the template.

The first target use case is:

- a customer purchases access to `service_a`
- the purchase grants `30` units
- each successful call to `service_a.run` consumes `1` unit
- the design must extend cleanly to future features

## Design Choice

Use a real `account` model from day one.

Do not treat `user` as the long-term billing owner.

Recommended ownership model:

- quota owner: `account`
- actor: `user`
- billable capability: `resource_key`
- request-level consumption: `feature_key`

## `feature_key` vs `resource_key`

These two names are intentionally different because they answer different questions.

- `feature_key`
  identifies the application action being performed
- `resource_key`
  identifies the entitlement bucket or quota balance being consumed

Examples:

- `items.create`
  is a `feature_key`
- `items.archive`
  is a `feature_key`
- `item_create`
  is a `resource_key`
- `item_archive`
  is a `resource_key`

Rule of thumb:

- `feature_key` should be action-shaped and stable
- `resource_key` should be billing-shaped and stable
- `feature_key` tells the system what the user is doing
- `resource_key` tells the system which quota bucket to charge

This separation is what makes the entitlement system reusable. Multiple features can:

- map to different quota buckets
- share the same quota bucket
- or later evolve into different pricing policies without renaming the user-facing feature action

## Proposed Models

### `Account`

Target file:

- [app/db/models/account.py](/Users/pluto/Documents/git/fastapi101/app/db/models/account.py)

Suggested shape:

```python
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=120)
    status: str = Field(default="active", index=True, max_length=30)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    users: list["User"] = Relationship(back_populates="account")
```
```

Also add:

- `account_id` to the existing `User` model
- `account` relationship on `User`

### `FeatureEntitlement`

Target file:

- [app/db/models/feature_entitlement.py](/Users/pluto/Documents/git/fastapi101/app/db/models/feature_entitlement.py)

Suggested shape:

```python
from datetime import datetime

from sqlmodel import Field, SQLModel


class FeatureEntitlement(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    resource_key: str = Field(index=True, max_length=100)
    units_total: int = Field(default=0)
    units_used: int = Field(default=0)
    status: str = Field(default="active", index=True, max_length=30)
    valid_from: datetime | None = None
    valid_until: datetime | None = Field(default=None, index=True)
    source_type: str = Field(default="purchase", max_length=30)
    source_id: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```
```

Recommended rules:

- `units_total >= 0`
- `units_used >= 0`
- `units_used <= units_total`

### `UsageReservation`

Target file:

- [app/db/models/usage_reservation.py](/Users/pluto/Documents/git/fastapi101/app/db/models/usage_reservation.py)

Suggested shape:

```python
from datetime import datetime

from sqlmodel import Field, SQLModel


class UsageReservation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    entitlement_id: int = Field(foreign_key="featureentitlement.id", index=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    resource_key: str = Field(index=True, max_length=100)
    feature_key: str = Field(index=True, max_length=120)
    units_reserved: int = Field(default=1)
    request_id: str = Field(index=True, max_length=120)
    status: str = Field(default="active", index=True, max_length=30)
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```
```

### `UsageEvent`

Target file:

- [app/db/models/usage_event.py](/Users/pluto/Documents/git/fastapi101/app/db/models/usage_event.py)

Suggested shape:

```python
from datetime import datetime

from sqlmodel import Field, SQLModel


class UsageEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    entitlement_id: int = Field(foreign_key="featureentitlement.id", index=True)
    reservation_id: int | None = Field(default=None, foreign_key="usagereservation.id", index=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    resource_key: str = Field(index=True, max_length=100)
    feature_key: str = Field(index=True, max_length=120)
    units: int = Field(default=1)
    request_id: str = Field(index=True, max_length=120)
    status: str = Field(default="committed", index=True, max_length=30)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```
```

## Feature Policy Draft

For phase 1, keep the feature map in code rather than creating a DB table.

Suggested location:

- [app/services/entitlement_service.py](/Users/pluto/Documents/git/fastapi101/app/services/entitlement_service.py)

Suggested draft:

```python
FEATURE_POLICIES = {
    "service_a.run": {
        "resource_key": "service_a",
        "units_per_call": 1,
        "charge_on": "success",
    }
}
```

This can later evolve into a DB-backed catalog if needed.

In the example above:

- `service_a.run` is the `feature_key`
- `service_a` is the `resource_key`
- each successful call consumes `1` unit

## How To Add A Policy To A New Feature

When you want to make a new feature quota-protected, the recommended flow is:

1. Choose a stable `feature_key`.
2. Choose a stable `resource_key`.
3. Add the mapping to `FEATURE_POLICIES`.
4. Make sure billing or ops can grant entitlements for that `resource_key`.
5. Call `reserve_feature_usage(...)` from the service layer before the protected work.
6. Call `commit_reserved_usage(...)` on success.
7. Call `release_reserved_usage(...)` if the request fails after reservation.

There are two valid enforcement patterns, and the right choice depends on the feature:

- `validate -> reserve -> write -> commit/release`
  Use this when business validation should win first, such as `not_found`, `forbidden`, or `already_archived`.
- `reserve -> write -> commit/release`
  Use this when the protected write itself is the main action and there is little or no pre-validation beyond auth.

Example: adding a policy for `POST /api/v1/items/{item_id}/archive`

```python
FEATURE_POLICIES = {
    "items.create": {
        "resource_key": "item_create",
        "units_per_call": 1,
        "charge_on": "success",
    },
    "items.archive": {
        "resource_key": "item_archive",
        "units_per_call": 1,
        "charge_on": "success",
    },
}
```

Recommended service flow for `items.archive`:

1. Load the target item.
2. Check `not_found`, ownership, and `already_archived`.
3. Resolve the current user's `account_id`.
4. Call `reserve_feature_usage(..., feature_key="items.archive", ...)`.
5. Perform the archive write.
6. Call `commit_reserved_usage(...)` if the archive succeeds.
7. Call `release_reserved_usage(...)` if the archive fails after reservation.

This is intentionally different from the simpler `items.create` flow. For `archive`, the current implementation preserves the more specific business errors first:

- `item.not_found`
- `item.forbidden`
- `item.already_archived`

Only requests that pass those checks go on to reserve archive quota.

## Reservation And Usage Lifecycle

The current system has three different moments to think about:

1. reservation
2. commit
3. post-commit correction

### Reserve

`reserve_feature_usage(...)` means:

- the feature policy was found
- an active entitlement exists
- enough quota is available
- a `usage_reservation` row is created with status `active`

At this point:

- `units_used` has not increased yet
- no committed usage event exists yet
- the request has only reserved the right to consume quota

Use reservation when you need to protect against concurrent requests before the business write completes.

### Commit

`commit_reserved_usage(...)` is the point where usage becomes real.

In the current implementation, commit does all of the following:

- increments `feature_entitlement.units_used`
- marks the reservation as `committed`
- creates a `usage_event` with status `committed`

Commit should happen only after the protected business write succeeds.

Examples:

- item creation succeeded
- item archive succeeded
- service A completed successfully

Rule of thumb:

- business write succeeded -> `commit`

### Release

`release_reserved_usage(...)` is for a reservation that should not turn into real usage.

In the current implementation, release:

- marks the reservation as `released`
- does not increment `units_used`
- does not create a committed usage event

Use release when the request reserved quota, but the protected work did not finish successfully.

Examples:

- DB write failed after reservation
- downstream operation failed after reservation
- business flow aborted after reserving quota

Rule of thumb:

- reserved, but the protected work failed -> `release`

### Reverse

`reverse` is different from `release`.

Use reversal only after usage was already committed.

That means:

- quota was already consumed
- a committed usage event already exists
- and now you need a correction or reconciliation step

Typical examples:

- an admin refunds a usage charge
- a later reconciliation job discovers the charge was invalid
- a compensating workflow undoes an already-committed usage decision

In other words:

- before commit -> `release`
- after commit -> `reverse`

The current template primarily implements the normal `reserve -> commit/release` flow. The reporting schema already anticipates statuses like `reversed`, but reversal is a separate correction workflow, not the normal failure path for a request that has not committed yet.

## Repository Draft

Suggested files:

- [app/db/repositories/account.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/account.py)
- [app/db/repositories/feature_entitlement.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/feature_entitlement.py)
- [app/db/repositories/usage_reservation.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/usage_reservation.py)
- [app/db/repositories/usage_event.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/usage_event.py)

Suggested responsibilities:

`account.py`
- create account
- get account by id

`feature_entitlement.py`
- get active entitlement for update
- increment used units
- decrement used units if reservation logic requires it

`usage_reservation.py`
- create reservation
- get active reservation by request id
- mark committed
- mark released
- expire stale reservations

`usage_event.py`
- create usage event
- list usage for account

## Service Draft

Suggested files:

- [app/services/entitlement_service.py](/Users/pluto/Documents/git/fastapi101/app/services/entitlement_service.py)
- [app/services/billing_service.py](/Users/pluto/Documents/git/fastapi101/app/services/billing_service.py)

Suggested service interface:

```python
class EntitlementService:
    def get_balance(self, session, account_id: int, resource_key: str) -> ServiceResult[int]: ...
    def reserve_feature_usage(self, session, account_id: int, feature_key: str, user_id: int, request_id: str) -> ServiceResult[UsageReservation]: ...
    def commit_reserved_usage(self, session, reservation_id: int) -> ServiceResult[UsageEvent]: ...
    def release_reserved_usage(self, session, reservation_id: int) -> ServiceResult[None]: ...


class BillingService:
    def grant_entitlement(self, session, account_id: int, resource_key: str, units_total: int, source_type: str, source_id: str | None) -> ServiceResult[FeatureEntitlement]: ...
    def list_entitlements(self, session, account_id: int) -> ServiceResult[list[FeatureEntitlement]]: ...
    def list_usage(self, session, account_id: int) -> ServiceResult[list[UsageEvent]]: ...
```

## Error Code Draft

Suggested additions in [app/services/exceptions.py](/Users/pluto/Documents/git/fastapi101/app/services/exceptions.py):

- `billing.no_entitlement`
- `billing.quota_exhausted`
- `billing.entitlement_expired`
- `billing.feature_not_enabled`

Suggested initial API mapping:

- `quota_exhausted` -> `403`
- `no_entitlement` -> `403`
- `entitlement_expired` -> `403`
- `feature_not_enabled` -> `403`

If your product later needs billing-specific client semantics, you can revisit `402`.

## Request Flow Draft

For a future route such as `POST /api/v1/service-a/run`:

1. authenticate user
2. resolve `account_id`
3. resolve feature policy for `service_a.run`
4. reserve one unit
5. if reservation fails, return a billing error
6. perform business logic
7. on success, commit the reservation into a usage event
8. on failure, release the reservation

## Phase 1 Implementation Checklist

### Step 1: models

Add:

- [app/db/models/account.py](/Users/pluto/Documents/git/fastapi101/app/db/models/account.py)
- [app/db/models/feature_entitlement.py](/Users/pluto/Documents/git/fastapi101/app/db/models/feature_entitlement.py)
- [app/db/models/usage_reservation.py](/Users/pluto/Documents/git/fastapi101/app/db/models/usage_reservation.py)
- [app/db/models/usage_event.py](/Users/pluto/Documents/git/fastapi101/app/db/models/usage_event.py)

Update:

- [app/db/models/user.py](/Users/pluto/Documents/git/fastapi101/app/db/models/user.py)
- [app/db/models/__init__.py](/Users/pluto/Documents/git/fastapi101/app/db/models/__init__.py)
- [app/db/base.py](/Users/pluto/Documents/git/fastapi101/app/db/base.py)

### Step 2: migration

Create one Alembic migration that:

- adds `account`
- adds `account_id` to `user`
- adds entitlement/reservation/event tables

### Step 3: repositories

Create:

- [app/db/repositories/account.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/account.py)
- [app/db/repositories/feature_entitlement.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/feature_entitlement.py)
- [app/db/repositories/usage_reservation.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/usage_reservation.py)
- [app/db/repositories/usage_event.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/usage_event.py)

### Step 4: services

Create:

- [app/services/entitlement_service.py](/Users/pluto/Documents/git/fastapi101/app/services/entitlement_service.py)
- [app/services/billing_service.py](/Users/pluto/Documents/git/fastapi101/app/services/billing_service.py)

### Step 5: schemas

Create:

- [app/schemas/billing.py](/Users/pluto/Documents/git/fastapi101/app/schemas/billing.py)

Initial useful schemas:

- entitlement balance response
- entitlement list response
- usage event response

### Step 6: ops visibility

After the core reserve/commit flow works, add read-only ops endpoints such as:

- `GET /api/v1/ops/billing/accounts/{account_id}/entitlements`
- `GET /api/v1/ops/billing/accounts/{account_id}/usage`

### Step 7: first feature integration

Introduce one feature key:

- `service_a.run`

Wire it into one API flow before expanding to more features.

### Step 8: tests

Add unit tests for:

- active entitlement lookup
- quota exhausted behavior
- expired entitlement behavior
- reservation commit
- reservation release

Add integration tests for:

- successful request consumes quota
- failed request does not permanently consume quota
- concurrent requests do not overspend quota

## Recommended Phase 1 Scope

Keep phase 1 intentionally small:

- one-time purchased quota
- one account owns the quota
- one feature consumes it
- one unit per successful request

Do not add recurring billing or payment integration yet.
