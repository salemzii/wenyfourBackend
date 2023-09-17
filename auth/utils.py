from datetime import datetime, timedelta
from typing import Annotated, Union, Union
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import smtplib
import os


from .models import UserModel, TokenData, UserLoginModel
from database import db as mongoDB

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

BaseUrl = os.environ["BASE_PATH"]


class UserInDB(UserModel):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/users/login")
oauth2_password_request_form = UserLoginModel


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(db, email: str) -> UserModel:
    user = await db["users"].find_one({"email": email})

    if user:
        user["id"] = str(user["_id"])
        uM = UserModel(**user)
        return uM
    return None
 

async def authenticate_user(db, username: str, password: str):
    user = await get_user(db, username)

    if not user:
        return False
    if not verify_password(password, user.password) or not user.is_active:
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = await get_user(db=mongoDB, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def filter_none_and_empty_fields(update_data):
    # Filter out fields with values of None or an empty string
    return {key: value for key, value in update_data.items() if value is not None and value != ""}



def sendmail(subject, body, to):

    gmail_user = os.environ["MAIL_USER"]
    gmail_password = os.environ["MAIL_PASSWORD"]

    sent_from = gmail_user
    to = to
    subject = subject
    body = body
    mailTo = None

    email_text = body

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print('Email sent!')
    except:
        print('Something went wrong...')


def SendAccountVerificationMail(userid, name, to):
    access_token = create_access_token(
        data={"sub": to, "uid": userid}, expires_delta=timedelta(minutes=60)
    )
    subject = "Verify your account"

    verificationLink = f"{BaseUrl}/{userid}/verify?token={access_token}"

    body = f"""Hello {name} \nThanks for signing up to our platform, we are thrilled to have you with us. 
                \n Kindly click the following link {verificationLink} to verify you account.\ncheers"""

    sendmail(subject=subject, body=body, to=to)

