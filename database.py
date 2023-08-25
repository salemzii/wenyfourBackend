import os
import motor.motor_asyncio

#os.environ["MONGODB_URL"]
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://salem:auth1234%23@localhost:27017/?authMechanism=DEFAULT")
db = client.wenyfour
