from datetime import datetime

from pydantic import BaseModel


class FeatureEntitlementResponse(BaseModel):
    id: int
    account_id: int
    resource_key: str
    units_total: int
    units_used: int
    units_remaining: int
    status: str
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    source_type: str
    source_id: str | None = None


class UsageEventResponse(BaseModel):
    id: int
    account_id: int
    entitlement_id: int
    reservation_id: int | None = None
    resource_key: str
    feature_key: str
    units: int
    user_id: int | None = None
    request_id: str
    status: str
    created_at: datetime


class GrantEntitlementRequest(BaseModel):
    resource_key: str
    units_total: int
    source_type: str = "grant"
    source_id: str | None = None
    valid_until: datetime | None = None


class FeatureBalanceResponse(BaseModel):
    account_id: int
    resource_key: str
    units_remaining: int


class AccountEntitlementsResponse(BaseModel):
    account_id: int
    entitlements: list[FeatureEntitlementResponse]


class AccountUsageResponse(BaseModel):
    account_id: int
    total_count: int
    has_next: bool
    has_prev: bool
    usage_events: list[UsageEventResponse]


class AccountBillingSummaryResponse(BaseModel):
    account_id: int
    entitlements: list[FeatureEntitlementResponse]
    balances: list[FeatureBalanceResponse]
    recent_usage_events: list[UsageEventResponse]


class UsageAggregateResponse(BaseModel):
    resource_key: str
    feature_key: str
    status: str
    event_count: int
    units_total: int


class AccountUsageReportResponse(BaseModel):
    account_id: int
    aggregates: list[UsageAggregateResponse]
