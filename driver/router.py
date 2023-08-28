from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from typing import Annotated
from bson import ObjectId

from .models import DriverModel
from database import db as mongoDB

router = APIRouter(
    prefix="/api/drivers",
    tags=["drivers"],
    #dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/create", response_description="add a driver profile", response_model=DriverModel)
async def create_driver(driver: DriverModel):

    driver_data = driver.dict()
    # Insert the driver data into the MongoDB collection
    result = await mongoDB["drivers"].insert_one(driver_data)

    # Assign the generated ObjectId to the driver's "id" field
    driver.id = result.inserted_id

    return driver