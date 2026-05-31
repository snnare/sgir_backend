# Resumen de Estado del Proyecto - SGIR (Actualizado Mayo 2026)

Este documento registra los avances, decisiones técnicas, lógica de negocio incorporada y estado de los repositorios durante la sesión actual para garantizar la continuidad del desarrollo del sistema **SGIR**.

---

## 🏛️ Contexto y Stack Tecnológico
*   **Backend:** FastAPI (Python 3.14) + SQLAlchemy 2.0.
*   **Frontend:** React (Vite, TypeScript, TailwindCSS/Vanilla CSS).
*   **Base de Datos:** PostgreSQL 16 (CMDB, Monitoreo y Transaccional).
*   **Seguridad:** Encriptación AES-256 para contraseñas de infraestructura y OAuth2 JWT.
*   **Orquestación SSH:** Paramiko con Connection Pooling (Keep-Alive de 30s) y soporte multiformato.

---

## 🚀 Logros y Cambios Clave de la Sesión Actual

### 1. Robustecimiento del Motor de Descubrimiento (Múltiples Extensiones)
*   **Decisión de Diseño:** Para admitir respaldos empaquetados o comprimidos por los administradores de sistemas en red, se amplió la búsqueda por RDBMS.
*   **Ampliación del `extension_map`:**
    *   **PostgreSQL / MySQL:** `[".sql", ".sql.gz", ".tar", ".zip", ".gz"]`
    *   **Oracle Database:** `[".dmp", ".dmp.gz", ".tar", ".zip", ".gz"]`
    *   **MongoDB:** `[".archive", ".tar.gz", ".tar", ".zip", ".gz"]`
*   **Lógica de Búsqueda SSH (Deduplicación):** Modificada en `run_integrated_file_discovery` dentro de [`ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py). El sistema ahora busca concurrentemente cada extensión en la ruta configurada, consolida la lista y **deduplica los archivos por su ruta absoluta en memoria** antes de ejecutar el auto-mapeo hacia las bases de datos de la CMDB.

### 2. Auto-Descubrimiento Global de Respaldos (Masa)
*   **Implementación del Servicio:** Creado `run_bulk_backups_discovery` en [`ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py).
    *   Filtra y itera todas las `RutaRespaldo` activas que cuenten con un servidor que posea credenciales SSH vigentes.
    *   Por cada servidor, obtiene todas sus instancias DBMS registradas.
    *   Invoca la lógica de escaneo y mapeo por instancia de forma automatizada.
    *   Registra una bitácora global de auditoría (`id_tipo_evento = 6`).
*   **Endpoint API expuesto:** `POST /sgir/v1/m3/inventory/discover-all-backups` registrado en el enrutador [`inventory_discovery_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/monitoring/inventory_discovery_routes.py).

### 3. Endpoint de Credenciales por Dirección IP
*   **Lógica de Negocio:** Para facilitar y optimizar la recuperación en frontend, se implementó `read_credentials_by_server_ip` en [`credencial_acceso_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/infrastructure/credencial_acceso_routes.py).
*   **Endpoint API:** `GET /sgir/v1/crud/credenciales/servidor/ip/{direccion_ip}`. Busca y asocia directamente el servidor IP sin requerir flujos intermedios del cliente.

### 4. Corrección de Bug Crítico de Red en el Frontend (404 Prefijos Duplicados)
*   **Diagnóstico:** Axios (`client.ts`) tiene configurado `baseURL: import.meta.env.VITE_API_URL` (que se lee como `/api/sgir/v1`). Al llamar endpoints que contenían `/sgir/v1/` hardcodeado en la cadena del path, Axios duplicaba el prefijo, provocando un error `404 Not Found` en el servidor de desarrollo de Vite.
*   **Soluciones Aplicadas en Frontend:**
    *   **[`monitoringService.ts`](file:///home/angel/src/titulacion/sgir_frontend/src/api/monitoringService.ts):** Cambiado `/sgir/v1/m1/db/live-cache` a `/m1/db/live-cache`.
    *   **[`databaseService.ts`](file:///home/angel/src/titulacion/sgir_frontend/src/api/databaseService.ts):** Removidos los prefijos `/sgir/v1` en sus 4 enrutados de CMDB (`/m2/...`).

---

## 🔒 Control de Cambios e Integración (Git Commit)

Ambos repositorios se encuentran completamente limpios, sincronizados y subidos a sus respectivas ramas remotas en GitHub:

1.  **Backend (`sgir_backend`):**
    *   **Commit:** `feat(backups): extend RDBMS backup extensions (.gz, .tar, .zip) and add global backups auto-discovery endpoint, add credentials by IP route` (Exitosamente subido a `origin/master`).
2.  **Frontend (`sgir_frontend`):**
    *   **Commit:** `fix(api): remove duplicated /sgir/v1 API prefix from frontend services` (Exitosamente subido a `origin/master`).

---

## 📝 Próximos Pasos Recomendados

### 1. Robustez ante Ficheros Gigantes o Rutas Inaccesibles
*   Asegurar un timeout controlado en Paramiko cuando se buscan múltiples extensiones en directorios de red muy extensos (ej. NFS compartido saturado).

### 2. Pruebas de Carga de Auto-Descubrimiento
*   Validar el consumo de memoria del backend al ejecutar `POST /sgir/v1/m3/inventory/discover-all-backups` cuando existen decenas de servidores y cientos de bases de datos registradas en paralelo.
