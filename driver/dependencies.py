from typing import Annotated

from fastapi import Header, HTTPException, Depends
from auth.utils import get_current_user
from database import db as mongoDB
from bson import ObjectId
from .models import DriverModel

async def get_token_header(x_token: Annotated[str, Header()]) -> tuple:
    if x_token == "" or x_token == " " or x_token == None or x_token == "Bearer" or x_token == "Bearer ":
        raise HTTPException(status_code=400, detail="X-Token header invalid")
    return x_token


async def get_current_user_by_jwtoken(x_token: Annotated[str, Header()]):
    user = await get_current_user(token=x_token)
    if user:
        return user
    return None

async def driver_is_verified(driver_id: str):
    driver = await mongoDB["drivers"].find_one({"_id": ObjectId(driver_id)})

    if driver:
        del driver["_id"]

        driver_model = DriverModel(**driver)
        driver_model.id = driver_id

        return driver_model.is_verified
    return False

async def get_query_token(token: str):
    if token != "jessica":
        raise HTTPException(status_code=400, detail="No Jessica token provided")
