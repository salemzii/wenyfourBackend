from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from auth.router import router as auth_routers
from driver.router import router as driver_routers

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
app.include_router(driver_routers)


@app.get("/api/")
def root():
    return {"message": "Welcome to FastAPI with MongoDB"}

