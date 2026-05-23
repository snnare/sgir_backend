# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para la observabilidad de infraestructura crítica (SRE), gestión automatizada de respaldos y monitoreo inteligente multi-motor.

## 📁 Estructura del Proyecto

El proyecto sigue una **Arquitectura Simétrica por Dominios**, dividido funcionalmente en tres módulos principales y un núcleo de seguridad base:

---

## 1️⃣ Módulo de Búsqueda de Activos (Gestión de Inventario CMDB)
Centraliza el registro, organización y descubrimiento de toda la infraestructura tecnológica.

### 🚀 Capacidades
*   **Importación Masiva:** Alta de servidores, instancias y credenciales vía CSV con cifrado automático (AES-256).
*   **Auto-Descubrimiento Inteligente:** Sincronización automática de bases de datos para MySQL, Oracle y MongoDB.
*   **Búsqueda Global de Activos:** Endpoint unificado que agrupa servidores e instancias con sus bases de datos y tamaños.
*   **Gestión de Particiones:** Descubrimiento remoto vía SSH (`df -h`) y registro de puntos de montaje.

### 🔌 Endpoints de Activos e Infraestructura
**Catálogos del Sistema:**
- **POST, GET, DELETE** `/estados/`, `/criticidad/`, `/tipo-acceso/`

**Infraestructura (Servidores, Particiones, DBMS):**
- **POST** `/servidores/import-bulk`
- **POST, GET, PUT, DELETE** `/servidores/` (Incluye búsqueda por IP y ID)
- **GET** `/servidores/ip/{ip}` (Búsqueda rápida por IP)
- **GET** `/servidores/ping/{ip_server}` (Test de conectividad básica en Docker)
- **POST, GET, DELETE** `/particiones/`
- **POST** `/particiones/register-upsert` (Registro inteligente de puntos de montaje)
- **GET** `/particiones/servidor/{servidor_id}` (Listar particiones por servidor)
- **POST, GET** `/dbms/`
- **POST, GET, DELETE** `/instancias/`
- **GET** `/instancias/servidor/{servidor_id}` (Listar instancias por servidor)
- **POST, GET, DELETE** `/bases-de-datos/`
- **GET** `/bases-de-datos/servidor/{servidor_id}` (Listar BDs por servidor)
- **GET** `/bases-de-datos/search` (Búsqueda enriquecida por nombre)
- **GET** `/bases-de-datos/filter` (Filtrado por nombre e IP del servidor)

**Credenciales y Pruebas de Conexión:**
- **POST, GET, PUT, DELETE** `/credenciales/`
- **GET** `/credenciales/servidor/{servidor_id}` (Listar credenciales de un servidor)
- **POST** `/credenciales/test-ssh/{id_servidor}/{id_credencial}`
- **POST** `/instancias/test-db/{id_instancia}/{id_credencial}`
- **POST** `/conexion/test/db/{motor}`
- **POST** `/conexion/test/ssh`

---

## 2️⃣ Módulo de Monitoreo Activo (Observabilidad SRE)
Vigilancia en tiempo real de recursos y servicios mediante tareas programadas asíncronas.

### 🚀 Capacidades
*   **Monitoreo de Host (SSH):** Extracción de CPU, RAM, Disco y Uptime con soporte para Legacy RHEL 4/5.
*   **Monitoreo Modular por Criticidad:** Homologación con Oracle de observabilidad por grupos para MySQL 5 (`information_schema`/`performance_schema`), MySQL 8 (`performance_schema`) y MongoDB (`ping`/`serverStatus`), recolectando información adaptada dinámicamente según la criticidad (Bajo: Grupo A; Medio: Grupos A+B; Alto/Crítico: Grupos A+B+C).
*   **DB Connection Pooling:** Reutilización de conexiones persistentes para MySQL, Oracle y MongoDB.
*   **Alcance Selectivo:** Configuración por servidor para monitorear solo Hardware, solo DB o ambos.
*   **Live Cache:** Métricas en tiempo real en RAM para Dashboard sin latencia.
*   **Monitoreo Silencioso:** Persistencia en DB solo bajo umbrales críticos (> 90%).

