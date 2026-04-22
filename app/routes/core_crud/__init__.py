from fastapi import APIRouter

# Importaciones desde subcarpetas organizadas
from .security.user_routes import router as user_router
from .security.rol_usuario_routes import router as role_router
from .audit.tipo_evento_auditoria_routes import router as tipo_evento_router
from .audit.bitacora_routes import router as bitacora_router
from .catalogs.nivel_criticidad_routes import router as nivel_criticidad_router
from .catalogs.tipo_acceso_routes import router as tipo_acceso_router
from .infrastructure.servidor_routes import router as servidor_router
from .infrastructure.credencial_acceso_routes import router as credencial_router
from .infrastructure.dbms_routes import router as dbms_router
from .infrastructure.instancia_routes import router as instancia_router
from .infrastructure.base_de_datos_routes import router as base_de_datos_router
from .backups.tipo_respaldo_routes import router as tipo_respaldo_router
from .backups.tipo_almacenamiento_routes import router as tipo_almacenamiento_router
from .backups.ruta_respaldo_routes import router as ruta_respaldo_router
from .backups.politica_respaldo_routes import router as politica_respaldo_router
from .backups.asignacion_politica_routes import router as asignacion_politica_router
from .backups.respaldo_routes import router as respaldo_router
from .catalogs.tipo_metrica_routes import router as tipo_metrica_router
from .catalogs.metrica_routes import router as metrica_router
from .catalogs.monitoreo_routes import router as monitoreo_router
from .catalogs.nivel_alerta_routes import router as nivel_alerta_router
from .catalogs.alerta_routes import router as alerta_router
from .catalogs.estado_general_routes import router as estado_general_router

router = APIRouter()

# Seguridad
router.include_router(user_router, prefix="/users", tags=["Security - Users"])
router.include_router(role_router, prefix="/roles", tags=["Security - Roles"])

# Catálogos Base
router.include_router(estado_general_router, prefix="/estados", tags=["Catalogs - Estados Generales"])
router.include_router(nivel_criticidad_router, prefix="/criticidad", tags=["Catalogs - Criticidad"])
router.include_router(tipo_acceso_router, prefix="/tipo-acceso", tags=["Catalogs - Tipo Acceso"])

# Auditoría
router.include_router(tipo_evento_router, prefix="/audit-types", tags=["Audit - Event Types"])
router.include_router(bitacora_router, prefix="/audit-logs", tags=["Audit - Logs"])

# Infraestructura (CMDB)
router.include_router(servidor_router, prefix="/servidores", tags=["Infrastructure - Servidores"])
router.include_router(credencial_router, prefix="/credenciales", tags=["Infrastructure - Credenciales"])
router.include_router(dbms_router, prefix="/dbms", tags=["Infrastructure - DBMS"])
router.include_router(instancia_router, prefix="/instancias", tags=["Infrastructure - Instancias"])
router.include_router(base_de_datos_router, prefix="/bases-de-datos", tags=["Infrastructure - Bases de Datos"])

# Backups
router.include_router(tipo_respaldo_router, prefix="/tipo-respaldo", tags=["Backups - Tipos de Respaldo"])
router.include_router(tipo_almacenamiento_router, prefix="/tipo-almacenamiento", tags=["Backups - Tipos de Almacenamiento"])
router.include_router(ruta_respaldo_router, prefix="/rutas-respaldo", tags=["Backups - Rutas de Respaldo"])
router.include_router(politica_respaldo_router, prefix="/politicas-respaldo", tags=["Backups - Políticas de Respaldo"])
router.include_router(asignacion_politica_router, prefix="/asignacion-politica", tags=["Backups - Asignación de Políticas"])
router.include_router(respaldo_router, prefix="/respaldos", tags=["Backups - Ejecuciones de Respaldo"])

# Monitoreo (CRUD)
router.include_router(tipo_metrica_router, prefix="/tipo-metrica", tags=["Monitoring CRUD - Tipos de Métrica"])
router.include_router(metrica_router, prefix="/metricas", tags=["Monitoring CRUD - Métricas"])
router.include_router(monitoreo_router, prefix="/monitoreo", tags=["Monitoring CRUD - Sesiones"])
router.include_router(nivel_alerta_router, prefix="/nivel-alerta", tags=["Monitoring CRUD - Niveles de Alerta"])
router.include_router(alerta_router, prefix="/alertas", tags=["Monitoring CRUD - Alertas"])
