from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from typing import Annotated
from bson import ObjectId

from .models import UserModel, TokenData, Token, UserLoginModel, UpdateUserModel
from .dependencies import *
from .utils import (
                        authenticate_user, 
                        get_current_active_user, 
                        get_current_user, 
                        get_password_hash, 
                        get_user,
                        create_access_token,
                        filter_none_and_empty_fields,
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
    #user.is_active = True 
    # more error handling here pls
    user_enc = jsonable_encoder(user)
    new_user = await mongoDB["users"].insert_one(user_enc)
    created_user = await mongoDB["users"].find_one({"_id": new_user.inserted_id})
    created_user["_id"] = str(created_user["_id"])

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@router.put("/{userId}/update", response_description="Update User", response_model=str)
async def update_user(userId: str, user: UpdateUserModel):
    # Convert the userId to ObjectId
    user_id_object = ObjectId(userId)

    # Check if the user exists
    to_update_user = await mongoDB["users"].find_one({"_id": user_id_object})

    if to_update_user:
        # Convert the Pydantic model to a JSON serializable format
        updated_user_enc = jsonable_encoder(user)

                # Filter out None or empty fields
        filtered_update_data = filter_none_and_empty_fields(updated_user_enc)
        # Update the user document
        update_result = await mongoDB["users"].update_one({"_id": user_id_object}, {"$set": filtered_update_data})

        if update_result.modified_count == 1:
            # Document updated successfully
            return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User updated successfully"})

        # If the update didn't modify any document
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User data unchanged"})

    # User not found
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {userId} not found")

@router.get("/all", response_description="Get all Users", response_model=list[UserModel])
async def get_all_users():
    users = []

    # Retrieve all user documents from the MongoDB collection
    async for user in mongoDB["users"].find():
        users.append(user)

    return users


@router.delete("/{userId}/delete", response_description="Delete User")
async def delete_user(userId: str):
    # Convert the userId to ObjectId
    user_id_object = ObjectId(userId)

    # Check if the user exists
    to_delete_user = await mongoDB["users"].find_one({"_id": user_id_object})

    if to_delete_user:
        # Delete the user document
        await mongoDB["users"].delete_one({"_id": user_id_object})

        return {"message": f"User with ID {userId} has been deleted"}

    # User not found
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {userId} not found")


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
