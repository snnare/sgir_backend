# Resumen de Estado del Proyecto - SGIR (Actualizado: 7 de Junio, 2026)

Este documento registra los avances, decisiones técnicas, lógica de negocio incorporada y estado de los repositorios durante las sesiones de desarrollo para garantizar la continuidad del sistema **SGIR**.

---

## 🚀 Logros y Cambios Clave de la Sesión (7 de Junio, 2026)

### 1. Documentación de Rutas de Instancias DBMS
*   Se recopilaron y mapearon todas las rutas del Módulo CRUD relacionadas con `instancia_dbms` (catálogo y tests en caliente) para referencia del equipo de desarrollo, vinculando los controladores en [`instancia_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/infrastructure/instancia_routes.py) con sus servicios en [`infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py).

### 2. Estructuración de Módulos de la Aplicación
*   Se definió la arquitectura y alcance de los 4 módulos funcionales actuales: Módulo CRUD (Configuración), Módulo 1 (Observabilidad), Módulo 2 (Auto-Descubrimiento & CMDB) y Módulo 3 (Gestión y Automatización de Respaldos), además del submódulo de Reportes PDF/CSV.

### 3. Análisis de Ahorro y Eficiencia (ROI)
*   Se diseñó una estimación y tabla comparativa del ahorro de tiempo operativo al automatizar procesos. Se calculó que las tareas rutinarias de 2 horas diarias (25% de la jornada de 8 horas) se reducen a **5 minutos**, logrando un ahorro diario neto de **1h 55m (95.8% de optimización)**.

---

## 🚀 Logros y Cambios Clave de la Sesión (5 de Junio, 2026)

### 1. Robustez en Conexiones MySQL Legacy y Charset Fallback
*   **Problema de Charset (Error 1115):** Servidores MySQL antiguos (como 5.1) no soportan el charset `utf8mb4` por defecto del cliente PyMySQL, lo que lanzaba un error 500 genérico en las pruebas de conexión.
*   **Solución Híbrida Automática:**
    *   **Prueba de Conexión (`test_db_connection`):** Implementamos un bucle de fallback automático. Intenta primero conectar con `utf8mb4`, si falla con el código `1115`, reintenta automáticamente con `utf8` (y si este falla, con `latin1`), de forma completamente transparente.
    *   **Pool de Conexiones de SQLAlchemy (`get_rdbms_session`):** Aplicamos el mismo patrón en la inicialización del Engine de SQLAlchemy en el Connection Pool, permitiendo que las tareas del scheduler de monitoreo y sincronización de inventario conecten a cualquier MySQL antiguo de manera automática sin fallar.
    *   **Configuración por Defecto:** Se modificó `get_dynamic_url` para inicializar por defecto todas las conexiones MySQL con `utf8mb4`, permitiendo que la auto-detección y el fallback hagan el downgrade solo cuando sea estrictamente necesario.

### 2. Persistencia en la Detección Global de Respaldos (Módulo 3)
*   **Registro Automático en DB:** Modificamos los endpoints de descubrimiento de respaldos a nivel servidor (`run_server_integrated_file_discovery` y `run_custom_server_integrated_file_discovery`) para que persistan de forma automática los respaldos exitosos encontrados en disco dentro de la tabla `Respaldo` (siempre que tengan una política asignada).
*   **Prevención de Duplicados:** Añadimos una validación previa a la inserción en la base de datos para comprobar si el archivo de respaldo ya fue registrado, evitando registros redundantes al correr escaneos repetitivos.

### 3. Exposición de Endpoints CRUD para Instancias
*   **Nuevos Endpoints de Instancia:** Expusimos y completamos el CRUD del controlador de instancias (`instancia_routes.py` y `infrastructure_crud.py`):
    *   `GET /sgir/v1/crud/instancias/` (Listar todas las instancias del sistema).
    *   `PUT /sgir/v1/crud/instancias/{id_instancia}` (Actualización parcial de campos de instancia mediante `InstanciaUpdate`).
    *   `DELETE /sgir/v1/crud/instancias/{id_instancia}` (Eliminación lógica/física).
*   **Documentación de API:** Registramos y documentamos los nuevos endpoints del catálogo en el mapa de rutas general (`routes.md`).

### 4. Diagnóstico y Monitoreo del Servidor (Middleware Logs)
*   **Middleware de Logs:** Agregamos temporalmente un middleware HTTP y traceback logger a `app/main.py` para visualizar en caliente cada petición y ver exactamente la traza del error en caso de HTTP 500.

---

