from fastapi import APIRouter, Depends, Body, HTTPException, status, Request
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from typing import Annotated
from bson import ObjectId


from .models import DriverModel
from database import db as mongoDB
from .dependencies import get_token_header, get_current_user_by_jwtoken
from auth.models import UserModel

router = APIRouter(
    prefix="/api/drivers",
    tags=["drivers"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/create", response_description="add a driver profile", response_model=DriverModel)
async def create_driver(driver: DriverModel, user:Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    driver.user_id = user.id

    driver_data = driver.encode()

    print(driver_data)
    # Insert the driver data into the MongoDB collection
    result = await mongoDB["drivers"].insert_one(driver_data)

    # Assign the generated ObjectId to the driver's "id" field
    driver.id = str(result.inserted_id)

    return driver


@router.get("/{driver_id}/driver", response_description="fetch a driver profile", response_model=DriverModel)
async def get_driver_by_id(driver_id:str):
    driver = await mongoDB["drivers"].find_one({"_id": ObjectId(driver_id)})

    print(driver)
    if driver:
        del driver["_id"]
        driver["id"] = driver_id
        return JSONResponse(content=driver, status_code=200)
    # User not found
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver with ID {driver_id} not found")
