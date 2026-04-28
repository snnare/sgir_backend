# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para la observabilidad de infraestructura crítica (SRE), gestión automatizada de respaldos y monitoreo inteligente de bases de datos multi-motor.

## 📁 Estructura del Proyecto

El proyecto sigue una **Arquitectura Simétrica por Dominios** para asegurar la escalabilidad y el orden:

*   **`app/core/`**: Núcleo del sistema. Contiene la configuración global, orquestador SSH con soporte Legacy, gestión de sesiones dinámicas de DB y lógica de seguridad (JWT/AES).
*   **`app/services/infrastructure/`**: Incluye el nuevo motor de **Importación Masiva (CSV)** con cifrado on-the-fly.
*   **`app/services/monitoring/ssh/`**: Proveedores modulares para métricas de host y descubrimiento de archivos.
*   **`plantilla/`**: Contiene las plantillas CSV oficiales para la carga masiva de infraestructura.
*   **`app/models/`**, **`app/schemas/`**, **`app/routes/`**: Capas de persistencia, validación y controladores organizados por dominios.

## 🚀 Catálogo de Endpoints

### 🔐 Seguridad y Usuarios (`/users`, `/roles`)
*   `POST /users/login`: Autenticación y generación de JWT.
*   `GET /users/me`: Perfil del usuario autenticado.
*   `POST /users/`: Registro de nuevos usuarios.

### 🏗️ Infraestructura y CMDB (`/servidores`, `/instancias`, `/credenciales`)
*   **`POST /servidores/import-bulk`**: Carga masiva de Servidores, Instancias y Credenciales vía CSV (Normaliza etiquetas y cifra passwords).
*   `POST /servidores/`: Registro individual de servidores.
*   `POST /credenciales/`: Almacenamiento cifrado (AES-256) de accesos.
*   `POST /credenciales/test-ssh/{id_srv}/{id_cred}`: Test de conexión SSH (Soporta **Legacy RHEL 4/5**).
*   `POST /instancias/test-db/{id_inst}/{id_cred}`: Test de conectividad dinámico a RDBMS (Oracle, MySQL, Mongo).

### 📊 Monitoreo y Descubrimiento (`/monitoring`)
*   `GET /monitoring/host/{id_srv}/{id_cred}`: Monitoreo en tiempo real de CPU, RAM y Disco.
*   **`POST /monitoring/inventory/discover-backups/...`**: Rastreo SSH integrado. Busca archivos (`.sql`, `.dmp`, `.archive`), vincula con BDs existentes y registra automáticamente en la tabla de Respaldos.
*   `POST /monitoring/inventory/discover/{id_inst}`: Sincronización de inventario lógico de bases de datos.
*   `GET /monitoring/oracle/{id_inst}/{id_cred}`: Monitoreo modular basado en criticidad (Grupos A, B, C).

### 💾 Gestión de Respaldos y Auditoría
*   `GET /respaldos/historial`: Consulta de trazas de backup (manuales y auto-descubiertas).
*   `GET /audit-logs/`: Bitácora inmutable (SRE) de todas las operaciones críticas.
*   `GET /ping`: Health check de disponibilidad del backend.

## 🛠️ Stack Tecnológico
*   **Backend:** FastAPI (Python 3.14) + SQLAlchemy 2.0
*   **Base de Datos:** PostgreSQL 16
*   **Gestión SSH:** Paramiko (Perfiles Legacy + Modernos)
*   **Seguridad:** JWT, Bcrypt, AES-256 (Fernet)
*   **DevOps:** Docker (Multi-stage) + `uv` (Fastest Python manager)
