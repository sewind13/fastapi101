from app.db.models.item import Item
from app.db.models.user import User
from app.db.repositories.item import create_item, list_items_by_owner_id
from app.db.repositories.user import create_user


def test_create_item_persists_model(session):
    owner = create_user(
        session,
        User(username="owner", email="owner@example.com", hashed_password="hashed"),
    )
    assert owner.id is not None
    item = Item(title="Repo Item", description="stored", owner_id=owner.id)

    created = create_item(session, item)

    assert created.id is not None
    assert created.owner_id == owner.id


def test_list_items_by_owner_id_filters_by_owner(session):
    owner = create_user(
        session,
        User(username="owner2", email="owner2@example.com", hashed_password="hashed"),
    )
    other = create_user(
        session,
        User(username="other", email="other@example.com", hashed_password="hashed"),
    )
    assert owner.id is not None
    assert other.id is not None
    create_item(session, Item(title="Mine", owner_id=owner.id))
    create_item(session, Item(title="Theirs", owner_id=other.id))

    items = list_items_by_owner_id(session, owner.id)

    assert len(items) == 1
    assert items[0].title == "Mine"
