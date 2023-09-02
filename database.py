import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv("../.env")
#os.environ["MONGODB_URL"]
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.wenyfour
