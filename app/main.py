from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import core_crud_router
from app.routes.healths import health_router
from app.routes.monitoring import m1_router, m2_router, m3_router
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

# Módulo 1: Monitoreo & Alertas (incluye salud e ICMP ping)
m1_root_router = APIRouter(prefix="/m1")
m1_root_router.include_router(health_router)

@m1_root_router.get("/")
def read_root_m1():
    return {"message": "Welcome"}

@m1_root_router.get("/ping")
def ping_m1():
    return {"status": "ok", "message": "Backend is reachable"}

api_router.include_router(m1_root_router)
api_router.include_router(m1_router)

# Módulo 2: Búsqueda de Activos (CMDB)
api_router.include_router(m2_router)

# Módulo 3: Gestión de Respaldos
api_router.include_router(m3_router)

# CRUD Completo bajo el prefijo /crud
api_router.include_router(core_crud_router)

app.include_router(api_router)

# Rutas de disponibilidad general en la raíz del servidor
@app.get("/")
def read_root():
    return {"message": "Welcome"}

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend is reachable"}
