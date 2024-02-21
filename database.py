import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv("../.env")
#os.environ["MONGODB_URL"]
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db_name = os.environ["MONGODB_DB"]
db = client[db_name]
