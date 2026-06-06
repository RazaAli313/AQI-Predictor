from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from routes.user import user_router

app=FastAPI()


CORS_ORIGINS=[
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
    prefix="/api",
    # router=user_router
)


if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="", port=8000)