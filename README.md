# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para la observabilidad de infraestructura crítica, gestión de respaldos y monitoreo de bases de datos.

## 🚀 Características Principales

### 🔐 Seguridad y Compliance
*   **JWT & Bcrypt:** Gestión de sesiones seguras.
*   **Cifrado Reversible (Fernet/AES):** Almacenamiento seguro de credenciales para acceso remoto automatizado.
*   **Auditoría Total:** Registro inmutable de operaciones (Logins, CRUD, Monitoreo).

### 🏗️ CMDB e Inventario
*   **Discovery Service:** Escaneo remoto para descubrir bases de datos y tamaños.
*   **Inventario Dinámico:** Gestión de servidores, DBMS, instancias y BDs.

### 📊 Monitoreo Multi-Motor (SRE)
*   **Motores Soportados:** MySQL 5, MySQL 8, MongoDB.
*   **Host Monitoring:** Monitoreo vía SSH de CPU, RAM, Disco y Uptime (con soporte para sistemas Legacy RHEL 4+).

## 🛠️ Stack Tecnológico

*   **Framework:** FastAPI (Python 3.14)
*   **ORM:** SQLAlchemy 2.0 (PostgreSQL)
*   **Gestión:** `uv` (Fastest Python package manager)
*   **Contenerización:** Docker (Multi-stage build)

## 📁 Estructura y Documentación

*   `/docs`: Swagger UI interactivo (con el servidor corriendo).
*   `workflow.txt`: Guía completa de endpoints con ejemplos `curl` para pruebas.
*   `app/services/`: Lógica de negocio y proveedores de métricas.

## ⚙️ Configuración Rápida

### Usando UV (Local)
1. `uv sync`
2. Configurar `.env` (Basado en `SECRET_KEY` de 32 bytes).
3. `uv run uvicorn app.main:app --reload`

### Usando Docker
1. `docker build -t sgir-backend .`
2. `docker run -p 8000:8000 --env-file .env sgir-backend`

## 🧪 Pruebas Rápidas
Consulta `workflow.txt` para encontrar los comandos `curl` de registro y monitoreo listos para copiar y pegar.