## 🚀 Logros y Cambios Clave de la Sesión (4 de Junio, 2026)

### 1. Auto-descubrimiento en Caliente de Instancias Oracle (`ORACLE_SID`)
*   **Comandos en Caliente:** Implementamos la ejecución de `ps -ef | grep smon | grep -v grep` vía SSH para descubrir dinámicamente los SIDs activos en servidores Oracle remotos.
*   **Registro Automático en CMDB:** Creamos la función `discover_and_register_oracle_instances` para crear y dar de alta de forma desatendida las instancias encontradas en PostgreSQL con sus respectivos `parametros_conexion = {"sid": sid}`.
*   **Nuevos Endpoints:**
    *   Integrado en el escaneo masivo `/m2/inventory/discover-all` para ejecutarse en la Fase 1.
    *   Nuevo endpoint individual por servidor: `POST /sgir/v1/m2/inventory/discover-server/{servidor_id}`.

### 2. Robustez y Fallback SSH para Sincronización Oracle
*   **Resolución del Error `DPY-4027`:** Al intentar sincronizar bases de datos en Oracle 10g/legacy, la librería del modo Thin fallaba. Implementamos un bypass o **fallback vía SSH** en `sync_databases_inventory` que abre una conexión SSH y ejecuta `sqlplus` de forma interna en el servidor para recuperar los esquemas locales usando el `ORACLE_SID` dinámico.
*   **Seguridad de Caracteres:** Envolvimos las credenciales ejecutadas en comillas simples (`'{db_user}/{db_password}'`) para proteger contraseñas que tengan caracteres especiales (como `$`) de ser evaluados por Bash.

### 3. Enriquecimiento del Historial de Auditoría (Audit Logs)
*   **Mapeo Relacional de Usuario:** Añadimos la relación `usuario = relationship("User")` al ORM de `Bitacora`.
*   **Esquema de Respuesta Enriquecido:** Modificamos `BitacoraResponse` en `audit_schemas.py` para devolver un objeto de usuario anidado (`usuario: Optional[UserMinResponse]`) que contiene el **`email`**, **`nombres`** y **`apellidos`** de quien realizó la acción, en lugar de solo su ID numérico.

### 4. Soporte para Respaldos Huérfanos/Desconocidos
*   **Listado Completo de Archivos:** Modificamos `run_integrated_file_discovery` y `run_server_integrated_file_discovery` en `ssh_service.py` para que los archivos encontrados en disco que no coincidan con bases de datos registradas en la CMDB se listen con `base_datos_id=0` y `nombre_base="Desconocida (<nombre_archivo>)"`. Esto evita que el frontend reciba listas vacías confusas cuando los archivos sí existen físicamente.

---

## 📋 Pendientes Críticos

