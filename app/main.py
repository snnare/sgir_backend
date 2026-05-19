from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import core_crud_router
from app.routes.healths import health_router
from app.routes.monitoring import router as monitoring_router
from app.core.scheduler_manager import start_scheduler, stop_scheduler, pause_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranca el scheduler de monitoreo automático
    start_scheduler()
    # Lo pausamos por defecto para evitar conexiones automáticas no deseadas al inicio
    pause_scheduler()
    yield
    # Detiene el scheduler al cerrar la app
    stop_scheduler()

# Aplicación FastAPI
app = FastAPI(title="FastAPI SGIR Backend", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Especificar de que ips se puede acceder
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Seccion para incluir rutas
from fastapi import APIRouter

api_router = APIRouter(prefix="/sgir/v1")
api_router.include_router(health_router)
api_router.include_router(core_crud_router)
api_router.include_router(monitoring_router, prefix="/monitoring")

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Welcome"}

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend is reachable"}
