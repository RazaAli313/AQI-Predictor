from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.openweather import openweather_router

app=FastAPI()



CORS_ORIGINS=[
    "http://localhost:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

app.include_router(
    openweather_router,
    prefix="/api",
)


if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)