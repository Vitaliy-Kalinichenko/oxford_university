from logging import getLogger
from typing import Union
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import CreateUser
from api.models import CreateUserResponse
from api.models import DeleteUserResponse
from api.models import GetUserResponse
from api.models import UpdateUser
from api.models import UpdateUserResponse
from db.dals import UserDAL
from db.models import User
from db.session import get_db

logger = getLogger(__name__)

user_router = APIRouter()


async def _create_new_user(body: CreateUser, db) -> CreateUserResponse:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.create_user(
                name=body.name,
                surname=body.surname,
                email=body.email,
            )
            return CreateUserResponse(
                user_id=user.user_id,
                name=user.name,
                surname=user.surname,
                email=user.email,
                is_active=user.is_active,
            )


async def _delete_user(user_id: UUID, db) -> Union[UUID, None]:
    async with db as session, session.begin():
        user_dal = UserDAL(session)
        return await user_dal.delete_user(user_id=user_id)


async def _get_user_by_id(user_id: UUID, db) -> Union[User, None]:
    async with db as session, session.begin():
        user_dal = UserDAL(session)
        return await user_dal.get_user_by_id(user_id=user_id)


async def _update_user(user_id: UUID, body: UpdateUser, db) -> Union[UUID, None]:
    async with db as session, session.begin():
        user_dal = UserDAL(session)
        return await user_dal.update_user(user_id=user_id, **body)


@user_router.post("/", response_model=CreateUserResponse)
async def create_user(
    body: CreateUser, db: AsyncSession = Depends(get_db)
) -> CreateUserResponse:
    try:
        return await _create_new_user(body, db)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {err}",
        )


@user_router.delete("/", response_model=DeleteUserResponse)
async def delete_user(
    user_id: UUID, db: AsyncSession = Depends(get_db)
) -> DeleteUserResponse:
    deleted_user_id = await _delete_user(user_id, db)
    if deleted_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )
    return DeleteUserResponse(deleted_user_id=deleted_user_id)


@user_router.get("/", response_model=GetUserResponse)
async def get_user_by_id(
    user_id: UUID, db: AsyncSession = Depends(get_db)
) -> GetUserResponse:
    user = await _get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )
    return GetUserResponse(
        user_id=user.user_id,
        name=user.name,
        surname=user.surname,
        email=user.email,
        is_active=user.is_active,
    )


@user_router.patch("/", response_model=UpdateUserResponse)
async def update_user(
    user_id: UUID, body: UpdateUser, db: AsyncSession = Depends(get_db)
) -> UpdateUserResponse:
    body = body.dict(exclude_none=True)
    if not body:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one parameter for user update info should be provided.",
        )
    try:
        updated_user_id = await _update_user(user_id, body, db)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {err}",
        )
    if updated_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )
    return UpdateUserResponse(updated_user_id=updated_user_id)
