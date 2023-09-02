from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, JSONResponse
from datetime import datetime, timedelta
from typing import Annotated, List
from bson import ObjectId

from .models import Ride, Passenger
from database import db as mongoDB
from auth.models import UserModel
from auth.utils import filter_none_and_empty_fields
from driver.models import DriverModel
from driver.dependencies import get_current_user_by_jwtoken, get_token_header

router = APIRouter(
    prefix="/api/rides",
    tags=["rides"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

# Define the sorting field and order (ascending: 1, descending: -1)
sort_field = "date"
sort_order = 1  # Ascending order


@router.post("/{driverId}/create", response_description="create a ride", response_model=Ride)
async def create_ride(driverId: str, ride: Ride):
    driver = await mongoDB["drivers"].find_one({"_id": ObjectId(driverId)})
    if driver:
        driver["id"] = driver["_id"]
        del driver["_id"]
        #driver_model = DriverModel(**driver)
        if driver["is_verified"]:
            ride.driver_id = str(driver["id"])
            ride.available_seats = ride.seats

            ride_data = jsonable_encoder(ride)

            # Insert the ride data into the MongoDB collection
            result = await mongoDB["rides"].insert_one(ride_data)

            ride.id = str(result.inserted_id)

            return JSONResponse(status_code=status.HTTP_201_CREATED, content=ride.encode())
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "encountered error creating ride, driver not verified"})
    # User not found
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver with Id: {driverId} not found")


@router.put("/{rideId}/book/ride", response_description="book a ride", response_model=Ride)
async def book_ride(rideId: str, passenger: Passenger, current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    ride = await mongoDB["rides"].find_one({"_id": ObjectId(rideId)})

    if ride:
        ride["id"] = str(ride["_id"])
        ride = Ride(**ride)

        if not(ride.expired) and current_user.is_active:

            passenger.ride_id = rideId
            passenger.user_id = current_user.id
            passenger.price = float(ride.seat_price * passenger.no_seats)

        
            passenger_data = jsonable_encoder(passenger)

            # Insert the passenger data into the MongoDB collection
            result = await mongoDB["passengers"].insert_one(passenger_data)
            passenger.id = str(result.inserted_id)

            ride.available_seats = ride.available_seats - passenger.no_seats
            ride.passengers.append(passenger)

            ride_enc = jsonable_encoder(ride)
            filtered_update_data = filter_none_and_empty_fields(ride_enc)
            
            update_result = await mongoDB["rides"].update_one({"_id": ObjectId(rideId)}, {"$set": filtered_update_data})
            
            if update_result.modified_count == 1:
                return JSONResponse(status_code=status.HTTP_200_OK, content={"message":"ride booked successfully"})
            
            return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "failed to book ride"})
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "ride has expired or user is not active"})
    # ride not found
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ride with Id: {rideId} not found")


@router.get("/{rideId}/ride", response_description="fetch a ride", response_model=Ride)
async def get_ride_by_id(rideId: str, current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    
    ride = await mongoDB["rides"].find_one({"_id": ObjectId(rideId)})
    if ride:

        ride["id"] = str(ride["_id"])
        ride = Ride(**ride)
        ride_enc = jsonable_encoder(ride)
        return JSONResponse(status_code=status.HTTP_200_OK, content=ride_enc)

    # ride not found
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ride with Id: {rideId} not found")


@router.get("/{userId}/ordered/ride", response_description="find all users ordered ride", response_model=Ride)       
async def get_ordered_ride(userId: str, current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):

    if userId == current_user.id:
    
        # Perform the aggregation query
        pipeline = [
            {
                "$match": {"user_id": userId}  # Filter passengers by user_id
            },
            {
                "$lookup": {
                    "from": "rides",      # Name of the Ride collection
                    "localField": "ride_id",
                    "foreignField": "id",
                    "as": "booked_rides"
                }
            },
            {
                "$sort": {sort_field: sort_order}
            }
        ]

        # Extract and print the booked rides
        async for result in mongoDB["passengers"].aggregate(pipeline):
            booked_rides = result.get("booked_rides", [])
        
        for ride in booked_rides:
            ride["id"] = str(ride["_id"])
            del ride["_id"]

        return JSONResponse(status_code=status.HTTP_200_OK, content=booked_rides)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "credential errors, different uid and cuid"})


@router.get("/{driverId}/published/rides", response_description="find all rides published by a driver", response_model=Ride)
async def get_published_rides(driverId: str, current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    
    rides = []
    async for ride in mongoDB["rides"].find({"driver_id": driverId}):
        ride["id"] = str(ride["_id"])
        del ride["_id"]

        rides.append(ride)
    return JSONResponse(status_code=status.HTTP_200_OK, content=rides)



@router.get("/q/search/ride", response_description="search for a ride", response_model=Ride)
async def search_rides(current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)], start_loc: Annotated[str, Query(max_length=50)] = None,
    to_loc: Annotated[str, Query(max_length=50)] = None
    ):

    search_results = []
    # Create indexes on start_location and to_location
    await mongoDB["rides"].create_index([("from_location", 1)])  # 1 for ascending order
    await mongoDB["rides"].create_index([("to_location", 1)])


    # Perform the search query
    async for ride in mongoDB["rides"].find({"from_location": start_loc, "to_location": to_loc}):
        ride["id"] = str(ride["_id"])
        del ride["_id"]

        date_format = "%Y-%m-%d %H:%M:%S" #"%Y-%m-%d %H:%M:%S.%f"
        ride_datetime_str = f"{ride['date']} {ride['time']}"

        # parse the string into a datetime object
        dt_obj = datetime.strptime(ride_datetime_str, date_format)

        if not ride["expired"] and dt_obj.__gt__(datetime.now()):
            search_results.append(ride)
        
    return JSONResponse(status_code=status.HTTP_200_OK, content=search_results)


@router.get("/all", response_description="fetch all rides", response_model=Ride)
async def all_rides(current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    rides = []
    async for ride in mongoDB["rides"].find():
        ride["id"] = str(ride["_id"])
        del ride["_id"]

        rides.append(ride)
    return JSONResponse(status_code=status.HTTP_200_OK, content=rides)

