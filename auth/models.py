from datetime import datetime, date
from typing import Union, Optional
from pydantic import BaseModel, Field, EmailStr

class UserModel(BaseModel):
    id: str = Field(None)
    name: str = Field(...)
    email: EmailStr = Field(...)
    phone: str = Field(...)
    nin: str = Field(...)
    date_of_birth: Optional[date] = Field(None)
    about: Optional[str] = Field(default="")
    password: str = Field(...)
    is_active: bool = False
    created_at: datetime = Field(None)
    updated_at: datetime = Field(None)

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "name": "test user",
                "email": "testuser@example.com",
                "phone": "23480904578",
                "nin": "300828566",
                "password": "auth1234",
            }
        }


class UpdateUserModel(BaseModel):
    name: Union[str, None]  = Field(None)
    email: Union[EmailStr, None]  = Field(None)
    phone: Union[str, None]  = Field(None)
    date_of_birth: date = Field(None)
    about: str = Field(default="")
    updated_at: datetime = Field(None)

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "name": "updatedtest user",
                "email": "updatedtestuser@example.com",
                "phone": "23480904578",
                "date_of_birth": "2000-08-17 00:00",
                "about": "i am a wenyfour driver"
            }
        }  

class ContactUs(BaseModel):
    id: str = Field(None)
    fullname: str = Field(...)
    phone: str = Field(...)
    email: EmailStr = Field(...)
    message: str = Field(...)

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "fullname":  "oliver yop",
                "email": "oliver@yopmail.com",
                "phone": "907766999000",
                "message": "A test message"
            }
        } 
        
        
class Support(BaseModel):
    id: str = Field(None)
    email: EmailStr = Field(...)
    subject: str = Field(...)
    body: str = Field(...)

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "email": "oliver@yopmail.com",
                "subject": "A test subject",
                "body": "A test body"
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