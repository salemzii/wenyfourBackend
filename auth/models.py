from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from typing import Annotated, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
from datetime import datetime
from fastapi.security import OAuth2PasswordRequestForm


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
        #json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "test user",
                "email": "testuser@example.com",
                "phone": "23480904578",
                "password": "auth1234",
            }
        }


class CustomOAuth2PasswordRequestForm(OAuth2PasswordRequestForm):
    email: EmailStr
    password: str

class UserLoginModel(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Union[EmailStr, None] = None