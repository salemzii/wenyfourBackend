from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from auth.router import router as auth_routers
from cars.routers import router as car_routers
from rides.router import router as ride_routers

import time
import random
import string



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    #logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time)
    response.headers["X-Process-Time"] = str(process_time)
    #formatted_process_time = '{0:.2f}'.format(process_time)
    #logger.info("returning response")
    return response

app.include_router(auth_routers)
app.include_router(car_routers)
app.include_router(ride_routers)


@app.get("/api/")
def root():
    from auth.utils import send_email_async

    send_email_async(
            subject="hello world", 
            email_to="salemododa2@gmail.com", 
            body="hello people how is the world"
            )
    return {"message": "Welcome to FastAPI with MongoDB"}

