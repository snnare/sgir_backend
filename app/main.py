from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# Aqui importar routeas
# Aqui import scheduler de metricas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranca el scraper en segundo plano
    # Monitoreo cada x tiempo
    # task = asyncio.create_tas()
    yield

    pass


# agregar la funcion anterior lifespan
app = FastAPI(title="FasltAPI SGIR Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Especificar de que ips se puede acceder
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Seccion para incluir rutas


@app.get("/")
def read_root():
    return {"message": "Welcome"}
