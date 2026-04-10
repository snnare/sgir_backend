# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para centralizar el control de infraestructura crítica, la gestión de políticas de respaldo y el monitoreo de Golden Signals en entornos de bases de datos heterogéneos (PostgreSQL, MySQL, Oracle, MongoDB).

## 🚀 Características Principales

### 🔐 Seguridad y Acceso
*   **Autenticación JWT:** Flujo completo de registro e inicio de sesión con tokens de acceso de corta duración.
*   **Gestión de Roles:** Control de acceso basado en roles (Administrador, Operador, Auditor).
*   **Cifrado de Credenciales:** Uso de **Bcrypt** para contraseñas de usuario y **Fernet (AES reversible)** para credenciales de servidores remotos, permitiendo la automatización de tareas sin exponer secretos.

### 🏗️ Gestión de Infraestructura
*   **Inventario de Servidores:** Registro detallado de activos físicos/virtuales con niveles de criticidad.
*   **CMDB Dinámica:** Gestión de instancias DBMS, bases de datos específicas y sus configuraciones de red.
*   **Tipos de Acceso:** Soporte para múltiples protocolos de conexión (SSH, Native DB, API).

### 💾 Estrategia de Respaldos
*   **Políticas Flexibles:** Definición de frecuencia de respaldo, retención de días y tipos de backup (Full, Incremental).
*   **Gestión de Rutas:** Configuración de paths de almacenamiento segmentados por tipo (Local, Cloud, NAS).
*   **Historial de Ejecución:** Registro transaccional de cada backup con tamaños y hashes de integridad.

### 📊 Monitoreo y Alertas
*   **Métricas Históricas:** Persistencia de puntos de datos para análisis de rendimiento.
*   **Sesiones de Monitoreo:** Registro de estados de salud y disponibilidad.
*   **Sistema de Alertas:** Generación de notificaciones basadas en niveles de severidad configurables.

### 📋 Auditoría Centralizada
*   **Bitácora de Eventos:** Cada operación sensible (creación, edición, eliminación, login) se registra automáticamente vinculando al usuario responsable, la entidad afectada y la descripción exacta del cambio.

## 🛠️ Stack Tecnológico

*   **Lenguaje:** Python 3.12+
*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
*   **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
*   **Base de Datos:** [PostgreSQL 16](https://www.postgresql.org/)
*   **Gestión de Dependencias:** [uv](https://github.com/astral-sh/uv)
*   **Seguridad:** Passlib (Bcrypt), Python-Jose (JWT), Cryptography (Fernet)

## 📋 Requisitos Previos

*   Python instalado.
*   Instancia de PostgreSQL 16 activa.
*   Herramienta `uv` instalada para una gestión eficiente del entorno.

## ⚙️ Configuración

1.  Clona el repositorio:
    ```bash
    git clone https://github.com/snnare/sgir_backend.git
    cd sgir_backend
    ```

2.  Configura las variables de entorno en un archivo `.env`:
    ```env
    # PostgreSQL
    POSTGRES_USER=tu_usuario
    POSTGRES_PASSWORD=tu_password
    POSTGRES_DB=sgir_db
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432

    # Security
    SECRET_KEY=tu_fernert_key_generada
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=60
    ```

3.  Instala las dependencias e inicia el servidor:
    ```bash
    uv sync
    uv run uvicorn app.main:app --reload
    ```

## 📖 Documentación API

Una vez iniciado el servidor, puedes acceder a la documentación interactiva (Swagger UI) en:
`http://localhost:8000/docs`

## 🗄️ Modelo de Base de Datos

El diseño físico de la base de datos se encuentra documentado en el archivo `modelo-fisico.sql`. Incluye catálogos base, tablas principales de nivel 1 a 3 y tablas transaccionales de alto volumen.
