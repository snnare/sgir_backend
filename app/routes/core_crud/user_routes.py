from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.user_schemas import UserCreate, UserResponse
from app.crud import user_crud

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_pg_db)):
    """Registra un nuevo usuario."""
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya registrado"
        )
    return user_crud.create_user(db=db, user=user)

@router.get("/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    """Obtiene la lista de todos los usuarios."""
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_pg_db)):
    """Obtiene un usuario por su ID."""
    db_user = user_crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user


@router.get("/email/{email}", response_model=UserResponse)
def read_user_by_email(email: str, db: Session = Depends(get_pg_db)):
    """Obtiene un usuario por su correo electrónico."""
    db_user = user_crud.get_user_by_email(db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserCreate, db: Session = Depends(get_pg_db)):
    """Actualiza la información de un usuario."""
    db_user = user_crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user


@router.put("/email/{email}", response_model=UserResponse)
def update_user_by_email(email: str, user_update: UserCreate, db: Session = Depends(get_pg_db)):
    """Actualiza la información de un usuario por su correo electrónico."""
    db_user = user_crud.update_user_by_email(db, email=email, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_pg_db)):
    """Elimina un usuario por su ID."""
    success = user_crud.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return None


@router.delete("/email/{email}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_email(email: str, db: Session = Depends(get_pg_db)):
    """Elimina un usuario por su correo electrónico."""
    success = user_crud.delete_user_by_email(db, email=email)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return None
