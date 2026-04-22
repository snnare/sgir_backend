from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.infrastructure_schemas import InstanciaCreate, Instancia as InstanciaResponse
from app.services import infrastructure_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.core.dynamic_db_core import get_dynamic_session
from sqlalchemy import text

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/test-db/{id_instancia}/{id_credencial}")
def test_db_connectivity(id_instancia: int, id_credencial: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """
    Prueba la conexión a una instancia de Base de Datos (MySQL 5 u 8).
    Valida host, puerto y credenciales de BD.
    """
    instancia = infrastructure_crud.get_instancia(db, id_instancia)
    credencial = infrastructure_crud.get_credencial(db, id_credencial)
    servidor = infrastructure_crud.get_servidor(db, instancia.id_servidor) if instancia else None
    
    if not instancia or not credencial or not servidor:
        raise HTTPException(status_code=404, detail="Instancia, Servidor o Credencial no encontrados")
    
    # Validar que sea MySQL (2, 3) u Oracle (4)
    if instancia.id_dbms not in [2, 3, 4]:
        raise HTTPException(status_code=400, detail="Este test solo soporta MySQL (5/8) y Oracle (19c) actualmente")

    session = None
    try:
        # Intentar obtener sesión dinámica
        # Para Oracle, podríamos necesitar pasar el nombre de la instancia como db_name
        session = get_dynamic_session(servidor, credencial, instancia.id_dbms, db_name=instancia.nombre_instancia)
        
        # Ejecutar consulta de validación adaptada al motor
        if instancia.id_dbms == 4:
            # Oracle: Consultar banner de versión
            query = text("SELECT banner FROM v$version WHERE ROWNUM = 1")
        else:
            # MySQL: Función version()
            query = text("SELECT VERSION()")
            
        version = session.execute(query).scalar()
        
        # Auditoría del test exitoso
        audit_crud.log_event(
            db=db,
            user_id=current_user.id_usuario,
            entidad="InstanciaDBMS",
            entidad_id=id_instancia,
            descripcion=f"Test DB exitoso en {servidor.direccion_ip}:{instancia.puerto}. Versión: {version}",
            tipo_evento_id=5 # Ejecución
        )
        
        return {
            "status": "success",
            "message": f"Conexión exitosa a la base de datos en {servidor.direccion_ip}:{instancia.puerto}",
            "details": {
                "dbms_id": instancia.id_dbms,
                "version_detectada": version,
                "puerto_utilizado": instancia.puerto
            }
        }
        
    except Exception as e:
        # Auditoría del fallo
        audit_crud.log_event(
            db=db,
            user_id=current_user.id_usuario,
            entidad="InstanciaDBMS",
            entidad_id=id_instancia,
            descripcion=f"Test DB fallido en {servidor.direccion_ip}:{instancia.puerto}: {str(e)}",
            tipo_evento_id=5
        )
        raise HTTPException(status_code=500, detail=f"Error de conexión a BD: {str(e)}")
    finally:
        if session:
            session.close()

@router.post("/", response_model=InstanciaResponse, status_code=status.HTTP_201_CREATED)
def create_instancia(instancia: InstanciaCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_inst = infrastructure_crud.create_instancia(db, instancia)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="InstanciaDBMS",
        entidad_id=new_inst.id_instancia,
        descripcion=f"Instancia creada: {new_inst.nombre_instancia} en puerto {new_inst.puerto}",
        tipo_evento_id=2 # Creación
    )
    return new_inst

@router.get("/servidor/{servidor_id}", response_model=List[InstanciaResponse])
def read_instancias_by_server(servidor_id: int, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.get_instancias_by_servidor(db, servidor_id)