### 🔌 Endpoints de Monitoreo
**Gestión de Métricas e Inventario:**
- **GET** `/monitoring/inventory/assets` (Búsqueda de activos agrupada por instancia)
- **POST** `/monitoring/inventory/discover/{instancia_id}/{credencial_id}` (Sync de BDs)
- **POST** `/monitoring/inventory/discover-all` (Sincronización masiva en paralelo)
- **GET** `/monitoring/inventory/summary/{servidor_id}`
- **POST, GET, DELETE** `/tipo-metrica/`, `/nivel-alerta/`
- **POST** `/metricas/`
- **POST, GET, PUT** `/alertas/` (Alertas activas, resueltas, hoy y recientes)
- **GET** `/alertas/today` (Alertas del día actual)
- **GET** `/alertas/recent` (Últimas alertas del sistema)

**Gestión del Scheduler y Salud:**
- **GET** `/monitoring/host/scheduler/status`
- **POST** `/monitoring/host/scheduler/pause` / `/monitoring/host/scheduler/resume`
- **POST** `/monitoring/host/scheduler/trigger-backup-retention` (Limpieza manual)
- **GET** `/monitoring/host/global-summary`
- **GET** `/monitoring/host/live-cache` (Métricas compactas en RAM)
- **GET** `/monitoring/host/health-status/{server_id}`
- **GET** `/monitoring/host/discover-filesystems/{servidor_id}` (df -h vía SSH)
- **GET** `/monitoring/host/{server_id}/{cred_id}` (Ejecución ad-hoc)

**Monitoreo Modular por Criticidad (MySQL & MongoDB):**
- **GET** `/m1/mysql5/modular/{id_instancia}/{id_credencial}` (Monitoreo modular por criticidad MySQL 5)
- **GET** `/m1/mysql8/modular/{id_instancia}/{id_credencial}` (Monitoreo modular por criticidad MySQL 8)
- **GET** `/m1/mongodb/modular/{id_instancia}/{id_credencial}` (Monitoreo modular por criticidad MongoDB)

---

## 3️⃣ Módulo de Automatización de Respaldos
Gestión, rastreo y cumplimiento de políticas de copias de seguridad.

### 🚀 Capacidades
*   **Descubrimiento de Respaldos:** Rastreo remoto vía SSH de archivos físicos (`.sql`, `.dmp`, `.archive`).
*   **Retention Manager:** Purga automática nocturna (4:00 AM) de registros expirados según política.
*   **Políticas Flexibles:** Configuración de retención por días y frecuencia por horas.

### 🔌 Endpoints de Respaldos
- **POST, GET, DELETE** `/tipo-respaldo/`, `/tipo-almacenamiento/`
- **POST, GET, PUT, DELETE** `/rutas-respaldo/`
- **GET** `/rutas-respaldo/servidor/{servidor_id}`
- **POST** `/politicas-respaldo/` (CRUD de políticas)
- **POST** `/asignacion-politica/` (Vincular política a BD)
- **POST** `/respaldos/` (Registro de ejecución)
- **GET** `/respaldos/historial` (Historial de backups por BD)
- **POST** `/monitoring/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}`
- **POST** `/monitoring/inventory/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}`

---

## 🛡️ Núcleo: Seguridad, Auditoría y Sistema Base
Base sobre la cual corren todos los módulos.

### 🔌 Endpoints Core
- **Usuarios:** `/users/login`, `/users/logout`, `/users/me`, `/users/` (CRUD), `/roles/`
- **Auditoría:** `/audit-types/`, `/audit-logs/` (Bitácora inmutable)
- **Salud:** `/health/postgres`, `/ping`, `/openapi.json`

---

## 📊 Especificación de Protocolo: Live Cache (Compact Pulse)
`cpu|ram|discos|uptime|timestamp`
*Ejemplo:* `10.5|45.2|/:30.0,u01:80.5|12.5|1715085600`

## 🗺️ Estructura de Rutas de la API (Bajo `/sgir/v1`)

Las rutas de la API han sido estructuradas de forma organizada bajo el prefijo principal `/sgir/v1/` para segmentar adecuadamente el comportamiento operativo y el acceso a los datos:

