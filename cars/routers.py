from fastapi import APIRouter, Depends, Body, HTTPException, status, Request
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from typing import Annotated
from bson import ObjectId


from .models import Car

from auth.models import UserModel
from auth.utils import filter_none_and_empty_fields
from driver.dependencies import get_current_user_by_jwtoken, get_token_header
from database import db as mongoDB

router = APIRouter(
    prefix="/api/cars",
    tags=["cars"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/create", response_description="create a car object", response_model=Car)
async def create_car(car: Car, user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    car.user_id = user.id
    car_enc = jsonable_encoder(car)
    new_car = await mongoDB["cars"].insert_one(car_enc)
    created_car = await mongoDB["cars"].find_one({"_id": new_car.inserted_id})
    created_car["id"] = str(created_car["_id"])
    del created_car["_id"]

    return JSONResponse(content=created_car, status_code=status.HTTP_201_CREATED)


@router.put("/update/{carId}/car", response_description="update a car's information", response_model=Car)
async def update_car(carId: str, car: Car, user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    
    to_update_car = await mongoDB["cars"].find_one({"_id": ObjectId(carId)})
    if to_update_car:
        updated_car_enc = jsonable_encoder(car)
        filtered_update_data = filter_none_and_empty_fields(updated_car_enc)
        update_result = await mongoDB["cars"].update_one({"_id": ObjectId(carId)}, {"$set": filtered_update_data})

    if update_result.modified_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Car updated successfully"})
    
    return JSONResponse(status_code=status.HTTP_200_OK, content={"mesage": "Car data unchanged!"})


@router.get ("/{carId}/car", response_description="get a car by id", response_model=Car)
async def getCarById(carId: str, user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    car = await mongoDB["cars"].find_one({"_id": ObjectId(carId)})

    if car:
        car["id"] = str(car["_id"])
        del car["_id"]
        return JSONResponse(content=car, status_code=status.HTTP_200_OK)        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"car with id {carId} not found")


@router.get("/check/user/cars", response_description="check if user has any available car", response_model=Car)
async def checkUserCars(user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    uid = user.id

    car = await mongoDB["cars"].find_one({"user_id": str(uid)}) 
    if car:
        return JSONResponse(content={"status": True, "message": "user has a valid vehicle"}, status_code=status.HTTP_200_OK)
    return JSONResponse(content={"status": False, "message": "user has no valid vehicle attached to their profile"})


@router.get("/user/all", response_description="get all a user's cars", response_model=Car)
async def getUserCars(user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):

    cars = []
    async for car in mongoDB["cars"].find({"user_id": user.id}):
        car["id"] = str(car["_id"])
        del car["_id"]

        cars.append(car)
    return JSONResponse(status_code=status.HTTP_200_OK, content=cars)
    

@router.delete("/{carId}/delete", response_description="delete a car by id", response_model=Car)
async def deleteCarById(carId: str, user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    car = await mongoDB["cars"].find_one({"_id": ObjectId(carId)})

    if car:
        if car["user_id"] == user.id:
            await mongoDB["cars"].delete_one({"_id": ObjectId(carId)})

            return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "car deleted successfully"})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "user has no access to car"})
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": f"car with id: {carId} not found!"})

    