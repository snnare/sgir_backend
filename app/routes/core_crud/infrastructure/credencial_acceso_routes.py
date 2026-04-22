from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.infrastructure_schemas import CredencialCreate, CredencialResponse, CredencialUpdate, CredencialFullResponse
from app.services import infrastructure_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.core.ssh_orchestrator import get_ssh_connection

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/test-ssh/{id_servidor}/{id_credencial}")
def test_ssh_connectivity(id_servidor: int, id_credencial: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """
    Prueba la conexión SSH de un servidor con una credencial específica.
    Valida perfiles legacy, reintentos y credenciales.
    """
    servidor = infrastructure_crud.get_servidor(db, id_servidor)
    credencial = infrastructure_crud.get_credencial(db, id_credencial)
    
    if not servidor or not credencial:
        raise HTTPException(status_code=404, detail="Servidor o Credencial no encontrados")
    
    ssh_client = None
    try:
        # El orquestador ya maneja la lógica de legacy y reintentos internamente
        ssh_client = get_ssh_connection(servidor, credencial)
        
        # Ejecutar un comando de prueba rápido
        stdin, stdout, stderr = ssh_client.exec_command("whoami && uptime")
        result = stdout.read().decode().strip().split("\n")
        
        # Auditoría del test exitoso
        audit_crud.log_event(
            db=db,
            user_id=current_user.id_usuario,
            entidad="CredencialAcceso",
            entidad_id=id_credencial,
            descripcion=f"Test SSH exitoso en {servidor.direccion_ip} con usuario {result[0]}",
            tipo_evento_id=5 # Ejecución
        )
        
        return {
            "status": "success",
            "message": f"Conexión exitosa a {servidor.direccion_ip}",
            "details": {
                "perfil_utilizado": "Legacy" if servidor.es_legacy else "Estándar",
                "usuario_remoto": result[0],
                "uptime_servidor": result[1] if len(result) > 1 else "N/A"
            }
        }
        
    except Exception as e:
        # Auditoría del fallo
        audit_crud.log_event(
            db=db,
            user_id=current_user.id_usuario,
            entidad="CredencialAcceso",
            entidad_id=id_credencial,
            descripcion=f"Test SSH fallido en {servidor.direccion_ip}: {str(e)}",
            tipo_evento_id=5
        )
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")
    finally:
        if ssh_client:
            ssh_client.close()

@router.post("/", response_model=CredencialResponse, status_code=status.HTTP_201_CREATED)
def create_credential(credencial: CredencialCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_cred = infrastructure_crud.create_credencial(db, credencial)

    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="CredencialAcceso",
        entidad_id=new_cred.id_credencial,
        descripcion=f"Credencial creada para usuario: {new_cred.usuario} en servidor ID: {new_cred.id_servidor}",
        tipo_evento_id=2 # Creación
    )
    return new_cred

@router.get("/", response_model=List[CredencialFullResponse])
def read_credentials(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    """Obtiene todas las credenciales registradas con información enriquecida (Join)."""
    creds = infrastructure_crud.get_credenciales_all(db, skip=skip, limit=limit)
    # Mapear el nombre del servidor manualmente si es necesario o dejar que Pydantic lo haga si se añade al schema
    for c in creds:
        c.servidor_nombre = c.servidor.nombre_servidor
    return creds

@router.get("/servidor/{servidor_id}", response_model=List[CredencialFullResponse])
def read_credentials_by_server(servidor_id: int, db: Session = Depends(get_pg_db)):
    creds = infrastructure_crud.get_credenciales_by_servidor(db, servidor_id)
    for c in creds:
        c.servidor_nombre = c.servidor.nombre_servidor
    return creds


@router.put("/{credencial_id}", response_model=CredencialResponse)
def update_credential(credencial_id: int, credencial_update: CredencialUpdate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    db_cred = infrastructure_crud.update_credencial(db, credencial_id, credencial_update)
    if not db_cred:
        raise HTTPException(status_code=404, detail="Credencial no encontrada")
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="CredencialAcceso",
        entidad_id=credencial_id,
        descripcion=f"Credencial actualizada para usuario: {db_cred.usuario}",
        tipo_evento_id=3 # Modificación
    )
    return db_cred

@router.delete("/{credencial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credential(credencial_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    if not infrastructure_crud.delete_credencial(db, credencial_id):
        raise HTTPException(status_code=404, detail="Credencial no encontrada")
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="CredencialAcceso",
        entidad_id=credencial_id,
        descripcion=f"Credencial eliminada ID: {credencial_id}",
        tipo_evento_id=4 # Eliminación
    )
    return None
