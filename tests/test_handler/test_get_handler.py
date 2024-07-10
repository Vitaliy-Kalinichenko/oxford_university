from uuid import uuid4

from fastapi import status
from starlette.testclient import TestClient

from tests.conftest import User


async def test_get_user_by_id(
    client: TestClient, create_user_in_database, get_user_from_database
):
    user_id = uuid4()
    user_data: User = {
        "user_id": user_id,
        "name": "Boba",
        "surname": "Bobenko",
        "email": "boba@boba.com",
        "is_active": True,
    }
    await create_user_in_database(**user_data)
    resp = client.get(f"/user/?user_id={user_id}")
    assert resp.status_code == status.HTTP_200_OK
    users_from_resp = resp.json()
    assert users_from_resp["name"] == user_data["name"]
    assert users_from_resp["surname"] == user_data["surname"]
    assert users_from_resp["email"] == user_data["email"]
    assert users_from_resp["is_active"] is True
    assert users_from_resp["user_id"] == str(user_id)


async def test_get_user_id_validation_error(
    client: TestClient, create_user_in_database, get_user_from_database
):
    user_data: User = {
        "user_id": uuid4(),
        "name": "Boba",
        "surname": "Bobenko",
        "email": "boba@boba.com",
        "is_active": True,
    }
    await create_user_in_database(**user_data)
    resp = client.get("/user/?user_id=123")
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data_from_response = resp.json()
    assert data_from_response == {
        "detail": [
            {
                "loc": ["query", "user_id"],
                "msg": "value is not a valid uuid",
                "type": "type_error.uuid",
            }
        ]
    }


async def test_get_user_not_found(
    client: TestClient, create_user_in_database, get_user_from_database
):
    user_data: User = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "is_active": True,
    }
    user_id_for_finding = uuid4()
    await create_user_in_database(**user_data)
    resp = client.get(f"/user/?user_id={user_id_for_finding}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json() == {"detail": f"User with id {user_id_for_finding} not found."}
