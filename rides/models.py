from typing import Annotated, Union
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
from datetime import datetime

class Passenger(BaseModel):
    id: str = Field(None)
    user_id: str = Field(None)
    ride_id: str = Field(None)
    no_seats: int = Field(...)
    price: float = Field(None)

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "no_seats": 2
            }
        }


class Ride(BaseModel):
    id: str = Field(None)
    date: datetime.date = Field(...)
    time: datetime.time = Field(...)
    from_location: str = Field(...)
    to_location: str = Field(...)
    pickup_location: str = Field(...)
    dropoff_location: str = Field(...)
    gender: str = Field(...)
    seats: int = Field(...)
    seat_price: float = Field(...)
    car_id: str = Field(...)
    driver_id: str = Field(None)
    expired: bool = False   
    available_seats: int = Field(None)

    passengers: List[Passenger] = Field(default=[])

    
    class Config:
        datetime_exp = datetime(year=2023, month=10, day=1, hour=18, minute=28)
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "date": datetime_exp.date(),
                "time": datetime_exp.time(),
                "from_location": "kano",
                "to_location": "dutse",
                "pickup_location": "zaria road",
                "dropoff_location": "investment",
                "gender": "any",
                "seats": 4,
                "car_id": "6505ff80e9af984125dc51ac",
                "seat_price": 4000.00,
            }
        }

    def encode(self):
        return {
                "id": self.id,
                "date": self.date,
                "time": self.time,
                "from_location": self.from_location,
                "to_location": self.to_location,
                "gender": self.gender,
                "pickup_location": self.pickup_location,
                "dropoff_location": self.dropoff_location,
                "seats": self.seats,
                "seat_price": self.seat_price,
                "driver_id": self.driver_id,
                "car_id": self.car_id,
                "expired": self.expired,  
                "available_seats": self.available_seats,

                "passengers": self.passengers
        }