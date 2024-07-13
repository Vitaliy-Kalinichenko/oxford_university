from typing import Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.models import CreateUser
from api.models import CreateUserResponse
from api.models import UpdateUser
from db.dals import UserDAL
from db.models import User
from hashing import Hasher


async def _create_new_user(
    body: CreateUser, session: AsyncSession
) -> CreateUserResponse:
    async with session.begin():
        user_dal = UserDAL(session)
        user = await user_dal.create_user(
            name=body.name,
            surname=body.surname,
            email=body.email,
            hashed_password=Hasher.get_password_hash(body.password),
        )
        return CreateUserResponse(
            user_id=user.user_id,
            name=user.name,
            surname=user.surname,
            email=user.email,
            is_active=user.is_active,
        )


async def _delete_user(user_id: UUID, session: AsyncSession) -> Union[UUID, None]:
    async with session.begin():
        user_dal = UserDAL(session)
        return await user_dal.delete_user(user_id=user_id)


async def _get_user_by_id(user_id: UUID, session: AsyncSession) -> Union[User, None]:
    async with session.begin():
        user_dal = UserDAL(session)
        return await user_dal.get_user_by_id(user_id=user_id)


async def _update_user(
    user_id: UUID, body: UpdateUser, session: AsyncSession
) -> Union[UUID, None]:
    async with session.begin():
        user_dal = UserDAL(session)
        return await user_dal.update_user(user_id=user_id, **body)
