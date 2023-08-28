from typing import Annotated, Union
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
from datetime import datetime


class UserModel(BaseModel):
    name: str = Field(...)
    email: EmailStr = Field(...)
    phone: str = Field(...)
    password: str = Field(...)
    is_active: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "name": "test user",
                "email": "testuser@example.com",
                "phone": "23480904578",
                "password": "auth1234",
            }
        }

class UpdateUserModel(BaseModel):
    name: Union[str, None]  = Field(None)
    email: Union[EmailStr, None]  = Field(None)
    phone: Union[str, None]  = Field(None)
    updated_at: datetime = datetime.now()

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "name": "updatedtest user",
                "email": "updatedtestuser@example.com",
                "phone": "23480904578",
            }
        }  

class UserLoginModel(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Union[EmailStr, None] = None