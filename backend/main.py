import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers.contracts import router as contracts_router
from routers.config import router as config_router

load_dotenv()

app = FastAPI(
    title="Horizon Search API",
    description="Government contract search for veteran-owned businesses.",
    version="1.0.0",
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contracts_router, prefix="/api")
app.include_router(config_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
