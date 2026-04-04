"""initial schema

Revision ID: 20260402_0001
Revises:
Create Date: 2026-04-02 13:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "20260402_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_account_name"), "account", ["name"], unique=True)
    op.create_index(op.f("ix_account_status"), "account", ["status"], unique=False)

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("phone", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("email_verification_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_account_id"), "user", ["account_id"], unique=False)
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)

    op.create_table(
        "item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_item_owner_id"), "item", ["owner_id"], unique=False)
    op.create_index(op.f("ix_item_title"), "item", ["title"], unique=False)

    op.create_table(
        "revoked_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("token_type", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_revoked_token_jti"), "revoked_token", ["jti"], unique=True)

    op.create_table(
        "outbox_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("task_name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_outbox_event_available_at"),
        "outbox_event",
        ["available_at"],
        unique=False,
    )
    op.create_index(op.f("ix_outbox_event_status"), "outbox_event", ["status"], unique=False)
    op.create_index(op.f("ix_outbox_event_task_id"), "outbox_event", ["task_id"], unique=True)
    op.create_index(op.f("ix_outbox_event_task_name"), "outbox_event", ["task_name"], unique=False)

    op.create_table(
        "feature_entitlement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("resource_key", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("units_total", sa.Integer(), nullable=False),
        sa.Column("units_used", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_type", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("source_id", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_feature_entitlement_account_id"),
        "feature_entitlement",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_feature_entitlement_resource_key"),
        "feature_entitlement",
        ["resource_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_feature_entitlement_status"),
        "feature_entitlement",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_feature_entitlement_valid_until"),
        "feature_entitlement",
        ["valid_until"],
        unique=False,
    )

    op.create_table(
        "usage_reservation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("entitlement_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("resource_key", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("feature_key", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("units_reserved", sa.Integer(), nullable=False),
        sa.Column("request_id", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"]),
        sa.ForeignKeyConstraint(["entitlement_id"], ["feature_entitlement.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_usage_reservation_account_id"),
        "usage_reservation",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_reservation_entitlement_id"),
        "usage_reservation",
        ["entitlement_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_reservation_user_id"),
        "usage_reservation",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_reservation_resource_key"),
        "usage_reservation",
        ["resource_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_reservation_feature_key"),
        "usage_reservation",
        ["feature_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_reservation_request_id"),
        "usage_reservation",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_reservation_status"),
        "usage_reservation",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_reservation_expires_at"),
        "usage_reservation",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "usage_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("entitlement_id", sa.Integer(), nullable=False),
        sa.Column("reservation_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("resource_key", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("feature_key", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("request_id", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"]),
        sa.ForeignKeyConstraint(["entitlement_id"], ["feature_entitlement.id"]),
        sa.ForeignKeyConstraint(["reservation_id"], ["usage_reservation.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usage_event_account_id"), "usage_event", ["account_id"], unique=False)
    op.create_index(
        op.f("ix_usage_event_entitlement_id"),
        "usage_event",
        ["entitlement_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_event_reservation_id"),
        "usage_event",
        ["reservation_id"],
        unique=False,
    )
    op.create_index(op.f("ix_usage_event_user_id"), "usage_event", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_usage_event_resource_key"),
        "usage_event",
        ["resource_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_event_feature_key"),
        "usage_event",
        ["feature_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usage_event_request_id"),
        "usage_event",
        ["request_id"],
        unique=False,
    )
    op.create_index(op.f("ix_usage_event_status"), "usage_event", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_usage_event_status"), table_name="usage_event")
    op.drop_index(op.f("ix_usage_event_request_id"), table_name="usage_event")
    op.drop_index(op.f("ix_usage_event_feature_key"), table_name="usage_event")
    op.drop_index(op.f("ix_usage_event_resource_key"), table_name="usage_event")
    op.drop_index(op.f("ix_usage_event_user_id"), table_name="usage_event")
    op.drop_index(op.f("ix_usage_event_reservation_id"), table_name="usage_event")
    op.drop_index(op.f("ix_usage_event_entitlement_id"), table_name="usage_event")
    op.drop_index(op.f("ix_usage_event_account_id"), table_name="usage_event")
    op.drop_table("usage_event")
    op.drop_index(op.f("ix_usage_reservation_expires_at"), table_name="usage_reservation")
    op.drop_index(op.f("ix_usage_reservation_status"), table_name="usage_reservation")
    op.drop_index(op.f("ix_usage_reservation_request_id"), table_name="usage_reservation")
    op.drop_index(op.f("ix_usage_reservation_feature_key"), table_name="usage_reservation")
    op.drop_index(op.f("ix_usage_reservation_resource_key"), table_name="usage_reservation")
    op.drop_index(op.f("ix_usage_reservation_user_id"), table_name="usage_reservation")
    op.drop_index(op.f("ix_usage_reservation_entitlement_id"), table_name="usage_reservation")
    op.drop_index(op.f("ix_usage_reservation_account_id"), table_name="usage_reservation")
    op.drop_table("usage_reservation")
    op.drop_index(op.f("ix_feature_entitlement_valid_until"), table_name="feature_entitlement")
    op.drop_index(op.f("ix_feature_entitlement_status"), table_name="feature_entitlement")
    op.drop_index(op.f("ix_feature_entitlement_resource_key"), table_name="feature_entitlement")
    op.drop_index(op.f("ix_feature_entitlement_account_id"), table_name="feature_entitlement")
    op.drop_table("feature_entitlement")
    op.drop_index(op.f("ix_outbox_event_task_name"), table_name="outbox_event")
    op.drop_index(op.f("ix_outbox_event_task_id"), table_name="outbox_event")
    op.drop_index(op.f("ix_outbox_event_status"), table_name="outbox_event")
    op.drop_index(op.f("ix_outbox_event_available_at"), table_name="outbox_event")
    op.drop_table("outbox_event")
    op.drop_index(op.f("ix_revoked_token_jti"), table_name="revoked_token")
    op.drop_table("revoked_token")
    op.drop_index(op.f("ix_item_title"), table_name="item")
    op.drop_index(op.f("ix_item_owner_id"), table_name="item")
    op.drop_table("item")
    op.drop_index(op.f("ix_user_account_id"), table_name="user")
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_account_status"), table_name="account")
    op.drop_index(op.f("ix_account_name"), table_name="account")
    op.drop_table("account")
