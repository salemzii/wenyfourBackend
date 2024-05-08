from datetime import timedelta, datetime
from typing import Annotated
from bson import ObjectId
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder

from jose import JWTError, jwt

from auth.models import UserModel
from auth.utils import filter_none_and_empty_fields, castObjectId
from driver.dependencies import get_current_user_by_jwtoken, get_token_header
from database import db as mongoDB

from .models import Transaction

router = APIRouter(
    prefix="/api/transactions",
    tags=["transactions"],
    #dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/create", response_description="create a transaction", response_model=Transaction)
async def create_transaction(tranx: Transaction, current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    
    try:
        tranx.userid = current_user.id
        tranx.name = current_user.name
        
        tranx_enc = jsonable_encoder(tranx) 
        
        new_tranx = await mongoDB["transactions"].insert_one(tranx_enc)

        tranx.id = str(new_tranx.inserted_id)
        
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(tranx))
    except Exception as e:
        print(e, )  
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "encountered error creating transaction"})


@router.get("/{userId}/transactions", response_description="Fetch all a user's transactions", response_model=Transaction)
async def fetch_transactions(userId: str, current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    try:
        transactions = []
        
        async for tranx in mongoDB["transactions"].find({"userid": userId}):
            castObjectId(tranx)
            transactions.append(tranx)
        
        return JSONResponse(status_code=status.HTTP_200_OK, content=transactions)
    except Exception as e:
        print(e, )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
    
    
@router.get("/{userId}/transactions/{transactionId}", response_description="Fetch a user transaction", response_model=Transaction)
async def fetch_transaction(userId: str, transactionId: str, current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):

    transaction = await mongoDB["transactions"].find_one({"_id": ObjectId(transactionId)})
    if transaction:
        castObjectId(transaction)
        
        return JSONResponse(status_code=status.HTTP_200_OK, content=transaction)
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "transaction not found"})
   