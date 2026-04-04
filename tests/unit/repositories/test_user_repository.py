from app.db.models.user import User
from app.db.repositories.user import create_user, get_user_by_id, get_user_by_username


def test_create_user_persists_model(session):
    user = User(
        username="repo_user",
        email="repo@example.com",
        hashed_password="hashed",
    )

    created = create_user(session, user)

    assert created.id is not None
    assert created.username == "repo_user"


def test_get_user_queries_by_id_and_username(session):
    user = User(
        username="lookup_user",
        email="lookup@example.com",
        hashed_password="hashed",
    )
    created = create_user(session, user)
    assert created.id is not None

    by_id = get_user_by_id(session, created.id)
    by_username = get_user_by_username(session, "lookup_user")

    assert by_id is not None
    assert by_username is not None
    assert by_id.id == created.id
    assert by_username.email == "lookup@example.com"
