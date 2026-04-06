from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import (
    health_router
)



# Aqui import scheduler de metricas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranca el scraper en segundo plano
    # Monitoreo cada x tiempo
    # task = asyncio.create_tas()
    yield

    pass


# agregar la funcion anterior lifespan
app = FastAPI(title="FastAPI SGIR Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Especificar de que ips se puede acceder
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Seccion para incluir rutas
app.include_router(router=health_router)

@app.get("/")
def read_root():
    return {"message": "Welcome"}
