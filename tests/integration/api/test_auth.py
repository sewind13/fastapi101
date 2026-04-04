import pytest

from app.core.config import settings
from app.core.security import create_email_verification_token, create_password_reset_token


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_user_success(client):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/users/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["email_verified"] is False
    assert "id" in data
    assert "password" not in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    payload = {
        "username": "sameuser",
        "email": "user1@example.com",
        "password": "password123",
    }
    await client.post("/api/v1/users/", json=payload)

    payload["email"] = "user2@example.com"
    response = await client.post("/api/v1/users/", json=payload)

    assert response.status_code == 400
    assert "already exists" in response.json()["message"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_user_is_blocked_when_public_registration_disabled(client, monkeypatch):
    monkeypatch.setattr(settings.api, "public_registration_enabled", False)

    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "blockeduser",
            "email": "blocked@example.com",
            "password": "strongpassword123",
        },
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Public registration is disabled."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_user_rejects_password_that_contains_username(client):
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "weakuser-password",
        },
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Password must not contain the username."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success(client):
    register_payload = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "correct_password",
    }
    await client.post("/api/v1/users/", json=register_payload)

    login_data = {
        "username": "loginuser",
        "password": "correct_password",
    }
    response = await client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_expires_in"] > 0
    assert data["refresh_expires_in"] > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_requires_verified_email_when_enabled(client, monkeypatch):
    monkeypatch.setattr(settings.security, "require_verified_email_for_login", True)

    await client.post(
        "/api/v1/users/",
        json={
            "username": "unverifiedlogin",
            "email": "unverifiedlogin@example.com",
            "password": "correct_password",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "unverifiedlogin", "password": "correct_password"},
    )

    assert response.status_code == 403
    assert (
        response.json()["message"]
        == "This account must verify its email address before signing in."
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_wrong_password(client):
    register_payload = {
        "username": "wrongpwuser",
        "email": "wrongpw@example.com",
        "password": "real_password",
    }
    await client.post("/api/v1/users/", json=register_payload)

    login_data = {
        "username": "wrongpwuser",
        "password": "fake_password",
    }
    response = await client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid username or password."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_rate_limit_blocks_repeated_failed_attempts(client, monkeypatch):
    monkeypatch.setattr(settings.auth_rate_limit, "login_max_attempts", 2)
    monkeypatch.setattr(settings.auth_rate_limit, "login_window_seconds", 300)

    register_payload = {
        "username": "ratelimituser",
        "email": "ratelimit@example.com",
        "password": "real_password",
    }
    await client.post("/api/v1/users/", json=register_payload)

    first_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "ratelimituser", "password": "bad_password"},
    )
    second_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "ratelimituser", "password": "bad_password"},
    )
    third_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "ratelimituser", "password": "bad_password"},
    )

    assert first_response.status_code == 401
    assert second_response.status_code == 429
    assert second_response.headers["Retry-After"].isdigit()
    assert (
        second_response.json()["message"]
        == "Too many failed login attempts. Please try again later."
    )
    assert third_response.status_code == 429


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_locks_account_after_failed_password_threshold(client, monkeypatch):
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_enabled", True)
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_max_attempts", 2)
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_seconds", 300)
    monkeypatch.setattr(settings.auth_rate_limit, "login_max_attempts", 50)

    await client.post(
        "/api/v1/users/",
        json={
            "username": "lockme",
            "email": "lockme@example.com",
            "password": "real_password",
        },
    )

    first_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "lockme", "password": "bad_password"},
    )
    second_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "lockme", "password": "bad_password"},
    )
    locked_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "lockme", "password": "real_password"},
    )

    assert first_response.status_code == 401
    assert second_response.status_code == 423
    assert (
        second_response.json()["message"]
        == "This account is temporarily locked. Please try again later."
    )
    assert locked_response.status_code == 423


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success_resets_failed_login_counter(client, monkeypatch):
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_enabled", True)
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_max_attempts", 2)
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_seconds", 300)
    monkeypatch.setattr(settings.auth_rate_limit, "login_max_attempts", 50)

    await client.post(
        "/api/v1/users/",
        json={
            "username": "resetcounter",
            "email": "resetcounter@example.com",
            "password": "real_password",
        },
    )

    failed_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "resetcounter", "password": "bad_password"},
    )
    successful_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "resetcounter", "password": "real_password"},
    )
    next_failed_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "resetcounter", "password": "bad_password"},
    )

    assert failed_response.status_code == 401
    assert successful_response.status_code == 200
    assert next_failed_response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_other_user_id_is_forbidden_before_lookup(client):
    register_payload = {
        "username": "lookupuser",
        "email": "lookup@example.com",
        "password": "correct_password",
    }
    await client.post("/api/v1/users/", json=register_payload)
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "lookupuser", "password": "correct_password"},
    )
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/users/9999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_other_user_by_id_requires_ops_admin(client):
    await client.post(
        "/api/v1/users/",
        json={
            "username": "firstuser",
            "email": "first@example.com",
            "password": "correct_password",
        },
    )
    second_response = await client.post(
        "/api/v1/users/",
        json={
            "username": "seconduser",
            "email": "second@example.com",
            "password": "correct_password",
        },
    )
    target_user_id = second_response.json()["id"]

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "firstuser", "password": "correct_password"},
    )
    token = login_response.json()["access_token"]

    response = await client.get(
        f"/api/v1/users/{target_user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_own_user_by_id_is_allowed(client):
    register_response = await client.post(
        "/api/v1/users/",
        json={
            "username": "selfuser",
            "email": "self@example.com",
            "password": "correct_password",
        },
    )
    user_id = register_response.json()["id"]

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "selfuser", "password": "correct_password"},
    )
    token = login_response.json()["access_token"]

    response = await client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "selfuser"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_current_user_profile(client):
    register_payload = {
        "username": "meuser",
        "email": "me@example.com",
        "password": "correct_password",
    }
    await client.post("/api/v1/users/", json=register_payload)

    login_data = {
        "username": "meuser",
        "password": "correct_password",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "meuser"
    assert response.json()["email_verified"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_email_verification_requires_authentication(client):
    response = await client.post("/api/v1/auth/verify-email/request")

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_email_verification_for_authenticated_user(client):
    await client.post(
        "/api/v1/users/",
        json={
            "username": "verifyme",
            "email": "verifyme@example.com",
            "password": "correct_password",
        },
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "verifyme", "password": "correct_password"},
    )
    token = login_response.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/verify-email/request",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Verification email queued."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_password_reset_does_not_leak_user_existence(client):
    response = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "missing@example.com"},
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "If an account exists for that email address, a password reset email has been queued."
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_password_reset_updates_password_and_clears_lockout(client, monkeypatch):
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_enabled", True)
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_max_attempts", 2)
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_seconds", 300)
    monkeypatch.setattr(settings.auth_rate_limit, "login_max_attempts", 50)

    register_response = await client.post(
        "/api/v1/users/",
        json={
            "username": "resetflow",
            "email": "resetflow@example.com",
            "password": "old_password",
        },
    )
    user_id = register_response.json()["id"]
    reset_token = create_password_reset_token(subject=str(user_id), username="resetflow")

    await client.post(
        "/api/v1/auth/login",
        data={"username": "resetflow", "password": "bad_password"},
    )
    await client.post(
        "/api/v1/auth/login",
        data={"username": "resetflow", "password": "bad_password"},
    )

    reset_response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "new_password_123"},
    )

    assert reset_response.status_code == 200
    assert reset_response.json()["message"] == "Password reset successfully."

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "resetflow", "password": "new_password_123"},
    )
    assert login_response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_password_reset_rejects_invalid_token(client):
    response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "bad-token", "new_password": "new_password_123"},
    )

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_email_verification_marks_user_verified(client):
    register_response = await client.post(
        "/api/v1/users/",
        json={
            "username": "verifyconfirm",
            "email": "verifyconfirm@example.com",
            "password": "correct_password",
        },
    )
    user_id = register_response.json()["id"]
    token = create_email_verification_token(subject=str(user_id), username="verifyconfirm")

    response = await client.get(
        "/api/v1/auth/verify-email/confirm",
        params={"token": token},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully."

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "verifyconfirm", "password": "correct_password"},
    )
    access_token = login_response.json()["access_token"]
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email_verified"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_email_verification_rejects_invalid_token(client):
    response = await client.get(
        "/api/v1/auth/verify-email/confirm",
        params={"token": "not-a-real-token"},
    )

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_token_rotates_and_invalidates_previous_refresh_token(client):
    register_payload = {
        "username": "refreshuser",
        "email": "refresh@example.com",
        "password": "correct_password",
    }
    await client.post("/api/v1/users/", json=register_payload)

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "refreshuser", "password": "correct_password"},
    )
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["access_token"] != login_response.json()["access_token"]
    assert refreshed["refresh_token"] != refresh_token

    replay_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert replay_response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_rate_limit_blocks_repeated_requests(client, monkeypatch):
    monkeypatch.setattr(settings.auth_rate_limit, "token_max_attempts", 2)
    monkeypatch.setattr(settings.auth_rate_limit, "token_window_seconds", 60)

    first_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not-a-valid-refresh-token"},
    )
    second_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not-a-valid-refresh-token"},
    )
    third_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not-a-valid-refresh-token"},
    )

    assert first_response.status_code == 401
    assert second_response.status_code == 429
    assert second_response.headers["Retry-After"].isdigit()
    assert (
        second_response.json()["message"]
        == "Too many authentication requests. Please try again later."
    )
    assert third_response.status_code == 429


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client):
    register_payload = {
        "username": "logoutuser",
        "email": "logout@example.com",
        "password": "correct_password",
    }
    await client.post("/api/v1/users/", json=register_payload)

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "logoutuser", "password": "correct_password"},
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out successfully"

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_inactive_user_cannot_access_me(client, session):
    register_payload = {
        "username": "inactiveuser",
        "email": "inactive@example.com",
        "password": "correct_password",
    }
    await client.post("/api/v1/users/", json=register_payload)

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "inactiveuser", "password": "correct_password"},
    )
    token = login_response.json()["access_token"]

    from app.db.repositories.user import get_user_by_username

    user = get_user_by_username(session, "inactiveuser")
    assert user is not None
    user.is_active = False
    session.add(user)
    session.commit()

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