*   **`/crud` (Operaciones Transaccionales Básicas):** Agrupa todos los endpoints CRUD del sistema base (Seguridad, Catálogos Base, CMDB de Infraestructura, Políticas de Respaldo, Históricos de Auditoría y Métricas de Monitoreo).
*   **`/m1` (Módulo 1 - Monitoreo Activo de Hosts):** Contiene la lógica operativa y de salud del monitoreo de hardware (CPU, RAM, Disco, estados de salud y tests de conectividad SSH / ping).
*   **`/m2` (Módulo 2 - Sincronización de Activos):** Centraliza las tareas operativas de sincronización y auto-descubrimiento en paralelo de bases de datos para motores activos (MySQL, Oracle, MongoDB).
*   **`/m3` (Módulo 3 - Descubrimiento y Gestión de Respaldos):** Contiene las operaciones y tareas programadas (como el Retention Manager) para rastrear archivos físicos de respaldos vía SSH en servidores remotos y purgar copias de seguridad expiradas.

---

## 🧪 Pruebas de Integración en Red (Targeting Docker)

Para validar esta arquitectura sin emulación en memoria, las pruebas están diseñadas para conectarse directamente al contenedor activo de Docker en `http://localhost:8000` mediante peticiones HTTP reales a través de `httpx`:

*   **[`tests/00_base.py`](file:///home/angel/src/titulacion/sgir_backend/tests/00_base.py):** Registra inicialmente en la base de datos de Docker al usuario administrador maestro (`admin@admin.com` / `123Nokia`) con el rol de Admin (ID=1).
*   **[`tests/01_basic_test_api.py`](file:///home/angel/src/titulacion/sgir_backend/tests/01_basic_test_api.py):** Verifica la disponibilidad de la API, el inicio de sesión OAuth2, el estado de salud de PostgreSQL (`/m1`), y flujos de lectura CRUD sobre catálogos.
*   **[`tests/crud/test_insert.py`](file:///home/angel/src/titulacion/sgir_backend/tests/crud/test_insert.py):** Realiza un flujo integral en cascada que valida el flujo de creación (`POST`/`INSERT`) de todas las entidades del sistema (Servidor, Partición, Credencial, Instancia DBMS, Base de Datos, Ruta de Respaldo, Políticas de Respaldo, Respaldo Histórico, Monitoreo y Alertas), satisfaciendo la integridad referencial y las claves foráneas de PostgreSQL.
*   **[`tests/m1/test_register_containers.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m1/test_register_containers.py):** Realiza el registro y la inicialización automática de los 7 contenedores de base de datos y servidores SSH locales de tu laboratorio.
*   **[`tests/m1/test_oracle_modular_monitoring.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m1/test_oracle_modular_monitoring.py):** Valida de forma secuencial el monitoreo modular de Oracle, alternando el nivel de criticidad del servidor (Bajo, Medio, Alto) para probar de manera exclusiva cada grupo de métricas (A, B y C).
*   **[`tests/m1/test_modular_db_monitoring.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m1/test_modular_db_monitoring.py):** Valida de forma secuencial e integral el monitoreo modular por criticidades en MySQL 5, MySQL 8 y MongoDB, alternando los niveles (Bajo, Medio, Alto) y verificando la consistencia en el retorno de los grupos específicos (A, B, C).
*   **[`tests/m1/test_bulk_servers_monitoring.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m1/test_bulk_servers_monitoring.py):** Simula una carga de escala real del inventario del laboratorio. Autentica vía OAuth2 (`admin@admin.com` / `123Nokia`), ejecuta el auto-descubrimiento en paralelo de esquemas (`discover-all`), verifica la consistencia de la caché y valida la descompresión y recuperación de datos del formato "Compact Pulse" en RAM.

---

## 🛠️ Stack Tecnológico
*   **Backend:** FastAPI (Python 3.14) + SQLAlchemy 2.0
*   **Motor de Tareas:** APScheduler (Async + ThreadPool)
*   **Base de Datos:** PostgreSQL 16
*   **Gestión SSH:** Paramiko (SSH Pooling + Keep-Alive)
*   **Gestión DB:** SQLAlchemy (Connection Pooling) + PyMongo
*   **DevOps:** Docker (Multi-stage) + `uv`

