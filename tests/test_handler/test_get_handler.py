from uuid import uuid4

from fastapi import status
from starlette.testclient import TestClient

from tests.conftest import create_bad_test_auth_headers_for_user
from tests.conftest import create_sample_user
from tests.conftest import create_test_auth_headers_for_user


async def test_get_user_by_id(
    client: TestClient, create_user_in_database, get_user_from_database
):
    user_data = await create_sample_user(create_user_in_database)
    resp = client.get(
        f"/user/?user_id={user_data.user_id}",
        headers=create_test_auth_headers_for_user(user_data.email),
    )
    assert resp.status_code == status.HTTP_200_OK
    users_from_resp = resp.json()
    assert users_from_resp["name"] == user_data.name
    assert users_from_resp["surname"] == user_data.surname
    assert users_from_resp["email"] == user_data.email
    assert users_from_resp["is_active"] is True
    assert users_from_resp["user_id"] == str(user_data.user_id)


async def test_get_user_id_validation_error(
    client: TestClient, create_user_in_database, get_user_from_database
):
    user_data = await create_sample_user(create_user_in_database)
    resp = client.get(
        "/user/?user_id=123", headers=create_test_auth_headers_for_user(user_data.email)
    )
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
    user_data = await create_sample_user(create_user_in_database)
    user_id_for_finding = uuid4()
    resp = client.get(
        f"/user/?user_id={user_id_for_finding}",
        headers=create_test_auth_headers_for_user(user_data.email),
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json() == {"detail": f"User with id {user_id_for_finding} not found."}


async def test_get_user_no_jwt(client: TestClient, create_user_in_database):
    user_data = await create_sample_user(create_user_in_database)
    resp = client.get(f"/user/?user_id={user_data.user_id}")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    data_from_response = resp.json()
    assert data_from_response == {"detail": "Not authenticated"}


async def test_get_user_unauth(client: TestClient, create_user_in_database):
    user_data = await create_sample_user(create_user_in_database)
    resp = client.get(
        f"/user/?user_id={user_data.user_id}",
        headers=create_bad_test_auth_headers_for_user(user_data.email),
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    data_from_response = resp.json()
    assert data_from_response == {"detail": "Could not validate credentials"}
