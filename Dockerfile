# --- Stage 1: Build y resolución de dependencias ---
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS build

# Deshabilitar telemetría de UV y forzar el uso de cache local si es posible
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Copiar solo los archivos de dependencias primero para aprovechar el cache de capas
COPY pyproject.toml uv.lock ./

# Instalar dependencias SIN el proyecto (para cachear el layer de vendor)
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev

# Copiar el código fuente y sincronizar el proyecto
COPY app ./app
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev

# --- Stage 2: Runtime limpio ---
FROM python:3.14-slim-bookworm

# Crear un usuario de sistema sin shell y sin home para seguridad
RUN addgroup --system sgir_group && \
  adduser --system --group --no-create-home --shell /bin/false sgir_user

WORKDIR /app

# Variable de entorno para que Python no bufferée logs y no genere .pyc innecesarios
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copiar el entorno virtual (.venv) desde el stage de build
COPY --from=build --chown=sgir_user:sgir_group /app/.venv /app/.venv

# Copiar el código de la aplicación y cambiar el dueño a sgir_user
COPY --chown=sgir_user:sgir_group app ./app

# Asegurar que el binario de uvicorn en el .venv sea accesible
ENV PATH="/app/.venv/bin:$PATH"

# Exponer el puerto por defecto de FastAPI
EXPOSE 8000

# Cambiar al usuario no privilegiado para ejecutar la app
USER sgir_user

# Comando de inicio: Usar uvicorn directamente desde el .venv
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

