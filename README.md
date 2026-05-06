# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para la observabilidad de infraestructura crítica (SRE), gestión automatizada de respaldos y monitoreo inteligente multi-motor.

## 📁 Estructura del Proyecto

El proyecto sigue una **Arquitectura Simétrica por Dominios**, dividido funcionalmente en tres módulos principales y un núcleo de seguridad base:

---

## 1️⃣ Módulo de Búsqueda de Activos (Gestión de Inventario CMDB)
Centraliza el registro, organización y descubrimiento de toda la infraestructura tecnológica.

### 🚀 Capacidades
*   **Importación Masiva:** Alta de servidores, instancias y credenciales vía CSV con cifrado automático (AES-256).
*   **Test de Conexión Dinámico:** Validar credenciales SSH y de Bases de Datos (Raw Payload) antes de su registro.
*   **Organización Jerárquica:** Soporta estructuras complejas: Servidores -> Particiones -> DBMS -> Instancias -> Bases de Datos.

### 🔌 Endpoints de Activos e Infraestructura
**Catálogos del Sistema:**
- **POST, GET, DELETE** `/estados/`, `/criticidad/`, `/tipo-acceso/`

**Infraestructura (Servidores, Particiones, DBMS):**
- **POST** `/servidores/import-bulk`
- **POST, GET, PUT, DELETE** `/servidores/` (Incluye búsqueda por IP y ID)
- **GET** `/servidores/ping/{ip_server}` (Test de conectividad básica)
- **POST, GET, DELETE** `/particiones/`
- **POST, GET** `/dbms/`
- **POST, GET** `/instancias/`
- **POST, GET** `/bases-de-datos/` (Incluye búsqueda por ID de servidor)
- **GET** `/bases-de-datos/search` (Búsqueda enriquecida por nombre)
- **GET** `/bases-de-datos/filter` (Filtrado por nombre e IP del servidor)

**Credenciales y Pruebas de Conexión Dinámica:**
- **POST, GET, PUT, DELETE** `/credenciales/`
- **POST** `/credenciales/test-ssh/{id_servidor}/{id_credencial}`
- **POST** `/instancias/test-db/{id_instancia}/{id_credencial}`
- **POST** `/conexion/test/db/{motor}`
- **POST** `/conexion/test/ssh`

---

## 2️⃣ Módulo de Monitoreo Activo (Observabilidad SRE)
Vigilancia en tiempo real de recursos y servicios mediante tareas programadas asíncronas.

### 🚀 Capacidades
*   **Monitoreo de Host (SSH):** Extracción de CPU, RAM, Disco y Uptime con soporte para Legacy RHEL 4/5 y múltiples particiones de montaje.
*   **Monitoreo Unificado de DB:** Estándar de recolección para Oracle, MySQL y MongoDB.
*   **Live Cache:** Almacenamiento en RAM de métricas en tiempo real para evitar latencia en los tableros.
*   **Monitoreo Silencioso:** Persiste métricas en BD solo si superan umbrales críticos (ej. > 90% CPU).
*   **Scheduler de Alta Disponibilidad:** Pool concurrente de 80 hilos que ajusta los escaneos basado en la criticidad de los servidores.
*   **Alertas Inteligentes:** Endpoints dedicados para gestión, resumen y resolución de incidentes.

### 🔌 Endpoints de Monitoreo
**Configuración de Métricas y Alertas:**
- **POST, GET, DELETE** `/tipo-metrica/`, `/nivel-alerta/`
- **POST** `/metricas/`
- **POST, GET, PUT** `/alertas/` (Incluye alertas activas, por servidor y resolución)

**Ejecución de Métricas y Discovery de DBs:**
- **POST, GET, PUT** `/monitoreo/`
- **GET** `/monitoring/db/health-status/{instancia_id}`
- **POST** `/monitoring/db/run-adhoc/{instancia_id}/{credencial_id}`
- **GET** `/monitoring/mysql5/metrics/{id_instancia}`
- **GET** `/monitoring/mysql8/{servidor_id}/{credencial_id}`
- **GET** `/monitoring/mongodb/{servidor_id}/{credencial_id}`
- **GET** `/monitoring/oracle/{id_instancia}/{id_credencial}`
- **POST** `/monitoring/inventory/discover/{instancia_id}/{credencial_id}`
- **GET** `/monitoring/inventory/summary/{servidor_id}`

**Gestión del Scheduler (Motor de Tareas):**
- **GET** `/monitoring/host/scheduler/status`
- **POST** `/monitoring/host/scheduler/pause`
- **POST** `/monitoring/host/scheduler/resume`
- **GET** `/monitoring/host/global-summary`
- **GET** `/monitoring/host/live-cache` (Métricas en tiempo real CPU/RAM/Disco)
- **GET** `/monitoring/host/health-status/{server_id}`
- **GET** `/monitoring/host/{server_id}/{cred_id}`

---

## 3️⃣ Módulo de Automatización de Respaldos
Gestión, rastreo y cumplimiento de políticas de copias de seguridad de las bases de datos.

### 🚀 Capacidades
*   **Rutas Exclusivas:** Las rutas de respaldo ahora están vinculadas a un servidor específico en la CMDB para mejor organización.
*   **Descubrimiento de Respaldos (Discovery):** Rastreo remoto vía SSH de archivos físicos (`.sql`, `.dmp`, `.archive`) y sincronización con el inventario CMDB.
*   **Políticas de Retención:** Asignación de reglas de ciclo de vida para diferenciar backups diarios, semanales, etc.
*   **Retention Manager:** Purga automática nocturna de registros que superen el tiempo de retención permitido.

### 🔌 Endpoints de Respaldos
- **POST, GET, DELETE** `/tipo-respaldo/`, `/tipo-almacenamiento/`
- **POST, GET, PUT, DELETE** `/rutas-respaldo/`
- **GET** `/rutas-respaldo/servidor/{servidor_id}` (Filtrado por servidor)
- **POST** `/monitoring/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}`
- **POST** `/monitoring/inventory/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}` (Descubrimiento global por servidor)
- **POST, GET** `/respaldos/` (Incluye historial)

---

## 🛡️ Núcleo: Seguridad, Auditoría y Sistema Base
Base sobre la cual corren todos los módulos y que garantiza el control de las operaciones SRE.

### 🚀 Capacidades
*   **Auditoría SRE:** Bitácora inmutable de cada acción, inicio de sesión o modificación.
*   **Control de Accesos:** Gestión de Usuarios y Roles protegidos con JWT.

### 🔌 Endpoints Core
**Documentación y Salud del Sistema:**
- **GET** `/openapi.json`, `/docs`, `/redoc`, `/health/postgres`, `/ping`, `/`

**Usuarios y Roles:**
- **POST** `/users/login`, `/users/logout`
- **POST, GET, PUT, DELETE** `/users/` (Incluye `/users/me`, búsqueda por ID/email y reset de password)
- **POST, GET, DELETE** `/roles/`

**Auditoría:**
- **POST, GET, DELETE** `/audit-types/`
- **GET** `/audit-logs/` (Incluye búsqueda por Bitácora ID)

---

## 🛠️ Stack Tecnológico
*   **Backend:** FastAPI (Python 3.14) + SQLAlchemy 2.0
*   **Motor de Tareas:** APScheduler (Async + ThreadPool)
*   **Base de Datos:** PostgreSQL 16
*   **Gestión SSH:** Paramiko (Algoritmos Legacy habilitados)
*   **DevOps:** Docker (Multi-stage) + `uv`
