# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para la observabilidad de infraestructura crítica (SRE), gestión automatizada de respaldos y monitoreo inteligente multi-motor.

---

## 📁 Estructura del Proyecto y Módulos

El proyecto sigue una **Arquitectura Simétrica por Dominios**, dividido funcionalmente en tres módulos principales y un núcleo de seguridad base:

### 1️⃣ Módulo de Búsqueda de Activos (Gestión de Inventario CMDB)
Centraliza el registro, organización y descubrimiento de toda la infraestructura tecnológica.
* **Importación Masiva:** Alta de servidores, instancias y credenciales vía CSV con cifrado automático (AES-256).
* **Auto-Descubrimiento Inteligente:** Sincronización automática de bases de datos para MySQL, Oracle y MongoDB.
* **Búsqueda Global de Activos:** Endpoint unificado que agrupa servidores e instancias con sus bases de datos y tamaños.
* **Gestión de Particiones:** Descubrimiento remoto vía SSH (`df -h`) y registro de puntos de montaje.

### 2️⃣ Módulo de Monitoreo Activo (Observabilidad SRE)
Vigilancia en tiempo real de recursos y servicios mediante tareas programadas asíncronas.
* **Monitoreo de Host (SSH):** Extracción de CPU, RAM, Disco y Uptime con soporte para Legacy RHEL 4/5.
* **Monitoreo Modular por Criticidad:** Homologación con Oracle de observabilidad por grupos para MySQL 5 (`information_schema`/`performance_schema`), MySQL 8 (`performance_schema`) y MongoDB (`ping`/`serverStatus`), recolectando información adaptada dinámicamente según la criticidad (Bajo: Grupo A; Medio: Grupos A+B; Alto/Crítico: Grupos A+B+C).
* **DB Connection Pooling:** Reutilización de conexiones persistentes para MySQL, Oracle y MongoDB.
* **Alcance Selectivo:** Configuración por servidor para monitorear solo Hardware, solo DB o ambos.
* **Live Cache:** Métricas en tiempo real en RAM para Dashboard sin latencia.
* **Monitoreo Silencioso:** Persistencia en DB solo bajo umbrales críticos (> 90%).

### 3️⃣ Módulo de Automatización de Respaldos
Gestión, rastreo y cumplimiento de políticas de copias de seguridad.
* **Descubrimiento de Respaldos:** Rastreo remoto vía SSH de archivos físicos (`.sql`, `.dmp`, `.archive`).
* **Retention Manager:** Purga automática nocturna (4:00 AM) de registros expirados según política.
* **Políticas Flexibles:** Configuración de retención por días y frecuencia por horas.

---

## 🔌 Referencia de Endpoints de la API

Las rutas de la API están estructuradas de forma organizada bajo el prefijo principal `/sgir/v1/` para segmentar adecuadamente el comportamiento operativo y el acceso a los datos:

*   **`/crud` (Operaciones Transaccionales Básicas):** Agrupa todos los endpoints CRUD del sistema base (Seguridad, Catálogos Base, CMDB de Infraestructura, Políticas de Respaldo, Históricos de Auditoría y Métricas de Monitoreo).
*   **`/m1` (Módulo 1 - Monitoreo Activo de Hosts):** Contiene la lógica operativa y de salud del monitoreo de hardware (CPU, RAM, Disco, estados de salud y tests de conectividad SSH / ping).
*   **`/m2` (Módulo 2 - Sincronización de Activos):** Centraliza las tareas operativas de sincronización y auto-descubrimiento en paralelo de bases de datos para motores activos (MySQL, Oracle, MongoDB).
*   **`/m3` (Módulo 3 - Descubrimiento y Gestión de Respaldos):** Contiene las operaciones y tareas programadas (como el Retention Manager) para rastrear archivos físicos de respaldos vía SSH en servidores remotos y purgar copias de seguridad expiradas.

### Lista de Endpoints de Activos e Infraestructura
* **Catálogos del Sistema:** `POST, GET, DELETE` `/estados/`, `/criticidad/`, `/tipo-acceso/`
* **Servidores:**
  * `POST` `/servidores/import-bulk` (Carga masiva por CSV)
  * `POST, GET, PUT, DELETE` `/servidores/` (Incluye búsqueda por IP y ID)
  * `GET` `/servidores/ip/{ip}` (Búsqueda rápida por IP)
  * `GET` `/servidores/ping/{ip_server}` (Test de conectividad básica en Docker)
