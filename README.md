# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para la observabilidad de infraestructura crítica (SRE), gestión automatizada de respaldos y monitoreo inteligente de bases de datos multi-motor.

## 📁 Estructura del Proyecto

El proyecto sigue una **Arquitectura Simétrica por Dominios** para asegurar la escalabilidad y el orden:

*   **`app/core/`**: Núcleo del sistema. Contiene la configuración global, orquestador SSH con soporte Legacy, gestión de sesiones dinámicas de DB y lógica de seguridad (JWT/AES).
*   **`app/db/`**: Configuración de conectividad para todos los motores soportados (Postgres, MySQL, Oracle, MongoDB).
*   **`app/models/`**: Modelos físicos de SQLAlchemy que definen la CMDB, el historial de respaldos y métricas.
*   **`app/schemas/`**: Esquemas de Pydantic organizados por dominio (Infrastructure, Backups, Security, etc.) para validación de entrada/salida.
*   **`app/services/`**: Lógica de negocio y operaciones CRUD, desacoplada de los controladores API.
*   **`app/routes/`**: Puntos de entrada de la API, organizados por dominios lógicos y funcionales.

## 🚀 Catálogo de Endpoints

### 🔐 Seguridad y Usuarios (`/users`, `/roles`)
*   `POST /users/login`: Autenticación y generación de JWT.
*   `POST /users/logout`: Cierre de sesión auditado.
*   `GET /users/me`: Perfil del usuario autenticado.
*   `POST /users/`: Registro de nuevos usuarios.
*   `GET /users/`: Listado de usuarios.
*   `PUT /users/{id}/password`: Cambio seguro de contraseña.
*   `POST /roles/`: Gestión de roles de sistema.

### 🏗️ Infraestructura y CMDB (`/servidores`, `/instancias`, `/credenciales`, `/dbms`)
*   `POST /servidores/`: Registro de servidores con validación de IP.
*   `GET /servidores/{ip}`: Consulta rápida de servidor por IP.
*   `POST /credenciales/`: Almacenamiento cifrado de accesos.
*   `POST /credenciales/test-ssh/{id_srv}/{id_cred}`: Test de conexión SSH (Soporta Legacy).
*   `POST /instancias/`: Registro de instancias de DB (MySQL, Oracle, etc).
*   `POST /instancias/test-db/{id_inst}/{id_cred}`: Test de conectividad dinámico a RDBMS.
*   `POST /bases-de-datos/`: Registro manual de bases de datos lógicas.

### 📊 Monitoreo y Descubrimiento (`/monitoring`)
*   `GET /monitoring/host/{id_srv}/{id_cred}`: Monitoreo en tiempo real de CPU, RAM y Disco vía SSH.
*   `POST /monitoring/inventory/discover/{id_inst}/{id_cred}`: Auto-descubrimiento de DBs y tamaños en MySQL.
*   `GET /monitoring/inventory/summary/{id_srv}`: Resumen de almacenamiento por servidor.
*   `GET /monitoring/mysql5/metrics/{id_inst}`: Métricas avanzadas de MySQL 5.
*   `GET /monitoring/mysql8/{id_srv}/{id_cred}`: Monitoreo nativo de MySQL 8.
*   `GET /monitoring/mongodb/{id_srv}/{id_cred}`: Monitoreo de performance para MongoDB.

### 💾 Gestión de Respaldos (`/rutas-respaldo`, `/politicas-respaldo`, `/respaldos`)
*   `POST /rutas-respaldo/`: Definición de destinos de storage (NFS, S3, Local).
*   `POST /politicas-respaldo/`: Configuración de frecuencias y periodos de retención.
*   `POST /asignacion-politica/`: Vinculación de bases de datos a políticas de backup.
*   `POST /respaldos/`: Registro y auditoría de ejecuciones de respaldo.
*   `GET /respaldos/historial`: Consulta de trazas de backup históricas.

### 🛠️ Catálogos y Auditoría (`/estados`, `/audit-logs`, `/criticidad`)
*   `GET /audit-logs/`: Bitácora inmutable de operaciones del sistema.
*   `POST /estados/`: Gestión de estados globales (Activo, Fallido, etc).
*   `GET /health/postgres`: Verificación de salud de la base de datos principal.

## 🛠️ Stack Tecnológico
*   **Backend:** FastAPI (Python 3.14) + SQLAlchemy 2.0
*   **Base de Datos:** PostgreSQL 16
*   **Gestión SSH:** Paramiko (con perfiles custom para Legacy)
*   **Seguridad:** JWT, Bcrypt, AES-256 (Fernet)
*   **DevOps:** Docker (Multi-stage build) + `uv` (Fastest Python manager)
