from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.user_schemas import UserCreate, UserResponse, UserLogin, Token
from app.services import user_crud, audit_crud
from app.core.security.hashing import verify_password
from app.core.security.tokens import create_access_token
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter()

@router.post("/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_pg_db)):
    """Inicia sesión para obtener un token de acceso."""
    user = user_crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    # Auditoría: Login
    audit_crud.log_event(
        db=db,
        user_id=user.id_usuario,
        entidad="Usuario",
        entidad_id=user.id_usuario,
        descripcion=f"Inicio de sesión exitoso: {user.email}",
        tipo_evento_id=5  # Ejecución
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """Obtiene la información del usuario actual autenticado."""
    return current_user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_pg_db)):
    """Registra un nuevo usuario (Público)."""
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya registrado"
        )
    new_user = user_crud.create_user(db=db, user=user)
    
    # Auditoría: Registro (ID de usuario es el mismo recién creado por ser público)
    audit_crud.log_event(
        db=db,
        user_id=new_user.id_usuario,
        entidad="Usuario",
        entidad_id=new_user.id_usuario,
        descripcion=f"Registro de nuevo usuario público: {new_user.email}",
        tipo_evento_id=2  # Creación
    )
    
    return new_user

@router.get("/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """Obtiene la lista de todos los usuarios."""
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """Obtiene un usuario por su ID."""
    db_user = user_crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user


@router.get("/email/{email}", response_model=UserResponse)
def read_user_by_email(email: str, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """Obtiene un usuario por su correo electrónico."""
    db_user = user_crud.get_user_by_email(db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """Actualiza la información de un usuario."""
    db_user = user_crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Auditoría: Modificación
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Usuario",
        entidad_id=user_id,
        descripcion=f"Usuario actualizado: {db_user.email} por {current_user.email}",
        tipo_evento_id=2  # Modificación
    )
    
    return db_user


@router.put("/email/{email}", response_model=UserResponse)
def update_user_by_email(email: str, user_update: UserCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """Actualiza la información de un usuario por su correo electrónico."""
    db_user = user_crud.update_user_by_email(db, email=email, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Auditoría: Modificación
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Usuario",
        entidad_id=db_user.id_usuario,
        descripcion=f"Usuario actualizado por email: {email} por {current_user.email}",
        tipo_evento_id=2  # Modificación
    )
    
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """Elimina un usuario por su ID."""
    db_user = user_crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    success = user_crud.delete_user(db, user_id=user_id)
    
    # Auditoría: Eliminación
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Usuario",
        entidad_id=user_id,
        descripcion=f"Usuario eliminado: {db_user.email} por {current_user.email}",
        tipo_evento_id=4  # Eliminación
    )
    
    return None


@router.delete("/email/{email}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_email(email: str, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """Elimina un usuario por su correo electrónico."""
    db_user = user_crud.get_user_by_email(db, email)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    success = user_crud.delete_user_by_email(db, email=email)
    
    # Auditoría: Eliminación
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Usuario",
        entidad_id=db_user.id_usuario,
        descripcion=f"Usuario eliminado por email: {email} por {current_user.email}",
        tipo_evento_id=4  # Eliminación
    )
    
    return None