* **Particiones:**
  * `POST, GET, DELETE` `/particiones/`
  * `POST` `/particiones/register-upsert` (Registro inteligente de puntos de montaje)
  * `GET` `/particiones/servidor/{servidor_id}` (Listar particiones por servidor)
* **Instancias y Bases de Datos:**
  * `POST, GET` `/dbms/`
  * `POST, GET, DELETE` `/instancias/`
  * `GET` `/instancias/servidor/{servidor_id}`
  * `POST, GET, DELETE` `/bases-de-datos/`
  * `GET` `/bases-de-datos/servidor/{servidor_id}`
  * `GET` `/bases-de-datos/search` (Búsqueda enriquecida por nombre)
  * `GET` `/bases-de-datos/filter` (Filtrado por nombre e IP del servidor)
* **Reportes Globales (Públicos):**
  * `GET` `/assets/pdf` (Generar reporte PDF de inventario de bases de datos con diseño de la UAEMex)
  * `GET` `/assets/csv` (Generar reporte CSV del inventario en formato Excel con BOM)
* **Credenciales y Pruebas de Conexión:**
  * `POST, GET, PUT, DELETE` `/credenciales/`
  * `GET` `/credenciales/servidor/{servidor_id}`
  * `POST` `/credenciales/test-ssh/{id_servidor}/{id_credencial}`
  * `POST` `/instancias/test-db/{id_instancia}/{id_credencial}`
  * `POST` `/conexion/test/db/{motor}`
  * `POST` `/conexion/test/db/oracle/legacy` (Prueba de conexión legacy vía SSH + sqlplus local)
  * `POST` `/conexion/test/db/oracle/no-legacy` (Prueba de conexión estándar TCP thin mode)
  * `POST` `/conexion/test/ssh`

### Lista de Endpoints de Monitoreo y Salud
* **Gestión de Métricas e Inventario:**
  * `GET` `/monitoring/inventory/assets` (Búsqueda de activos agrupada por instancia)
  * `POST` `/monitoring/inventory/discover/{instancia_id}/{credencial_id}` (Sync de BDs)
  * `POST` `/monitoring/inventory/discover-all` (Sincronización masiva en paralelo)
  * `GET` `/monitoring/inventory/summary/{servidor_id}`
  * `POST, GET, DELETE` `/tipo-metrica/`, `/nivel-alerta/`
  * `POST` `/metricas/`
  * `POST, GET, PUT` `/alertas/` (Alertas activas, resueltas, hoy y recientes)
  * `GET` `/alertas/today` (Alertas del día actual)
  * `GET` `/alertas/recent` (Últimas alertas del sistema)
* **Gestión del Scheduler y Salud:**
  * `GET` `/monitoring/host/scheduler/status`
  * `POST` `/monitoring/host/scheduler/pause` / `/monitoring/host/scheduler/resume`
  * `POST` `/monitoring/host/scheduler/trigger-backup-retention` (Limpieza manual)
  * `GET` `/monitoring/host/global-summary`
  * `GET` `/monitoring/host/live-cache` (Métricas compactas en RAM)
  * `GET` `/monitoring/host/health-status/{server_id}`
  * `GET` `/monitoring/host/discover-filesystems/{servidor_id}` (df -h vía SSH)
  * `GET` `/monitoring/host/{server_id}/{cred_id}` (Ejecución ad-hoc)
* **Monitoreo Modular por Criticidad (MySQL & MongoDB):**
  * `GET` `/m1/mysql5/modular/{id_instancia}/{id_credencial}` (Monitoreo modular por criticidad MySQL 5)
  * `GET` `/m1/mysql8/modular/{id_instancia}/{id_credencial}` (Monitoreo modular por criticidad MySQL 8)
  * `GET` `/m1/mongodb/modular/{id_instancia}/{id_credencial}` (Monitoreo modular por criticidad MongoDB)

### Lista de Endpoints de Respaldos
* **Configuraciones:** `POST, GET, DELETE` `/tipo-respaldo/`, `/tipo-almacenamiento/`
* **Rutas de Respaldo:**
  * `POST, GET, PUT, DELETE` `/rutas-respaldo/`
  * `GET` `/rutas-respaldo/servidor/{servidor_id}`
