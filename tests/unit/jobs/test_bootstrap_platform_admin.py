import pytest

from app.core.security import get_password_hash
from app.db.models.user import User as UserModel
from app.db.repositories.user import get_user_by_username
from app.jobs.bootstrap_platform_admin import bootstrap_platform_admin
from tests.unit.repositories.conftest import session as session


def test_bootstrap_platform_admin_creates_new_privileged_user(session):
    result = bootstrap_platform_admin(
        username="platformadmin",
        email="platformadmin@example.com",
        password="StrongPass123!",
        role="platform_admin",
        session=session,
    )

    created_user = get_user_by_username(session, "platformadmin")

    assert result["action"] == "created"
    assert created_user is not None
    assert created_user.role == "platform_admin"
    assert created_user.is_active is True
    assert created_user.email_verified is True


def test_bootstrap_platform_admin_promotes_existing_user(session):
    session.add(
        UserModel(
            username="existingadmin",
            email="existingadmin@example.com",
            hashed_password=get_password_hash("StrongPass123!"),
            role="user",
        )
    )
    session.commit()

    result = bootstrap_platform_admin(
        username="existingadmin",
        role="ops_admin",
        session=session,
    )

    promoted_user = get_user_by_username(session, "existingadmin")

    assert result["action"] == "promoted"
    assert promoted_user is not None
    assert promoted_user.role == "ops_admin"


def test_bootstrap_platform_admin_requires_creation_inputs_for_new_user(session):
    with pytest.raises(ValueError, match="email and password are required"):
        bootstrap_platform_admin(
            username="missinginputs",
            role="platform_admin",
            session=session,
        )
