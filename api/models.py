import re
from http import HTTPStatus
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import constr
from pydantic import EmailStr
from pydantic import validator

#########################
# BLOCK WITH API MODELS #
#########################


LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")


class TunedModel(BaseModel):
    class Config:
        """tells pydantic to convert even non dict obj to json"""

        orm_mode = True


class CreateUserResponse(TunedModel):
    user_id: UUID
    name: str
    surname: str
    email: EmailStr
    is_active: bool


class DeleteUserResponse(BaseModel):
    deleted_user_id: UUID


class UpdateUserResponse(BaseModel):
    updated_user_id: UUID


class GetUserResponse(TunedModel):
    user_id: UUID
    name: str
    surname: str
    email: EmailStr
    is_active: bool


class BaseUser(BaseModel):
    name: Optional[constr(min_length=1)]
    surname: Optional[constr(min_length=1)]
    email: Optional[EmailStr]

    @validator("name")
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Name should contains only letters.",
            )
        return value

    @validator("surname")
    def validate_surname(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Surname should contains only letters.",
            )
        return value

    class Config:
        extra = "forbid"


class CreateUser(BaseUser):
    name: constr(min_length=1)
    surname: constr(min_length=1)
    email: EmailStr


class UpdateUser(BaseUser):
    pass
