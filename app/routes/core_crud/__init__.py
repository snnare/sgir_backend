from fastapi import APIRouter
from .user_routes import router as user_router
from .rol_usuario_routes import router as role_router
from .tipo_evento_auditoria_routes import router as tipo_evento_router
from .bitacora_routes import router as bitacora_router

router = APIRouter()

router.include_router(user_router, prefix="/users", tags=["Users"])
router.include_router(role_router, prefix="/roles", tags=["Roles"])
router.include_router(tipo_evento_router, prefix="/audit-types", tags=["Audit Event Types"])
router.include_router(bitacora_router, prefix="/audit-logs", tags=["Audit Logs"])
