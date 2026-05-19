from typing import Any, Dict, Optional
from fastapi import status

class SGIRBaseException(Exception):
    """Excepción base para toda la lógica de negocio de la aplicación SGIR."""
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        message: str = "Ha ocurrido un error inesperado en el servidor",
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        # Si detail no se proporciona, usamos el message como valor por defecto
        self.detail = detail if detail is not None else message
        self.headers = headers
        super().__init__(self.message)

# --- SEGURIDAD Y AUTENTICACIÓN ---
class AuthenticationException(SGIRBaseException):
    def __init__(self, detail: Any = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            message="No se pudo validar las credenciales o token inválido",
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationException(SGIRBaseException):
    def __init__(self, detail: Any = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            message="No tiene privilegios suficientes para realizar esta acción",
            detail=detail
        )

# --- MÓDULO CRUD / CMDB ---
class AssetNotFoundException(SGIRBaseException):
    def __init__(self, asset_type: str = "Recurso", detail: Any = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=f"{asset_type} no encontrado en el sistema",
            detail=detail or f"No existe un registro de {asset_type} con los parámetros especificados"
        )

class CMDBConflictException(SGIRBaseException):
    def __init__(self, detail: Any = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            message="Conflicto de unicidad en la base de datos o activo duplicado",
            detail=detail
        )

# --- MÓDULO 1: MONITOREO Y ALERTAS ---
class SSHConnectionException(SGIRBaseException):
    def __init__(self, host: str, detail: Any = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="SSH_CONNECTION_ERROR",
            message=f"No se pudo establecer la conexión SSH con el host: {host}",
            detail=detail
        )

class DBMetricsExtractionException(SGIRBaseException):
    def __init__(self, dbms_name: str, detail: Any = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="METRICS_EXTRACTION_ERROR",
            message=f"Error al extraer métricas del motor de base de datos {dbms_name}",
            detail=detail
        )

class HostUnreachableException(SGIRBaseException):
    def __init__(self, host: str, detail: Any = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="HOST_UNREACHABLE",
            message=f"El host de destino no es alcanzable: {host}",
            detail=detail
        )

# --- MÓDULO 3: GESTIÓN DE RESPALDOS ---
class BackupPathMissingException(SGIRBaseException):
    def __init__(self, path: str, detail: Any = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="BACKUP_PATH_MISSING",
            message=f"La ruta de respaldo especificada no existe en el host: {path}",
            detail=detail
        )

class BackupExecutionException(SGIRBaseException):
    def __init__(self, policy_name: str, detail: Any = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="BACKUP_EXECUTION_ERROR",
            message=f"Fallo crítico durante la ejecución de la política de respaldo: {policy_name}",
            detail=detail
        )
