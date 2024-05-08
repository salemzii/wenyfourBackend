from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, JSONResponse
from datetime import datetime, timedelta
from typing import Annotated, List
from bson import ObjectId

from .models import Ride, Passenger
from database import db as mongoDB
from auth.models import UserModel
from auth.utils import filter_none_and_empty_fields, castObjectId
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


@router.post("/create", response_description="create a ride", response_model=Ride)
async def create_ride(ride: Ride, user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    
    if user.is_active:
        ride.driver_id = user.id
        ride.available_seats = ride.seats
        ride.from_location = ride.from_location.lower()
        ride.to_location = ride.to_location.lower()

        ride.dropoff_location = ride.dropoff_location.lower()
        ride.pickup_location = ride.pickup_location.lower()

        ride_data = jsonable_encoder(ride)

        # Insert the ride data into the MongoDB collection
        result = await mongoDB["rides"].insert_one(ride_data)

        ride.id = str(result.inserted_id)

        return JSONResponse(status_code=status.HTTP_201_CREATED, content=ride.encode())
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "encountered error creating ride, driver not verified"})


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
        booked_rides = []
        async for ride in mongoDB["rides"].find():
            try: 
                castObjectId(ride)
                ridemodel = Ride(**ride)
                del ride["passengers"]

                for passenger in ridemodel.passengers:
                    
                    if userId == passenger.user_id:
                    

                        car_obj = await mongoDB["cars"].find_one({"_id": ObjectId(ridemodel.car_id)})
                        driver_obj = await mongoDB["users"].find_one({"_id": ObjectId(ridemodel.driver_id)})
                        
                        if car_obj:
                            ride["car_model"] = car_obj["model"]
                            ride["car_color"] = car_obj["color"]
                            ride["car_type"] = car_obj["c_type"]
                        if driver_obj:
                            ride["driver_name"] = driver_obj["name"]
                            ride["driver_phone"] = driver_obj["phone"]

                            
                        booked_rides.append(ride)
            except Exception as err:
                raise err
        return JSONResponse(status_code=status.HTTP_200_OK, content=booked_rides)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "credential errors, different uid and cuid"})


async def SetExpiredRides(ride_ids: List[ObjectId]):
    
    update_data = {"expired": True}
    
    res = await mongoDB['rides'].update_many(
        {'_id': {'$in': ride_ids}},
        {'$set': update_data}
    )
    
    print(res.modified_count)


@router.get("/published/rides", response_description="find all rides published by a driver", response_model=Ride)
async def get_published_rides(current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)], background_tasks: BackgroundTasks):
    
    rides = []
    expired_rides_ls = []
    
    async for ride in mongoDB["rides"].find({"driver_id": current_user.id}):
        if not ride["expired"]:
            ride["id"] = str(ride["_id"])
            del ride["_id"]

            rides.append(ride)
        else:
            expired_rides_ls.append(ride["_id"])
            
    try:
        background_tasks.add_task(SetExpiredRides, expired_rides_ls)
    except Exception as err:
        print(err, )
    
    return JSONResponse(status_code=status.HTTP_200_OK, content=rides)




@router.get("/q/search/ride", response_description="search for a ride", response_model=Ride)
async def search_rides(current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)], 
                        background_tasks: BackgroundTasks, start_loc: Annotated[str, Query(max_length=50)] = None,
                        to_loc: Annotated[str, Query(max_length=50)] = None,
                        seats: int = None
    ):

    search_results = []
    expired_rides_ls = []

    # Create indexes on start_location and to_location
    await mongoDB["rides"].create_index([("from_location", 1)])  # 1 for ascending order
    await mongoDB["rides"].create_index([("to_location", 1)])


    # Perform the search query
    async for ride in mongoDB["rides"].find({"from_location": start_loc.lower(), "to_location": to_loc.lower()}):
        castObjectId(ride)

        date_format = "%Y-%d-%m %H:%M" #:%S "%Y-%m-%d %H:%M:%S.%f"
        ride_datetime_str = f"{ride['date']} {ride['time']}"

        try:
            # parse the string into a datetime object
            dt_obj = datetime.strptime(ride_datetime_str, date_format)
        except ValueError as e:
            print(f"datetime parsing error: {e}")
            continue

        if not ride["expired"]:            
            # Format the current date and time in the desired format (year-day-month hour:minute)
            formatted_datetime = datetime.strptime(datetime.now().strftime(date_format), date_format)

            
            
            if dt_obj.__gt__(formatted_datetime):
                if ride["available_seats"] >= seats and not(ride["driver_id"] == current_user.id):
                    car_obj = await mongoDB["cars"].find_one({"_id": ObjectId(ride["car_id"])})
                    if car_obj:
                        ride["car_model"] = car_obj["model"]
                        ride["car_color"] = car_obj["color"]
                        ride["car_type"] = car_obj["c_type"]
                    
                    driver_obj = await mongoDB["users"].find_one({"_id": ObjectId(ride["driver_id"])})
                    if driver_obj:
                        ride["driver_name"] = driver_obj["name"]
                        ride["driver_phone"] = driver_obj["phone"]

                    if await NoPassengerIsCurrentUser(ride["passengers"], current_user.id):
                        del ride["passengers"]
                        search_results.append(ride)

            else:
                print(ride["id"])
                expired_rides_ls.append(ObjectId(ride["id"]))
 
    try:
        background_tasks.add_task(SetExpiredRides, expired_rides_ls)
    except Exception as err:
        print(err, )
        
    return JSONResponse(status_code=status.HTTP_200_OK, content=search_results)




async def NoPassengerIsCurrentUser(passengers: List, cuid: str):
    for passenger in passengers:
        if str(cuid) == str(passenger["user_id"]):
            return False
    return True


@router.get("/all", response_description="fetch all rides", response_model=Ride)
async def all_rides(current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    rides = []
    async for ride in mongoDB["rides"].find():
        ride["id"] = str(ride["_id"])
        del ride["_id"]

        rides.append(ride)
    return JSONResponse(status_code=status.HTTP_200_OK, content=rides)


@router.delete("/delete/{rideId}", response_description="delete a particular ride", response_model=Ride)
async def delete_ride(rideId: str, current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    deleted = await mongoDB["rides"].delete_one({"_id": ObjectId(rideId)})
    if deleted:
        return JSONResponse(content={"msg": "ride deleted successfully"}, status_code=status.HTTP_200_OK)
    return JSONResponse(content={"error": ""})


