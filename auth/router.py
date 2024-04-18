from datetime import timedelta, datetime
from typing import Annotated
from bson import ObjectId
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder

from jose import JWTError, jwt

from driver.dependencies import get_current_user_by_jwtoken
from database import db as mongoDB

from .models import UserModel, UserLoginModel, UpdateUserModel, ContactUs, Support, PasswordResetModel, ForgotPasswordResetModel, AddEmailModel
from .exceptions import contactus_exception, support_exception
from .dependencies import *
from .utils import (
                        authenticate_user, 
                        get_current_active_user, 
                        get_current_user, 
                        get_password_hash, 
                        get_user,
                        verify_password,
                        create_access_token,
                        SendPasswordResetMail,
                        filter_none_and_empty_fields,
                        ACCESS_TOKEN_EXPIRE_MINUTES,
                        ALGORITHM, 
                        SECRET_KEY,
                        SendAccountVerificationMail,
                        castObjectId,
                        sendmail,
                        cloudinary
                )




router = APIRouter(
    prefix="/api/auth/users",
    tags=["users"],
    #dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/create", response_description="Add new user", response_model=UserModel)
async def create_user(user: UserModel):

    check_mail = await mongoDB["users"].find_one({"email": user.email})
    # more error handling here pls

    if not check_mail:
        hashed_password = get_password_hash(password=user.password)
        user.password = hashed_password

        user.created_at = datetime.now()
        user.updated_at = datetime.now()
        user_enc = jsonable_encoder(user)
        new_user = await mongoDB["users"].insert_one(user_enc)
        created_user = await mongoDB["users"].find_one({"_id": new_user.inserted_id})
        created_user["_id"] = str(created_user["_id"])

        SendAccountVerificationMail(userid=created_user["_id"], name=user.name, to=user.email)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user with the mail already exists")


@router.get("/me", response_description="fetch logged In user", response_model=UserModel)
async def get_loggedin_user(user:Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    if user:
        user.id = str(user.id)
        user_enc = jsonable_encoder(user)
        return JSONResponse(status_code=200, content=user_enc)
    return JSONResponse(status_code=404, content={"error": "user not logged in"})


@router.get("/{userId}/user", response_description="get user by Id", response_model=UserModel)
async def get_user_by_Id(userId: str, user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    # Convert the userId to ObjectId
    user_id_object = ObjectId(userId)

    # Check if the user exists
    _user = await mongoDB["users"].find_one({"_id": user_id_object})    

    if _user:
        castObjectId(_user)
        user_enc = jsonable_encoder(_user)
        return JSONResponse(status_code=200, content=user_enc)
    return JSONResponse(status_code=404, content={"error": f"user with Id={userId} not found"})        


@router.put("/{userId}/update", response_description="Update User", response_model=str)
async def update_user(userId: str, user: UpdateUserModel, c_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
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
async def get_all_users(user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    users = []

    # Retrieve all user documents from the MongoDB collection
    async for user in mongoDB["users"].find():
        castObjectId(user)
        users.append(user)

    return JSONResponse(status_code=status.HTTP_200_OK, content=users)


@router.delete("/{userId}/delete", response_description="Delete User")
async def delete_user(userId: str, user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
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


@router.post("/login")
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
    return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "user_id": user.id, 
            "name": user.name, 
            "email": user.email
        }


@router.get("/me", response_model=UserModel)
async def read_users_me(
    current_user: Annotated[str, Depends(get_current_active_user)]
):
    return current_user


@router.get("/{userId}/verify", response_description="verify a user's email")
async def verifyAccount(userId: str, token: Annotated[str, Query] = None):


    html_content = """
        <html>
            <head>
                <title>verify your email</title>
            </head>
            <body>
                <h1>Account verified successfully</h1>
            </body>
        </html>
    """

    html_content_err = """
        <html>
            <head>
                <title>verify your email</title>
            </head>
            <body>
                <h1>Could not validate your token!</h1>
            </body>
        </html>
    """

    user = await mongoDB["users"].find_one({"_id": ObjectId(userId)})

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate your token",
    )

    if user:
        user["id"] = str(user["_id"])
        print(user)
        uM = UserModel(**user)

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return HTMLResponse(content=html_content_err, status_code=400)

        except JWTError:
            return HTMLResponse(content=html_content_err, status_code=400)

        uM.is_active = True

        user_enc = jsonable_encoder(uM)

                # Filter out None or empty fields
        filtered_update_data = filter_none_and_empty_fields(user_enc)
        # Update the user document
        update_result = await mongoDB["users"].update_one({"_id": ObjectId(userId)}, {"$set": filtered_update_data})

        if update_result.modified_count == 1:
            return RedirectResponse("https://app.wenyfour.com/auth")
        return HTMLResponse(content=html_content_err, status_code=400)
    

@router.post("/reset/password", response_description="Reset Password")
async def resetPassword(password: PasswordResetModel, 
            current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):
    if current_user:
        if verify_password(password.password, current_user.password):
            new_password = get_password_hash(password=password.new_password)
            # Update the user document
            update_result = await mongoDB["users"].update_one({"_id": ObjectId(current_user.id)}, {"$set": {"password": new_password}})

            if update_result.modified_count == 1:
                # Document updated successfully
                return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User password updated successfully"})

            # If the update didn't modify any document
            return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User data unchanged"})            
    raise credentials_exception



@router.post("/forgot/password", response_description="add email for forget password")
async def addForgetPasswordMail(email: AddEmailModel):
    if email:
        usermodel = await get_user(db=mongoDB, email=email.email)
        if usermodel:
            SendPasswordResetMail(userid=usermodel.id, name=usermodel.name, to=email.email)
            return JSONResponse(content={"message": "email sent successfully"}, status_code=status.HTTP_200_OK)
    return JSONResponse(content={"error": "user with mail does not exists"}, status_code=status.HTTP_400_BAD_REQUEST)


@router.get("/{userId}/reset", response_description="reset a user's forgotten password")
async def resetAccountpswd(userId: str, token: Annotated[str, Query] = None):
    user = await mongoDB["users"].find_one({"_id": ObjectId(userId)})
    
    html_content_err = """
        <html>
            <head>
                <title>verify your email</title>
            </head>
            <body>
                <h1>Could not validate your token!</h1>
            </body>
        </html>
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate your token",
    )

    if user:
        user["id"] = str(user["_id"])
        print(user)
        uM = UserModel(**user)

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return HTMLResponse(content=html_content_err, status_code=400)

        except JWTError:
            return HTMLResponse(content=html_content_err, status_code=400)
        
    return RedirectResponse("https://app.wenyfour.com/reset")

@router.post("/forgot/password/reset", response_description="reset a user's password after forgetting password")
async def forgetPasswordReset(pswdmodel: ForgotPasswordResetModel):
    if pswdmodel: 
        new_password = get_password_hash(password=pswdmodel.password)
        # Update the user document
        update_result = await mongoDB["users"].update_one({"email": pswdmodel.email}, {"$set": {"password": new_password}})

        if update_result.modified_count == 1:
            # Document updated successfully
            return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User password updated successfully"})

        # If the update didn't modify any document
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User data unchanged"})            
    raise credentials_exception



@router.post("/contact/us", response_description="contact us")
async def contactUs(contactus: ContactUs):
    contactus_enc = jsonable_encoder(contactus)
    new_contactus = await mongoDB["contactus"].insert_one(contactus_enc)
    created_contactus = await mongoDB["contactus"].find_one({"_id": new_contactus.inserted_id})

    if created_contactus:
        mail_rep = os.environ["MAIL_R"]
        try:
            sendmail(subject=contactus.subject, body=contactus.message, to=mail_rep)
        except Exception as err:
            print(err, )
        return JSONResponse(content={"message": "successfully created"}, status_code=status.HTTP_201_CREATED)
    raise contactus_exception


@router.post("/support", response_description="contact support")
async def support(support: Support):
    support_enc = jsonable_encoder(support)
    new_support = await mongoDB["support"].insert_one(support_enc)
    created_support = await mongoDB["support"].find_one({"_id": new_support.inserted_id})

    if created_support:
        mail_rep = os.environ["MAIL_R"]
        try:
            sendmail(subject=support.subject, body=support.body, to=mail_rep)
        except Exception as err:
            print(err, )
        return JSONResponse(content={"message": "successfully created"}, status_code=status.HTTP_201_CREATED)
    raise support_exception




@router.post("/upload/profile/picture", response_description="upload a user's profile picture")
async def uploadProfilePicture(picture: Annotated[UploadFile, File()], current_user: Annotated[UserModel, Depends(get_current_user_by_jwtoken)]):

    try:
        # Upload the file to Cloudinary
        upload_result = cloudinary.uploader.upload(picture.file)

        # You can access the Cloudinary URL for the uploaded file
        file_url = upload_result['secure_url']

        user = await mongoDB["users"].find_one({"_id": ObjectId(current_user.id)})
        if user:
            updated_user = await mongoDB["users"].update_one({"_id": ObjectId(current_user.id)}, {"$set": {"picture": file_url}})
            if updated_user.modified_count == 1:
                return JSONResponse(content={"message": "profile picture uploaded successfully!", "url": file_url}, status_code=status.HTTP_200_OK)
            return JSONResponse(content={"error": "error updating profile picture"}, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
