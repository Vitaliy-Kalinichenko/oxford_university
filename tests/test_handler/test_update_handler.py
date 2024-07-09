import json
import uuid

import pytest
from fastapi import status
from starlette.testclient import TestClient

from tests.conftest import User


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
    assert resp.status_code == status.HTTP_200_OK
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


async def test_update_user_id_validation_error(client: TestClient):
    user_data_updated = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
    }
    resp = client.patch("/user/?user_id=123", data=json.dumps(user_data_updated))
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


async def test_update_user_not_found_error(client: TestClient):
    user_data_updated = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
    }
    user_id = uuid.uuid4()
    resp = client.patch(f"/user/?user_id={user_id}", data=json.dumps(user_data_updated))
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    resp_data = resp.json()
    assert resp_data == {"detail": f"User with id {user_id} not found."}