1.  **[x] Resolver el Descubrimiento Vacío de Respaldos (Bases de Datos no emparejadas):**
    *   *Resuelto:* Modificamos los endpoints de escaneo a nivel instancia y servidor en [`ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py) para que, en caso de detectar archivos físicos en el servidor remoto que no coincidan con bases de datos registradas en la CMDB local, los listen como "Desconocidos/Huérfanos" (con `base_datos_id=0`) en lugar de ignorarlos.
2.  **[x] Auto-descubrimiento de Instancias Oracle (ORACLE_SID):**
    *   *Resuelto:* Implementamos la lógica para descubrir instancias activas mediante procesos `ora_smon` e insertarlas dinámicamente en la CMDB antes de la sincronización masiva y en el nuevo endpoint `/discover-server/{servidor_id}`.
3.  **Diagnosticar y resolver el error 500 al probar conexión con MySQL 5.x:**
    *   **Problema:** Al probar conexión a base de datos MySQL 5.x (`POST /conexion/test/db/mysql`), el backend retorna un HTTP 500 genérico.
    *   **Acciones Pendientes:**
        *   Revisar los logs del contenedor para identificar la causa raíz (timeout, credenciales, red o incompatibilidad de hash de contraseñas de MySQL 5.x antiguos).
        *   Refactorizar el controlador para capturar la excepción específica y retornar un mensaje HTTP controlado o descriptivo al frontend en vez de lanzar un error 500.

---

## 🏛️ Contexto y Stack Tecnológico
*   **Backend:** FastAPI (Python 3.14) + SQLAlchemy 2.0.
*   **Frontend:** React (Vite, TypeScript, TailwindCSS/Vanilla CSS).
*   **Base de Datos:** PostgreSQL 16 (CMDB, Monitoreo, Transaccional y Persistencia SRE).
*   **Seguridad:** Encriptación AES-256 para contraseñas de infraestructura y OAuth2 JWT.
*   **Orquestación SSH:** Paramiko con Connection Pooling (Keep-Alive de 30s) y soporte multiformato.

---

## 🚀 Logros y Cambios Clave de la Sesión (3 de Junio, 2026)

### 1. Alineación y Corrección de Mapeo Relacional (Discrepancias)
Comparamos el script de base de datos [`modelo-logico.sql`](file:///home/angel/src/titulacion/sgir_backend/modelo-logico.sql) contra los modelos del backend y corregimos dos discrepancias críticas:
*   **Tabla de Particiones:** Se modificó en [`infrastructure_models.py`](file:///home/angel/src/titulacion/sgir_backend/app/models/infrastructure_models.py#L51) la tabla de la clase `ServidorParticion` de `"servidor_particion"` a `"particion"` para que coincida exactamente con la definición del DDL.
*   **Ortografía de Columna en Políticas:** Se corrigió en el modelo [`backup_models.py`](file:///home/angel/src/titulacion/sgir_backend/app/models/backup_models.py#L40) y en los esquemas Pydantic [`backup_schemas.py`](file:///home/angel/src/titulacion/sgir_backend/app/schemas/backups/backup_schemas.py#L60-L75) el campo `hora_ejecuccion` (con doble 'c') a `hora_ejecucion` (con una sola 'c') para evitar fallos de persistencia en base de datos.

### 2. Creación e Integración de Pruebas para Módulo 3
*   **Script de Prueba Interactivo:** Se creó la carpeta [`tests/m3`](file:///home/angel/src/titulacion/sgir_backend/tests/m3) y el script [`test_discover_backups.py`](file:///home/angel/src/titulacion/sgir_backend/tests/m3/test_discover_backups.py).
*   **Flujo del Test:** Se conecta a la API local (`localhost:8000`), inicia sesión como administrador maestro (`admin@admin.com`/`123Nokia`), pide la IP de un servidor por consola, resuelve de forma automática sus relaciones (instancias DBMS, credenciales SSH, rutas de backup) y ejecuta el endpoint de auto-descubrimiento de copias de seguridad.

### 3. Diagnóstico y Corrección en Monitoreo Oracle Legacy (RHEL 4)
*   **Análisis del Fallo ORA-01034 / SP2-0306:** Se identificó que la tarea de monitoreo de base de datos fallaba al conectarse por SSH a la base de datos `DbEvapem` (IP `148.215.1.98`) debido a que el campo `parametros_conexion` de la instancia estaba vacío (`None`), lo cual forzaba a que el backend usara por defecto el SID `"ORCL"`.
*   **Efecto:** Al intentar conectarse a un SID inexistente en el host, `sqlplus` fallaba con `ORA-01034` y después entraba en un bucle leyendo el código SQL como datos de inicio de sesión (`SP2-0306` y `SP2-0157`).
*   **Corrección sugerida:** Actualizar `parametros_conexion` de la instancia en PostgreSQL para registrar la clave `"sid": "DbEvapem"`. Al hacer esto, el fallback de SSH funciona correctamente sin levantar ninguna alerta y recupera las métricas de Oracle 10g en silencio.
*   **Validación exitosa:** Se corrió el test de descubrimiento de respaldos para la IP `148.215.1.98` obteniendo un resultado `200 OK` con un conteo exitoso de 15 archivos físicos de respaldos `.dmp.gz`.

---

## 🚀 Logros y Cambios Clave de la Sesión Anterior (2 de Junio, 2026)

### 1. Robustecimiento y Consistencia de Reportes (RDBMS + Versión)
*   Modificamos los endpoints `/assets/pdf` y `/assets/csv` en [`app/routes/__init__.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/__init__.py) para recuperar y normalizar el tipo de motor de base de datos junto con su versión principal (ej. `"MySQL 8"`, `"MongoDB 6"`).

### 2. Conversión a Endpoints Offline
*   **Reporte CSV**: Modificamos `/assets/csv` para que trabaje de forma offline por completo, eliminando la llamada a sync por red.
*   **Reporte PDF Offline**: Se creó el endpoint `/assets/pdf-offline` para generar el PDF del inventario de bases de datos de forma instantánea a partir de la CMDB local (PostgreSQL).

### 3. Resumen Global de Políticas de Respaldo
*   **Endpoint API**: Se implementó `GET /sgir/v1/crud/politicas-respaldo/resumen-global` en [`politica_respaldo_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/backups/politica_respaldo_routes.py).

### 4. Nuevo Reporte de SLA, Incidentes SRE y Uptime
*   **Endpoint API**: Se implementó `GET /sgir/v1/assets/sre-sla-pdf` en [`app/routes/__init__.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/__init__.py).

