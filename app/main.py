from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import create_pool, close_pool, init_database
from app.routes import router
from app.routes_auth import router as auth_router
from app.routes_admin import router as admin_router
from app.auth import create_default_admin

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_pool()
    # Initialiser les tables de la base de données
    try:
        await init_database()
    except Exception as e:
        print(f"Note: Erreur lors de l'initialisation de la DB: {e}")
    # Créer le compte admin par défaut s'il n'existe pas
    try:
        await create_default_admin()
    except Exception as e:
        print(f"Note: Impossible de créer l'admin par défaut: {e}")
    yield
    # Shutdown
    await close_pool()


app = FastAPI(
    title="r/placeFR API",
    description="API pour le site r/placeFR",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"message": "r/placeFR API", "version": "1.1.0"}
