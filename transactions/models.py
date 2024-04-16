from typing import Annotated, Union
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
from datetime import datetime


class Transaction(BaseModel):

    id: str = Field(None)
    userid: str = Field(None)
    message: str = Field(...)
    amount: float = Field(...)
    timestamp: datetime = Field(...)
    status: str = Field(...)
    name: str = Field(None)
    seats: int = Field(...)
    trxn_referenceid: str = Field(...)
    transactionid: str = Field(...)
    
    
    
    
    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "message": "Approved",
                "amount": 10000.00,
                "status": "success",
                "name": "Test User",
                "seats": 2,
                "timestamp": datetime.now(),
                "trxn_referenceid": "1712408531164",
                "transactionid":   "3691543628"
            }
        }
        
        
        