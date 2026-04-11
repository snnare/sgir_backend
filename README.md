# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para la observabilidad y control de infraestructura crítica, gestión de respaldos y monitoreo de bases de datos.

## 🚀 Características Principales

### 🔐 Seguridad Modular
*   **Autenticación JWT:** Gestión de sesiones seguras con tokens de acceso.
*   **Arquitectura de Seguridad:** Lógica desacoplada en módulos de `hashing` (Bcrypt), `tokens` (JWT) y `encryption` (Fernet).
*   **Cifrado Reversible:** Las credenciales de servidores remotos se almacenan cifradas con AES, permitiendo al sistema recuperarlas para conexiones automáticas sin exponerlas.

### 🏗️ CMDB e Inventario Inteligente
*   **Inventario Dinámico:** Registro de servidores, instancias DBMS y bases de datos.
*   **Descubrimiento de Activos (Discovery):** Funcionalidad para escanear servidores remotos y detectar automáticamente bases de datos y su tamaño real.
*   **Persistencia Local:** Sincronización de la realidad remota con la base de datos local para permitir búsquedas y resúmenes de almacenamiento instantáneos.

### 💾 Gestión de Respaldos
*   **Políticas y Rutas:** Configuración granular de frecuencias de respaldo y destinos de almacenamiento (Local, Nube, NAS).
*   **Auditoría de Ejecución:** Seguimiento detallado de cada tarea de respaldo, incluyendo tamaños y verificación de integridad.

### 📊 Monitoreo Multi-Motor (SRE)
*   **MySQL 5 y 8:** Extracción de métricas de hilos, locks, QPS y uso de conexiones.
*   **MongoDB:** Monitoreo NoSQL usando comandos administrativos para estado de conexiones, contadores de operaciones y memoria.
*   **Alertas:** Sistema integrado para notificar anomalías basadas en niveles de criticidad.

### 📋 Auditoría Total
*   **Bitácora Automática:** Todas las operaciones (CRUD, logins, inicios de monitoreo, sincronizaciones) se registran en una bitácora inmutable que vincula al usuario responsable con la entidad afectada.

## 🛠️ Stack Tecnológico

*   **Framework:** FastAPI
*   **ORM:** SQLAlchemy 2.0 (PostgreSQL)
*   **NoSQL Driver:** PyMongo
*   **Seguridad:** Bcrypt, Python-Jose, Cryptography (Fernet)
*   **Gestión:** `uv` (Fastest Python package manager)

## 📁 Estructura del Proyecto

*   `app/services/`: Lógica de negocio, sincronización de inventario y proveedores de monitoreo.
*   `app/core/security/`: Utilidades modulares de cifrado y autenticación.
*   `app/routes/`: Endpoints organizados por `core_crud` y `monitoring`.
*   `app/models/` & `app/schemas/`: Definiciones de datos y validaciones Pydantic.

## ⚙️ Configuración Rápida

1.  **Entorno:** `uv sync`
2.  **Variables:** Configurar `.env` basado en la sección de seguridad (Secret Key de 32 bytes).
3.  **Ejecución:** `uv run uvicorn app.main:app --reload`

## 📖 Documentación
Accede a `/docs` para interactuar con la API mediante Swagger UI.
