from pydantic import BaseModel

class StatusBase(BaseModel):
    nombre_estado: str

class StatusCreate(StatusBase):
    pass

class StatusResponse(StatusBase):
    id_estado: int

    class Config:
        from_attributes = True
