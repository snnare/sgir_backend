from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# Schemas para Rol de Usuario
class RoleBase(BaseModel):
    nombre_rol: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id_rol: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    nombres: str
    apellidos: str


class UserCreate(UserBase):
    password: str
    id_rol: int = 1
    id_estado_usuario: int = 1


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserResponse(UserBase):
    id_usuario: int
    fecha_creacion: datetime
    id_rol: int
    id_estado_usuario: int

    class Config:
        from_attributes = True
