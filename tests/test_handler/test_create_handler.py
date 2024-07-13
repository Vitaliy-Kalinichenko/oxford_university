import json
import uuid

import pytest
from fastapi import status
from starlette.testclient import TestClient

from tests.conftest import User


async def create_user(client: TestClient, user_data: dict) -> User:
    resp = client.post("/user/", data=json.dumps(user_data))
    data_from_resp: User = resp.json()
    assert resp.status_code == status.HTTP_200_OK
    assert data_from_resp["name"] == user_data["name"]
    assert data_from_resp["surname"] == user_data["surname"]
    assert data_from_resp["email"] == user_data["email"]
    assert data_from_resp["is_active"] is True
    return data_from_resp


async def verify_user_in_db(
    get_user_from_database, user_data: dict, user_id: uuid.UUID
):
    user_from_db = await get_user_from_database(user_id)
    assert len(user_from_db) == 1
    user_from_db: User = dict(user_from_db[0])
    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["is_active"] is True
    assert str(user_from_db["user_id"]) == str(user_id)


async def test_create_user(client: TestClient, get_user_from_database):
    user_data = {
        "name": "Boba",
        "surname": "Bobenko",
        "email": "boba@boba.com",
        "password": "SamplePass1!",
    }
    data_from_resp = await create_user(client, user_data)
    await verify_user_in_db(
        get_user_from_database, user_data, data_from_resp["user_id"]
    )


async def test_create_user_duplicate_email_error(
    client: TestClient, get_user_from_database
):
    user_data = {
        "name": "Boba",
        "surname": "Bobenko",
        "email": "boba@boba.com",
        "password": "SamplePass1!",
    }
    data_from_resp = await create_user(client, user_data)
    await verify_user_in_db(
        get_user_from_database, user_data, data_from_resp["user_id"]
    )
    user_data_same_email = {
        "name": "Alice",
        "surname": "Wonderland",
        "email": "boba@boba.com",
        "password": "SamplePass1!",
    }
    resp = client.post("/user/", data=json.dumps(user_data_same_email))
    assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert (
        'duplicate key value violates unique constraint "users_email_key"'
        in resp.json()["detail"]
    )


@pytest.mark.parametrize(
    "user_data_for_creation, expected_status_code, expected_detail",
    [
        (
            {},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {
                "detail": [
                    {
                        "loc": ["body", "name"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                    {
                        "loc": ["body", "surname"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                    {
                        "loc": ["body", "email"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                    {
                        "loc": ["body", "password"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                ]
            },
        ),
        (
            {"name": "123", "surname": "456", "email": "789"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"detail": "Name should contains only letters."},
        ),
        (
            {"name": "Boba", "surname": "456", "email": "789"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"detail": "Surname should contains only letters."},
        ),
        (
            {"name": "Boba", "surname": "Bobenko", "email": "789"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {
                "detail": [
                    {
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address",
                        "type": "value_error.email",
                    },
                    {
                        "loc": ["body", "password"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                ]
            },
        ),
        (
            {
                "name": "Boba",
                "surname": "Bobenko",
                "email": "boba@boba.com",
                "password": "SamplePass1",
                "123": "123",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
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
                "surname": "Bobenko",
                "email": "boba@boba.com",
                "password": "SamplePass1",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
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
    ],
)
async def test_create_user_validation_error(
    client: TestClient, user_data_for_creation, expected_status_code, expected_detail
):
    resp = client.post("/user/", data=json.dumps(user_data_for_creation))
    data_from_resp = resp.json()
    assert resp.status_code == expected_status_code
    assert data_from_resp == expected_detail
