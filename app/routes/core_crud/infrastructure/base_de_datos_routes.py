from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import BaseDatosCreate, BaseDatos as BaseDatosResponse
from app.schemas.infrastructure.infrastructure_schemas import BaseDatosSearchResult
from app.services import infrastructure_crud, audit_crud
from app.services.infrastructure.import_service import process_bases_datos_csv
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/import-bulk")
async def import_bases_datos_bulk(
    file: UploadFile = File(...),
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    """
    Carga masiva de bases de datos vinculándolas a instancias mediante CSV.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un CSV")
    
    contents = await file.read()
    try:
        summary = process_bases_datos_csv(db, contents, current_user.id_usuario)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=BaseDatosResponse, status_code=status.HTTP_201_CREATED)
def create_base_datos(base_datos: BaseDatosCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_bd = infrastructure_crud.create_base_datos(db, base_datos)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="BaseDeDatos",
        entidad_id=new_bd.id_base_datos,
        descripcion=f"Base de datos registrada: {new_bd.nombre_base}",
        tipo_evento_id=2 # Creación
    )
    return new_bd

@router.get("/servidor/{servidor_id}", response_model=List[BaseDatosResponse])
def read_bases_de_datos_by_servidor(servidor_id: int, db: Session = Depends(get_pg_db)):
    """Obtiene todas las bases de datos asociadas a un servidor (a través de sus instancias)."""
    return infrastructure_crud.get_bases_de_datos_by_servidor(db, servidor_id)

@router.get("/search", response_model=List[BaseDatosSearchResult])
def search_bases_de_datos_endpoint(query: str, db: Session = Depends(get_pg_db)):
    """Busca bases de datos por nombre (coincidencia parcial) y devuelve detalles enriquecidos (IP, DBMS, Estado)."""
    return infrastructure_crud.search_bases_de_datos(db, query)

@router.get("/filter", response_model=List[BaseDatosSearchResult])
def filter_bases_de_datos_endpoint(nombre: Optional[str] = None, ip: Optional[str] = None, db: Session = Depends(get_pg_db)):
    """Filtra bases de datos por nombre y/o IP del servidor."""
    return infrastructure_crud.filter_bases_de_datos(db, nombre, ip)
