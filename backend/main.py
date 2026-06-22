import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers.tasks import router as tasks_router
from backend.routers.users import router as users_router

app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
    description="Backend API for the internship task manager project.",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{duration:.4f}"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(tasks_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Task Manager API is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}