from fastapi import FastAPI
from .config import settings
from .database import Base, engine
from .api import cdr as cdr_router
from .api import health as health_router
from .api import subscribers as subscribers_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # DB init
    Base.metadata.create_all(bind=engine)

    # Routers
    app.include_router(health_router.router, prefix="")
    app.include_router(cdr_router.router, prefix="/cdrs", tags=["cdrs"])
    app.include_router(subscribers_router.router, prefix="/subscribers", tags=["subscribers"])

    return app


app = create_app()
