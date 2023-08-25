from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from typing import Annotated, Union
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .models import UserModel, TokenData, Token, UserLoginModel
from .dependencies import *
from .utils import (
                        authenticate_user, 
                        get_current_active_user, 
                        get_current_user, 
                        get_password_hash, 
                        get_user,
                        create_access_token,
                        ACCESS_TOKEN_EXPIRE_MINUTES,
                        ALGORITHM, 

                )

from database import db as mongoDB

router = APIRouter(
    prefix="/api/auth/users",
    tags=["users"],
    #dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/create", response_description="Add new user", response_model=UserModel)
async def create_user(user: UserModel):
    hashed_password = get_password_hash(password=user.password)
    user.password = hashed_password
    user.is_active = True # remove
    
    user_enc = jsonable_encoder(user)
    new_user = await mongoDB["users"].insert_one(user_enc)
    created_user = await mongoDB["users"].find_one({"_id": new_user.inserted_id})
    created_user["_id"] = str(created_user["_id"])

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@router.post("/login", response_model=Token)
async def login_for_access_token(
    userlogin: UserLoginModel
):
    user = await authenticate_user(mongoDB, userlogin.email, userlogin.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserModel)
async def read_users_me(
    current_user: Annotated[str, Depends(get_current_active_user)]
):
    return current_user

