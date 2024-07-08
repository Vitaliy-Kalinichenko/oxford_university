import json
import uuid
from http import HTTPStatus
from typing import TypedDict

import pytest
from starlette.testclient import TestClient


class User(TypedDict):
    user_id: uuid.UUID
    name: str
    surname: str
    email: str
    is_active: bool


async def test_create_user(client: TestClient, get_user_from_database):
    user_data = {
        "name": "Vitalii",
        "surname": "Kalinichenko",
        "email": "boba@boba.com",
    }
    resp = client.post("/user/", data=json.dumps(user_data))
    data_from_resp: User = resp.json()
    assert resp.status_code == HTTPStatus.OK
    assert data_from_resp["name"] == user_data["name"]
    assert data_from_resp["surname"] == user_data["surname"]
    assert data_from_resp["email"] == user_data["email"]
    assert data_from_resp["is_active"] is True
    user_from_db = await get_user_from_database(data_from_resp["user_id"])
    assert len(user_from_db) == 1
    user_from_db: User = dict(user_from_db[0])
    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["is_active"] is True
    assert str(user_from_db["user_id"]) == data_from_resp["user_id"]


async def test_delete_user(
    client: TestClient, create_user_in_database, get_user_from_database
):
    user_id = uuid.uuid4()
    user_data: User = {
        "user_id": user_id,
        "name": "Vitalii",
        "surname": "Kalinichenko",
        "email": "boba@boba.com",
        "is_active": True,
    }
    await create_user_in_database(**user_data)
    resp = client.delete(f"/user/?user_id={user_id}")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"deleted_user_id": str(user_id)}
    users_from_db = await get_user_from_database(user_id)
    user_from_db: User = dict(users_from_db[0])
    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["is_active"] is False
    assert user_from_db["user_id"] == user_id


async def test_get_user_by_id(
    client: TestClient, create_user_in_database, get_user_from_database
):
    user_id = uuid.uuid4()
    user_data: User = {
        "user_id": user_id,
        "name": "Vitalii",
        "surname": "Kalinichenko",
        "email": "boba@boba.com",
        "is_active": True,
    }
    await create_user_in_database(**user_data)
    resp = client.get(f"/user/?user_id={user_id}")
    assert resp.status_code == HTTPStatus.OK
    users_from_resp = resp.json()
    assert users_from_resp["name"] == user_data["name"]
    assert users_from_resp["surname"] == user_data["surname"]
    assert users_from_resp["email"] == user_data["email"]
    assert users_from_resp["is_active"] is True
    assert users_from_resp["user_id"] == str(user_id)


async def test_update_user(
    client: TestClient, create_user_in_database, get_user_from_database
):
    user_id_for_update = uuid.uuid4()
    user_data_for_update: User = {
        "user_id": user_id_for_update,
        "name": "Ivan",
        "surname": "Ivanenko",
        "email": "iva@boba.com",
        "is_active": True,
    }
    user_id_not_for_update = uuid.uuid4()
    user_data_not_for_update: User = {
        "user_id": user_id_not_for_update,
        "name": "Vitalii",
        "surname": "Kalinichenko",
        "email": "boba@boba.com",
        "is_active": True,
    }
    user_data_updated = {
        "name": "Petro",
        "surname": "Petrenko",
        "email": "pet@boba.com",
    }
    await create_user_in_database(**user_data_for_update)
    await create_user_in_database(**user_data_not_for_update)
    resp = client.patch(
        f"/user/?user_id={user_id_for_update}", data=json.dumps(user_data_updated)
    )
    data_from_resp = resp.json()
    assert resp.status_code == HTTPStatus.OK
    assert data_from_resp["updated_user_id"] == str(user_id_for_update)

    #  check updated user
    users_from_db = await get_user_from_database(user_id_for_update)
    updated_user_from_db: User = dict(users_from_db[0])
    assert updated_user_from_db["user_id"] == user_id_for_update
    assert updated_user_from_db["name"] == user_data_updated["name"]
    assert updated_user_from_db["surname"] == user_data_updated["surname"]
    assert updated_user_from_db["email"] == user_data_updated["email"]
    assert updated_user_from_db["is_active"] is True

    #  check not updated user
    users_from_db = await get_user_from_database(user_id_not_for_update)
    not_updated_user_from_db: User = dict(users_from_db[0])
    assert not_updated_user_from_db["user_id"] == user_id_not_for_update
    assert not_updated_user_from_db["name"] == user_data_not_for_update["name"]
    assert not_updated_user_from_db["surname"] == user_data_not_for_update["surname"]
    assert not_updated_user_from_db["email"] == user_data_not_for_update["email"]
    assert not_updated_user_from_db["is_active"] is True


@pytest.mark.parametrize(
    "user_data_updated, expected_status_code, expected_status_detail",
    [
        (
            {},
            422,
            {
                "detail": "At least one parameter for user update info should be provided."
            },
        ),
        (
            {
                "123": "123",
            },
            422,
            {
                "detail": [
                    {
                        "loc": ["body", "123"],
                        "msg": "extra fields not permitted",
                        "type": "value_error.extra",
                    }
                ]
            },
        ),
        (
            {
                "name": "",
            },
            422,
            {
                "detail": [
                    {
                        "loc": ["body", "name"],
                        "msg": "ensure this value has at least 1 characters",
                        "type": "value_error.any_str.min_length",
                        "ctx": {"limit_value": 1},
                    }
                ]
            },
        ),
        (
            {
                "name": "123",
            },
            422,
            {"detail": "Name should contains only letters."},
        ),
        (
            {
                "email": "123",
            },
            422,
            {
                "detail": [
                    {
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address",
                        "type": "value_error.email",
                    }
                ]
            },
        ),
        (
            {
                "email": "",
            },
            422,
            {
                "detail": [
                    {
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address",
                        "type": "value_error.email",
                    }
                ]
            },
        ),
    ],
)
async def test_update_user_validation_error(
    client: TestClient,
    create_user_in_database,
    user_data_updated,
    expected_status_code,
    expected_status_detail,
):
    user_id = uuid.uuid4()
    user_data: User = {
        "user_id": user_id,
        "name": "Ivan",
        "surname": "Ivanenko",
        "email": "iva@boba.com",
        "is_active": True,
    }
    await create_user_in_database(**user_data)
    resp = client.patch(f"/user/?user_id={user_id}", data=json.dumps(user_data_updated))
    assert resp.status_code == expected_status_code
    data_from_resp = resp.json()
    assert data_from_resp == expected_status_detail
