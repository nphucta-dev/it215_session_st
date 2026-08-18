import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select

from core.config import settings
from core.database import Base, SessionLocal, engine
from middleware.request_middleware import RequestContextMiddleware
from models.models import User, Resource
from routers import auth_router, resource_router, user_router
from services.auth_service import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


def seed_database() -> None:
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@example.com"))
        if admin is None:
            admin = User(
                email="admin@example.com",
                full_name="System Admin",
                hashed_password=hash_password("Admin123!"),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.flush()

        user = db.scalar(select(User).where(User.email == "user@example.com"))
        if user is None:
            user = User(
                email="user@example.com",
                full_name="Demo User",
                hashed_password=hash_password("User12345!"),
                role="user",
                is_active=True,
            )
            db.add(user)
            db.flush()

        existing_resource = db.scalar(select(Resource).where(Resource.title == "Python FastAPI Fundamentals"))
        if existing_resource is None:
            db.add(
                Resource(
                    title="Python FastAPI Fundamentals",
                    description="Tài liệu mẫu về routing, dependency injection và JWT.",
                    resource_type="document",
                    content_url="https://fastapi.tiangolo.com/",
                    owner_id=user.id,
                )
            )
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Secure learning resource portal with JWT authentication, RBAC, ownership checks, CORS and request monitoring.",
)

# Custom middleware is added first; CORS is added after it so CORS stays the outer layer
# and can answer browser preflight OPTIONS requests without requiring a token.
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Input validation failed",
            "errors": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.get("/api/v1/health", tags=["System"])
def health():
    return {"status": "ok", "service": settings.app_name}


app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(resource_router.router)
