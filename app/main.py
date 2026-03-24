from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router


app = FastAPI(
    title="KLS Timber Floor Joist API",
    version="0.1.0",
    description=(
        "Backend API for timber floor joist calculations with typed inputs, "
        "traceable outputs, and reusable domain logic."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return FileResponse("frontend/preview.html", media_type="text/html")

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.include_router(router)
