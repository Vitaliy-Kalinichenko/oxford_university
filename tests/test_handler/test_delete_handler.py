from uuid import uuid4

from fastapi import status
from starlette.testclient import TestClient

from tests.conftest import create_bad_test_auth_headers_for_user
from tests.conftest import create_sample_user
from tests.conftest import create_test_auth_headers_for_user
from tests.conftest import User


async def test_delete_user(
    client: TestClient, create_user_in_database, get_user_from_database
):
    user_data = await create_sample_user(create_user_in_database)

    resp = client.delete(
        f"/user/?user_id={user_data.user_id}",
        headers=create_test_auth_headers_for_user(user_data.email),
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"deleted_user_id": str(user_data.user_id)}
    users_from_db = await get_user_from_database(user_data.user_id)
    user_from_db: User = dict(users_from_db[0])
    assert user_from_db["name"] == user_data.name
    assert user_from_db["surname"] == user_data.surname
    assert user_from_db["email"] == user_data.email
    assert user_from_db["is_active"] is False
    assert user_from_db["user_id"] == user_data.user_id


async def test_delete_user_not_found(client: TestClient, create_user_in_database):
    user_data = await create_sample_user(create_user_in_database)
    user_id = uuid4()
    resp = client.delete(
        f"/user/?user_id={user_id}",
        headers=create_test_auth_headers_for_user(user_data.email),
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json() == {"detail": f"User with id {user_id} not found."}


async def test_delete_user_user_id_validation_error(
    client: TestClient, create_user_in_database
):
    user_data = await create_sample_user(create_user_in_database)
    resp = client.delete(
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


async def test_delete_user_no_jwt(client: TestClient, create_user_in_database):
    user_data = await create_sample_user(create_user_in_database)
    resp = client.delete(f"/user/?user_id={user_data.user_id}")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    data_from_response = resp.json()
    assert data_from_response == {"detail": "Not authenticated"}


async def test_delete_user_unauth(client: TestClient, create_user_in_database):
    user_data = await create_sample_user(create_user_in_database)
    resp = client.delete(
        f"/user/?user_id={user_data.user_id}",
        headers=create_bad_test_auth_headers_for_user(user_data.email),
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    data_from_response = resp.json()
    assert data_from_response == {"detail": "Could not validate credentials"}
