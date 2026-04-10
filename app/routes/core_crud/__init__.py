from fastapi import APIRouter
from .user_routes import router as user_router
from .rol_usuario_routes import router as role_router
from .tipo_evento_auditoria_routes import router as tipo_evento_router
from .bitacora_routes import router as bitacora_router
from .nivel_criticidad_routes import router as nivel_criticidad_router
from .tipo_acceso_routes import router as tipo_acceso_router
from .servidor_routes import router as servidor_router
from .credencial_acceso_routes import router as credencial_router

router = APIRouter()

router.include_router(user_router, prefix="/users", tags=["Users"])
router.include_router(role_router, prefix="/roles", tags=["Roles"])
router.include_router(tipo_evento_router, prefix="/audit-types", tags=["Audit Event Types"])
router.include_router(bitacora_router, prefix="/audit-logs", tags=["Audit Logs"])
router.include_router(nivel_criticidad_router, prefix="/criticidad", tags=["Infrastructure - Criticidad"])
router.include_router(tipo_acceso_router, prefix="/tipo-acceso", tags=["Infrastructure - Tipo Acceso"])
router.include_router(servidor_router, prefix="/servidores", tags=["Infrastructure - Servidores"])
router.include_router(credencial_router, prefix="/credenciales", tags=["Infrastructure - Credenciales"])
