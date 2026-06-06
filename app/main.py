from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import traceback
import time

from app.routes import core_crud_router, router as reports_router
from app.routes.healths import health_router
from app.routes.monitoring import m1_router, m2_router, m3_router
from app.core.scheduler_manager import start_scheduler, stop_scheduler, pause_scheduler
from app.core.exceptions import SGIRBaseException

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

# --- REQUEST LOGGING MIDDLEWARE ---

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    query = request.url.query
    query_str = f"?{query}" if query else ""
    print(f"--> [REQ] {request.method} {path}{query_str}")
    
    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        print(f"<-- [RES] {request.method} {path}{query_str} - Status: {response.status_code} ({duration:.2f}ms)")
        return response
    except Exception as exc:
        duration = (time.time() - start_time) * 1000
        print(f"<!- [ERR] {request.method} {path}{query_str} - Error: {str(exc)} ({duration:.2f}ms)")
        traceback.print_exc()
        raise exc

# --- GLOBAL EXCEPTION HANDLERS ---

@app.exception_handler(SGIRBaseException)
async def sgir_base_exception_handler(request: Request, exc: SGIRBaseException):
    print(f"[EXC] SGIRBaseException caught during {request.method} {request.url.path}: {exc.message} (status: {exc.status_code})")
    timestamp = datetime.now(timezone.utc).isoformat()
    content = {
        "success": False,
        "detail": str(exc.detail),
        "error": {
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
            "timestamp": timestamp
        }
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    print(f"[EXC] StarletteHTTPException caught during {request.method} {request.url.path}: {exc.detail} (status: {exc.status_code})")
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Mapeo de códigos HTTP a error_code de negocio
    status_to_code = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_ERROR",
        403: "AUTHORIZATION_ERROR",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
    }
    error_code = status_to_code.get(exc.status_code, "INTERNAL_SERVER_ERROR")
    
    # Determinar un mensaje amigable en español según el código de estado
    status_to_msg = {
        400: "Petición incorrecta o mal formada",
        401: "No autorizado. Inicie sesión nuevamente",
        403: "No tiene privilegios suficientes para realizar esta acción",
        404: "El recurso solicitado no fue encontrado",
        409: "Conflicto con un recurso existente en el sistema",
        422: "Error de validación en los datos enviados",
    }
    message = status_to_msg.get(exc.status_code, "Ha ocurrido un error en el servidor")
    
    content = {
        "success": False,
        "detail": str(exc.detail),
        "error": {
            "status_code": exc.status_code,
            "error_code": error_code,
            "message": message,
            "detail": exc.detail,
            "timestamp": timestamp
        }
    }
    
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=headers
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[EXC] RequestValidationError caught during {request.method} {request.url.path}: {str(exc.errors())}")
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Formatear los detalles de validación de manera amigable
    errors = []
    missing_fields = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Error de validación")
        typ = err.get("type", "")
        errors.append({
            "field": field,
            "issue": msg,
            "type": typ
        })
        if typ == "missing":
            missing_fields.append(field)
            
    detail = {
        "errors": errors
    }
    if missing_fields:
        detail["missing_fields"] = missing_fields
        
    content = {
        "success": False,
        "detail": str(exc.errors()),
        "error": {
            "status_code": 422,
            "error_code": "VALIDATION_ERROR",
            "message": "Los datos de entrada no cumplen con el formato requerido o son inválidos",
            "detail": detail,
            "timestamp": timestamp
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"[EXC] General exception caught during {request.method} {request.url.path}: {str(exc)}")
    traceback.print_exc()
    timestamp = datetime.now(timezone.utc).isoformat()
    detail_msg = str(exc)
    
    content = {
        "success": False,
        "detail": detail_msg,
        "error": {
            "status_code": 500,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Ha ocurrido un error inesperado en el servidor",
            "detail": detail_msg,
            "timestamp": timestamp
        }
    }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content
    )


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

# Reporte de inventario PDF público sin autenticación
api_router.include_router(reports_router)

app.include_router(api_router)

# Rutas de disponibilidad general en la raíz del servidor
@app.get("/")
def read_root():
    return {"message": "Welcome"}

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend is reachable"}
