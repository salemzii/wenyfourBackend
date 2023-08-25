from fastapi import FastAPI
from auth.router import router as auth_routers


app = FastAPI()


app.include_router(auth_routers)

@app.get("/api/")
def root():
    return {"message": "Welcome to FastAPI with MongoDB"}