* **Políticas y Respaldos:**
  * `POST` `/politicas-respaldo/` (CRUD de políticas)
  * `POST` `/asignacion-politica/` (Vincular política a BD)
  * `POST` `/respaldos/` (Registro de ejecución)
  * `GET` `/respaldos/historial` (Historial de backups por BD)
  * `POST` `/monitoring/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}`
  * `POST` `/monitoring/inventory/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}`

---

## 📊 Especificación de Protocolo: Live Cache (Compact Pulse)

`cpu|ram|discos|uptime|timestamp`
*Ejemplo:* `10.5|45.2|/:30.0,u01:80.5|12.5|1715085600`

---

## 🧪 Pruebas de Integración en Red (Targeting Docker)

Para validar esta arquitectura sin emulación en memoria, las pruebas están diseñadas para conectarse directamente al contenedor activo de Docker en `http://localhost:8000` mediante peticiones HTTP reales a través de `httpx`:

*   **[`tests/00_base.py`](file:///home/angel/src/titulacion/sgir_backend/tests/00_base.py):** Registra inicialmente en la base de datos de Docker al usuario administrador maestro (`admin@admin.com` / `123Nokia`) con el rol de Admin (ID=1).
*   **[`tests/01_basic_test_api.py`](file:///home/angel/src/titulacion/sgir_backend/tests/01_basic_test_api.py):** Verifica la disponibilidad de la API, el inicio de sesión OAuth2, el estado de salud de PostgreSQL (`/m1`), y flujos de lectura CRUD sobre catálogos.
*   **[`tests/crud/test_insert.py`](file:///home/angel/src/titulacion/sgir_backend/tests/crud/test_insert.py):** Realiza un flujo integral en cascada que valida el flujo de creación de todas las entidades del sistema satisfaciendo la integridad referencial.
*   **[`tests/m1/test_register_containers.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m1/test_register_containers.py):** Realiza el registro y la inicialización automática de los 7 contenedores de base de datos y servidores SSH locales de tu laboratorio.
*   **[`tests/m1/test_oracle_modular_monitoring.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m1/test_oracle_modular_monitoring.py):** Valida de forma secuencial el monitoreo modular de Oracle, alternando el nivel de criticidad del servidor para probar cada grupo de métricas.
*   **[`tests/m1/test_modular_db_monitoring.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m1/test_modular_db_monitoring.py):** Valida de forma secuencial e integral el monitoreo modular por criticidades en MySQL 5, MySQL 8 y MongoDB.
*   **[`tests/m1/test_bulk_servers_monitoring.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m1/test_bulk_servers_monitoring.py):** Simula una carga de escala real del inventario del laboratorio y valida el desempeño de auto-descubrimiento y live-cache.
*   **[`tests/m1/test_oracle_legacy_endpoint.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m1/test_oracle_legacy_endpoint.py):** Valida el registro e invocación del endpoint de prueba de conexión legacy para Oracle 10g usando SSH y variables de entorno.

---

## 🛠️ Stack Tecnológico
*   **Backend:** FastAPI (Python 3.14) + SQLAlchemy 2.0
*   **Motor de Tareas:** APScheduler (Async + ThreadPool)
*   **Base de Datos:** PostgreSQL 16
*   **Gestión SSH:** Paramiko (SSH Pooling + Keep-Alive)
*   **Gestión DB:** SQLAlchemy (Connection Pooling) + PyMongo
*   **DevOps:** Docker (Multi-stage) + `uv`

---

## 📅 Historial de Progreso del Proyecto

### 📅 Fecha: 1 de Mayo, 2026 (Endpoints de Conexión Dinámica y Estabilidad)
*   **Test de Conexión Independiente (Raw Payload)**: Creación de `/conexion/test/db/{motor}` y `/conexion/test/ssh` para validar credenciales sin persistencia en DB.
*   **Monitoreo Multi-Partición (SSH)**: Implementación de la tabla `servidor_particion`.
*   **Importación Masiva (CSV v2)**: Soporte de formato para particiones.
*   **Refactorización de APIs de Infraestructura**: Búsqueda granular por ID e IP.

### 📅 Fecha: 5 de Mayo, 2026 (Arquitectura de Observabilidad y Rutas Exclusivas)
*   **Refactor de Rutas de Respaldo (Modelo v2)**: Exclusividad por servidor añadiendo `id_servidor` a `RutaRespaldo`.
*   **Simplificación de Sesiones de Monitoreo**: Desacoplamiento de credenciales eliminando `id_credencial` de `Monitoreo`.
*   **Optimización del Orquestador SSH**: Mapeo de puertos dinámico (puerto en IP, ej: `:2224`) y compatibilidad con DNS internos de contenedores.
*   **Scheduler con Lista Blanca (Whitelist)**: Procesamiento exclusivo de servidores previamente activados.
*   **API de Métricas en Tiempo Real**: Endpoint `/monitoring/host/live-cache` para métricas en RAM.

### 📅 Fecha: 6 de Mayo, 2026 (Endpoint de Ping y Estabilidad en Docker)
*   **Ping de Servidor**: Endpoint `/servidores/ping/{ip_server}` con privilegios no privilegiados de `icmplib` para contenedores.
*   **Infraestructura y DevOps**: Inclusión de `iputils-ping` en stage runtime de Docker.
*   **Herramientas de Validación (SRE Tests)**: `tests/test_ping_server.py` y `tests/test_live_cache.py`.

### 📅 Fecha: 7 de Mayo, 2026 (Protocolo Compact Pulse y SSH Pooling)
*   **Protocolo Compact Pulse**: Optimización de red serializada por tuberías (`cpu|ram|disks|uptime|timestamp`), ahorrando un ~75% de ancho de banda.
*   **SSH Connection Pooling**: Creación de un pool global de conexiones reutilizables con Keep-Alive de 30s, reduciendo recolección a <100ms.

### 📅 Fecha: 8 de Mayo, 2026 (Alcance de Monitoreo, DB Pooling e Inventario Global)
*   **Selección de Alcance (Alcance de Monitoreo)**: Control asíncrono con flags `monitoreo_host` y `monitoreo_db` en `Servidor`.
*   **Persistencia de Conexiones (DB Pooling)**: Reutilización de SQLAlchemy Engines y Clientes de MongoDB en ciclos del scheduler.
*   **Auto-Descubrimiento Extendido**: Extracción de bases de datos/esquemas automáticamente para Oracle y MongoDB.
*   **Endpoint de Búsqueda de Activos (Global CMDB)**: Endpoint unificado `/monitoring/inventory/assets`.
*   **Automatización de Respaldos (Retention Manager)**: Purgas programadas de respaldos obsoletos a las 4:00 AM.

### 📅 Fecha: 10 de Mayo, 2026 (Endpoints de Alertas Temporales y Auditoría)
*   **Consultas Temporales de Alertas**: Endpoints `/alertas/today` y `/alertas/recent`.
*   **Auditoría y Trazabilidad**: Validación de logs de auditoría mediante `/audit-logs/`.

### 📅 Fecha: 21 de Mayo, 2026 (Monitoreo Modular por Criticidad para MySQL y MongoDB)
*   **Monitoreo Modular Basado en Criticidad**: Homologación con Oracle en Grupos A (Conectividad), B (Recursos) y C (Performance) determinado por la criticidad asignada en MySQL 5, 8 y MongoDB.
*   **Escapado de Contraseñas (URL-Encoding)**: Corrección en `dynamic_db_core.py` usando `urllib.parse.quote_plus` para contraseñas con caracteres especiales (ej. `$`).

### 📅 Fecha: 22 de Mayo, 2026 (Monitoreo Masivo en Paralelo y Pruebas SRE de Carga)
*   **Auto-Descubrimiento Asíncrono en Paralelo**: Sincronización masiva concurrente de toda la infraestructura mediante hilos en `/discover-all`.
*   **Suite de Pruebas de Carga SRE**: Test automatizado de escala real (`test_bulk_servers_monitoring.py`) con OAuth2.

### 📅 Fecha: 23 de Mayo, 2026 (Integración Oracle Legacy y Pruebas Independientes)
*   **Endpoints Independientes de Oracle**: `/test/db/oracle/legacy` (SSH + `sqlplus` local cargando `.bash_profile`) y `/test/db/oracle/no-legacy` (TCP Thin Mode).
*   **Sourcing Completo de Entorno SSH**: Integración de variables de entorno en el fallback SSH de `oracle_monitoring_service.py`.

---

## 📅 Cambios Recientes (26 de Mayo, 2026)

### 1️⃣ Ampliación de la Tabla `Politica_de_Respaldo`
Se modificó la estructura lógica de políticas para soportar planificaciones avanzadas alineadas a crontabs locales y scripts remotos:
*   **Modelo Físico y ORM:** Se agregaron las columnas `expression_cron VARCHAR(100)`, `hora_ejecuccion TIME`, `dias_semana VARCHAR(50)` y `script_path VARCHAR(512)` en `modelo-logico.sql` y `app/models/backup_models.py`.
*   **Validación de API:** Se actualizaron los esquemas Pydantic `PoliticaRespaldoBase` y `PoliticaRespaldoUpdate` en `backup_schemas.py` para recibir estos parámetros de forma opcional.
*   **Efecto en Endpoints:** Todos los endpoints CRUD bajo `/sgir/v1/crud/politicas-respaldo/` ahora aceptan y devuelven estas variables en su payload JSON de manera automatizada.

### 2️⃣ Re-estructuración y Ciclo de Vida en la Tabla `Respaldo`
Se reformuló la tabla de históricos de ejecución para dotar a la plataforma de observabilidad completa sobre el estado físico, ubicación e integridad de los archivos de backup:
*   **Modelo Físico y ORM:** Se eliminó la columna rígida `id_ruta_respaldo`, se flexibilizó `id_credencial` para permitir valores `NULL`, y se agregaron las siguientes columnas en `modelo-logico.sql` y `app/models/backup_models.py`:
    *   `fecha_descubrimiento TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP` (fecha en que el escaneo detecta el archivo).
    *   `nombre_archivo VARCHAR(255)` (nombre exacto del dump).
    *   `path_fisico_origen VARCHAR(512)` (ruta inicial en el servidor de base de datos).
    *   `ubicacion_actual VARCHAR(50) DEFAULT 'Origen'` (estado del ciclo físico: `'Origen'`, `'Descargado'`, `'Replica'`).
    *   `ip_almacenado_actual VARCHAR(50)` (IP del host donde reside el archivo físico actualmente).
    *   `path_fisico_actual VARCHAR(512)` (ruta del archivo en el host actual).
    *   `metadata_tecnica JSONB DEFAULT '{}'::jsonb` (detalles y logs del motor).
*   **Validación de API:** Se actualizó `RespaldoBase` en `backup_schemas.py` sincronizando los nuevos campos de forma opcional y removiendo la ruta estática obsoleta.
*   **Lógica de Descubrimiento SSH:** Se modificó la función de descubrimiento asíncrono `run_integrated_file_discovery` en `ssh_service.py` para construir e insertar las instancias de `Respaldo` mapeando automáticamente los archivos encontrados en red a este nuevo diseño dinámico.
*   **Pruebas de Integración:** Se adaptó el payload de la suite de pruebas `test_11_insert_respaldo` en `tests/crud/test_insert.py` para garantizar retrocompatibilidad.

### 3️⃣ Reportes de Inventario Global de Activos (30 de Mayo, 2026)
Se diseñaron e implementaron endpoints públicos y no autenticados para permitir a los usuarios descargar reportes de inventario global consolidados:
*   **Endpoint PDF (`GET /sgir/v1/assets/pdf`):** Genera dinámicamente un reporte formal en formato A4 con WeasyPrint y Jinja2, utilizando la identidad institucional de la UAEMex (colores verde y oro, celdas limpias, badges temáticos por RDBMS con MySQL en azul, MongoDB en verde y Oracle en rojo). Se eliminó la sección rígida "Tipo de Formato" del panel de metadatos, configurando un `colspan="3"` en el campo de usuario generador. Dispara sincronización en vivo (`run_bulk_inventory_sync`) en cada llamado con fallback automático.
*   **Endpoint CSV (`GET /sgir/v1/assets/csv`):** Exporta el inventario de bases de datos completo codificado en `utf-8-sig` (con BOM) para asegurar compatibilidad instantánea y correcta visualización de acentos y caracteres especiales en Microsoft Excel.
*   **Infraestructura y Docker:** Se añadieron y configuraron en el entorno virtual y Docker (`pyproject.toml` / `uv.lock`) las librerías `weasyprint`, `jinja2` y `markupsafe`, instalando las dependencias nativas del compilador de PDFs (Cairo, Pango, GObject) dentro de la imagen de producción `sgir-backend`.
*   **Mapeo y Validación Relacional:** Se verificó la consistencia relacional de la tabla `Politica_de_Respaldo` (`modelo-logico.sql`) con los esquemas Pydantic y el ORM de SQLAlchemy, garantizando coincidencia absoluta en campos complejos (incluyendo el mapeo exitoso de `hora_ejecuccion`).