### 5. Depuración y Limpieza de Carga Masiva (CSV)
*   Se eliminaron los endpoints de `/import-bulk` obsoletos y redundantes. El único endpoint activo es `POST /sgir/v1/crud/servidores/import-bulk`.
*   Se reescribió y depuró [`import_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/import_service.py).

### 6. Ordenamiento de Plantillas de Prueba (Mockups)
*   Se creó el directorio [`app/templates/reports/mockups`](file:///home/angel/src/titulacion/sgir_backend/app/templates/reports/mockups) para agrupar las vistas HTML.

---

## 📈 Mapeo de Módulos y Métricas de Eficiencia (Ahorro de Tiempo / ROI)

Asumiendo que realizar manualmente las tareas operativas de monitoreo e inventario sin **SGIR** consume un **25% de la jornada laboral de 8 horas (120 minutos diarios)**, a continuación se detalla la optimización de tiempo por cada módulo del sistema:

| Módulo de SGIR | Tarea Manual (Sin SGIR) | Tiempo Manual Estimado (Diario) | Solución Automatizada (Con SGIR) | Tiempo con SGIR (Diario) | Tiempo Ahorrado | % de Optimización |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: |
| **Módulo CRUD & Admin** | Registrar servidores, inventariar credenciales en archivos locales, resetear passwords y actualizar catálogos manualmente. | **15 min** *(0.25h)* | Formularios rápidos, importación masiva de infraestructura vía CSV y credenciales cifradas con AES-256. | **2 min** *(Visualización)* | **13 min** | **86.7%** |
| **Módulo 1: Observabilidad** | Conectarse por SSH o consola a cada base de datos (MySQL, Mongo, Oracle) para comprobar conectividad, estados de salud y métricas. | **30 min** *(0.50h)* | Endpoints unificados de salud en tiempo real (`GET /health-status`) y alertas centralizadas automáticas. | **1 min** *(Revisión del dashboard)* | **29 min** | **96.7%** |
| **Módulo 2: Auto-Descubrimiento** | Auditar manualmente qué instancias Oracle están activas en cada servidor, listar bases de datos y revisar tareas `cron` en disco. | **35 min** *(0.58h)* | Escaneo desatendido de procesos `ora_smon`, auto-registro en la CMDB local y lectura automatizada de archivos `crontab` vía SSH. | **1 min** *(Auditoría automática)* | **34 min** | **97.1%** |
| **Módulo 3: Respaldos** | Ingresar a directorios remotos, listar archivos, verificar tamaños en MB, validar hashes de integridad y borrar respaldos antiguos para liberar espacio. | **40 min** *(0.67h)* | Escaneo automático de archivos físicos remotos, registro dinámico de copias en DB (incluyendo huérfanas) y purga automática por políticas de retención. | **1 min** *(Revisión de logs)* | **39 min** | **97.5%** |
| **TOTAL** | **Gestión operativa y preventiva diaria de infraestructura de datos.** | **120 min** *(2.00h)* | **Ejecución y monitoreo centralizado.** | **5 min** | **115 min** *(1.92h)* | **95.8%** |

*   **Ahorro Semanal (L-V):** **9.58 horas** libres para tareas estratégicas (equivalente a más de un día completo de trabajo).
*   **Ahorro Mensual (20 días):** **38.3 horas** (casi una semana laboral recuperada).

---

## 🔒 Control de Cambios (Estado de Git)
*   Se han compilado exitosamente y libre de errores de sintaxis todos los archivos modificados de la sesión.
*   El backend y el scheduler procesan las tareas concurrentemente de forma estable.

---

## 📝 Próximos Pasos Recomendados

1.  **Validación del Frontend:**
    *   Asegurar que los formularios y esquemas del Front-end utilicen el campo corregido `hora_ejecucion` (en lugar de `hora_ejecuccion`) al crear o actualizar políticas de respaldo.
2.  **Sincronización del SID en CMDB:**
    *   Revisar que todas las instancias de Oracle registradas en la CMDB cuenten con el parámetro `"sid"` definido dentro del campo `parametros_conexion` para evitar fallos de fallback por SSH al usar el SID `"ORCL"`.
3.  **Continuar con la Documentación del Módulo 1**:
    *   Documentar el resto de los endpoints de observabilidad en formatos `.md`, `.txt` y `.docx`.
