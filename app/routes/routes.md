# 🗺️ SGIR API Routes Reference Map

This document lists all active routes in the SGIR backend categorized by operational modules: **CRUD (Core & Catalog Configuration)**, **Módulo 1 (Observabilidad & Salud)**, **Módulo 2 (CMDB & Descubrimiento)**, and **Módulo 3 (Gestión de Respaldos)**.

---

## 🛠️ Módulo CRUD
Contiene las operaciones del catálogo relacional y configuraciones base. El prefijo global de estos endpoints es `/sgir/v1/crud`.

### 🔑 Seguridad y Control de Acceso
*   **`POST`** `/users/`
    *   **Body requerido:**
        ```json
        {
          "nombres": "Juan",
          "apellidos": "Pérez",
          "email": "juan.perez@example.com",
          "password": "PasswordSeguro123",
          "id_rol": 2,
          "id_estado_usuario": 1
        }
        ```
*   **`POST`** `/users/login`
    *   **Body requerido (Form-Data / OAuth2 Flow):**
        ```ini
        username = juan.perez@example.com
        password = PasswordSeguro123
        ```
*   **`PUT`** `/users/{user_id}`
    *   **Body requerido:**
        ```json
        {
          "nombres": "Juan Modificado",
          "apellidos": "Pérez",
          "email": "juan.perez@example.com",
          "id_rol": 2,
          "id_estado_usuario": 1
        }
        ```
*   **`PUT`** `/users/{user_id}/password`
    *   **Body requerido:**
        ```json
        {
          "old_password": "PasswordSeguro123",
          "new_password": "NuevoPassword456"
        }
        ```
*   **`POST`** `/roles/`
    *   **Body requerido:**
        ```json
        {
          "nombre_rol": "Operador",
          "descripcion": "Rol con permisos operativos estándar"
        }
        ```
*   **`GET`** `/users/` $\rightarrow$ *Sin Body*
*   **`GET`** `/users/{user_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/users/email/{email}` $\rightarrow$ *Sin Body*
*   **`GET`** `/users/me` $\rightarrow$ *Sin Body (Requiere Bearer Token)*
*   **`DELETE`** `/users/{user_id}` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/users/email/{email}` $\rightarrow$ *Sin Body*
*   **`GET`** `/roles/` $\rightarrow$ *Sin Body*
*   **`GET`** `/roles/{role_id}` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/roles/{role_id}` $\rightarrow$ *Sin Body*

---

### 🖥️ Infraestructura y Servidores (CMDB CRUD)
*   **`POST`** `/servidores/`
    *   **Body requerido:**
        ```json
        {
          "nombre_servidor": "Svr-Linux-01",
          "direccion_ip": "192.168.1.50",
          "monitoreo_host": true,
          "monitoreo_db": false
        }
        ```
*   **`POST`** `/servidores/import-bulk`
    *   **Body requerido (Array JSON):**
        ```json
        [
          {
            "nombre_servidor": "Svr-Linux-02",
            "direccion_ip": "192.168.1.51",
            "monitoreo_host": true,
            "monitoreo_db": true
          }
        ]
        ```
*   **`PUT`** `/servidores/{servidor_id}`
    *   **Body requerido:**
        ```json
        {
          "nombre_servidor": "Svr-Linux-01-Prod",
          "direccion_ip": "192.168.1.50",
          "monitoreo_host": true,
          "monitoreo_db": true,
          "id_estado_servidor": 1
        }
        ```
*   **`POST`** `/particiones/`
    *   **Body requerido:**
        ```json
        {
          "punto_montaje": "/data",
          "tamano_total_gb": 500.0,
          "tamano_usado_gb": 120.5,
          "id_servidor": 1
        }
        ```
*   **`POST`** `/particiones/register-upsert`
    *   **Body requerido (Array JSON de sincronización automática):**
        ```json
        [
          {
            "punto_montaje": "/",
            "tamano_total_gb": 100.0,
            "tamano_usado_gb": 45.3,
            "id_servidor": 1
          }
        ]
        ```
*   **`POST`** `/credenciales/`
    *   **Body requerido:**
        ```json
        {
          "usuario_ssh": "ansible_user",
          "password_ssh": "ClaveSSH_2026",
          "llave_privada": null,
          "id_tipo_acceso": 1,
          "id_servidor": 1
        }
        ```
*   **`PUT`** `/credenciales/{credencial_id}`
    *   **Body requerido:**
        ```json
        {
          "usuario_ssh": "ansible_user",
          "password_ssh": "NuevaClave_2026",
          "llave_privada": null,
          "id_tipo_acceso": 1,
          "id_servidor": 1,
          "id_estado_credencial": 1
        }
        ```
*   **`POST`** `/dbms/`
    *   **Body requerido:**
        ```json
        {
          "nombre_dbms": "PostgreSQL",
          "version": "16.1"
        }
        ```
*   **`POST`** `/instancias/`
    *   **Body requerido:**
        ```json
        {
          "nombre_instancia": "postgres_prod",
          "puerto": 5432,
          "id_dbms": 1,
          "id_servidor": 1
        }
        ```
*   **`POST`** `/bases-de-datos/`
    *   **Body requerido:**
        ```json
        {
          "nombre_base": "sgir_prod",
          "tamano_mb": 1540.20,
          "id_instancia": 1
        }
        ```
*   **`POST`** `/conexion/test/db/{motor}` *(Motor = mysql5, mysql8, mongodb, oracle)*
    *   **Body requerido:**
        ```json
        {
          "ip": "192.168.1.100",
          "puerto": 3306,
          "usuario": "root",
          "password": "SuperSecurePassword",
          "db_name": "mysql"
        }
        ```
*   **`POST`** `/conexion/test/ssh`
    *   **Body requerido:**
        ```json
        {
          "ip": "192.168.1.100",
          "usuario": "ubuntu",
          "password": "OptionalPassword",
          "key": "OptionalPrivateKeyPlaintext"
        }
        ```
*   **`GET`** `/servidores/` $\rightarrow$ *Sin Body*
*   **`GET`** `/servidores/{servidor_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/servidores/ip/{ip}` $\rightarrow$ *Sin Body*
*   **`GET`** `/servidores/ping/{ip_server}` $\rightarrow$ *Sin Body (Ping ICMP rápido)*
*   **`DELETE`** `/servidores/{servidor_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/particiones/servidor/{servidor_id}` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/particiones/{id_particion}` $\rightarrow$ *Sin Body*
*   **`GET`** `/credenciales/` $\rightarrow$ *Sin Body*
*   **`GET`** `/credenciales/servidor/{servidor_id}` $\rightarrow$ *Sin Body*
*   **`POST`** `/credenciales/test-ssh/{id_servidor}/{id_credencial}` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/credenciales/{credencial_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/dbms/` $\rightarrow$ *Sin Body*
*   **`GET`** `/instancias/servidor/{servidor_id}` $\rightarrow$ *Sin Body*
*   **`POST`** `/instancias/test-db/{id_instancia}/{id_credencial}` $\rightarrow$ *Sin Body*
*   **`GET`** `/bases-de-datos/servidor/{servidor_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/bases-de-datos/search` $\rightarrow$ *Sin Body (Usa query params: q)*
*   **`GET`** `/bases-de-datos/filter` $\rightarrow$ *Sin Body (Usa query params: dbms_id, size_min, size_max)*

---

### 📂 Respaldos (CRUD & Políticas)
*   **`POST`** `/tipo-respaldo/`
    *   **Body requerido:**
        ```json
        {
          "nombre_tipo": "Físico",
          "descripcion": "Respaldo directo de archivos de datos"
        }
        ```
*   **`POST`** `/tipo-almacenamiento/`
    *   **Body requerido:**
        ```json
        {
          "nombre_tipo": "S3 Bucket",
          "descripcion": "Almacenamiento de objetos en la nube"
        }
        ```
*   **`POST`** `/rutas-respaldo/`
    *   **Body requerido:**
        ```json
        {
          "path": "/mnt/backups/pg_prod",
          "id_tipo_almacenamiento": 1,
          "id_servidor": 1
        }
        ```
*   **`PUT`** `/rutas-respaldo/{ruta_id}`
    *   **Body requerido:**
        ```json
        {
          "path": "/mnt/backups/pg_prod_v2",
          "id_tipo_almacenamiento": 1,
          "id_servidor": 1
        }
        ```
*   **`POST`** `/politicas-respaldo/`
    *   **Body requerido:**
        ```json
        {
          "nombre_politica": "Semanal Retención 15d",
          "retencion_dias": 15,
          "frecuencia_horas": 168
        }
        ```
*   **`PUT`** `/politicas-respaldo/{politica_id}`
    *   **Body requerido:**
        ```json
        {
          "nombre_politica": "Semanal Retención 30d",
          "retencion_dias": 30,
          "frecuencia_horas": 168
        }
        ```
*   **`POST`** `/asignacion-politica/`
    *   **Body requerido:**
        ```json
        {
          "id_base_datos": 1,
          "id_politica": 1
        }
        ```
*   **`POST`** `/respaldos/`
    *   **Body requerido:**
        ```json
        {
          "id_base_datos": 1,
          "id_politica": 1,
          "id_credencial": 1,
          "id_ruta_respaldo": 1,
          "id_estado_ejecucion": 4,
          "tamano_mb": 420.50
        }
        ```
*   **`GET`** `/tipo-respaldo/` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/tipo-respaldo/{tipo_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/tipo-almacenamiento/` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/tipo-almacenamiento/{tipo_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/rutas-respaldo/` $\rightarrow$ *Sin Body*
*   **`GET`** `/rutas-respaldo/servidor/{servidor_id}` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/rutas-respaldo/{ruta_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/politicas-respaldo/` $\rightarrow$ *Sin Body*
*   **`GET`** `/politicas-respaldo/{politica_id}/assets` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/politicas-respaldo/{politica_id}` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/asignacion-politica/{id_base_datos}/{id_politica}` $\rightarrow$ *Sin Body*
*   **`GET`** `/respaldos/historial` $\rightarrow$ *Sin Body (Soporta query: id_base_datos)*

---

### 🚨 Catálogos de Monitoreo & Alerting
*   **`POST`** `/alertas/`
    *   **Body requerido:**
        ```json
        {
          "id_servidor": 1,
          "id_tipo_metrica": 1,
          "id_nivel_alerta": 3,
          "valor_lectura": 94.5,
          "detalle_alerta": "El uso del disco superó el umbral crítico del 90%"
        }
        ```
*   **`PUT`** `/alertas/{alerta_id}/resolve` $\rightarrow$ *Sin Body*
*   **`POST`** `/estados/` -> Body: `{"nombre_estado": "string", "descripcion": "string"}`
*   **`POST`** `/metricas/` -> Body: `{"id_monitoreo": 1, "id_tipo_metrica": 1, "valor_lectura": 75.3}`
*   **`POST`** `/monitoreo/` -> Body: `{"id_servidor": 1, "fecha_inicio": "2026-05-19T00:00:00", "id_estado_monitoreo": 3}`
*   **`PUT`** `/monitoreo/{monitoreo_id}/close` -> Body: `{"fecha_fin": "2026-05-19T00:10:00", "id_estado_monitoreo": 4}`
*   **`POST`** `/nivel-alerta/` -> Body: `{"nombre_nivel": "string", "descripcion": "string"}`
*   **`POST`** `/criticidad/` -> Body: `{"nombre_criticidad": "string", "descripcion": "string"}`
*   **`POST`** `/tipo-acceso/` -> Body: `{"nombre_tipo": "string", "descripcion": "string"}`
*   **`POST`** `/tipo-metrica/` -> Body: `{"nombre_tipo": "CPU_USAGE", "descripcion": "Porcentaje de uso de CPU", "umbral_alerta": 90.0}`
*   **`GET`** `/alertas/active` $\rightarrow$ *Sin Body*
*   **`GET`** `/alertas/summary` $\rightarrow$ *Sin Body*
*   **`GET`** `/alertas/today` $\rightarrow$ *Sin Body*
*   **`GET`** `/alertas/recent` $\rightarrow$ *Sin Body*
*   **`GET`** `/alertas/servidor/{servidor_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/estados/` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/estados/{status_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/monitoreo/{monitoreo_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/nivel-alerta/` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/nivel-alerta/{nivel_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/criticidad/` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/criticidad/{nivel_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/tipo-acceso/` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/tipo-acceso/{tipo_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/tipo-metrica/` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/tipo-metrica/{tipo_id}` $\rightarrow$ *Sin Body*

---

### 📋 Auditoría
*   **`POST`** `/audit-types/` -> Body: `{"nombre_evento": "string", "descripcion": "string"}`
*   **`GET`** `/audit-logs/` $\rightarrow$ *Sin Body (Paginación: limit, offset)*
*   **`GET`** `/audit-logs/{bitacora_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/audit-types/` $\rightarrow$ *Sin Body*
*   **`DELETE`** `/audit-types/{tipo_id}` $\rightarrow$ *Sin Body*

---

## 📈 Módulo 1: Observabilidad & Monitoreo Operativo
Endpoints para consulta de salud, estadísticas en tiempo real y ejecución de tareas de monitoreo del Scheduler. El prefijo global de estos endpoints es `/sgir/v1/m1`.

### 🫀 Chequeos de Salud (Health Checks)
*   **`GET`** `/m1/health/postgres` $\rightarrow$ *Sin Body (Retorna estado de conexión interna)*
*   **`POST`** `/m1/health/ping`
    *   **Body requerido:**
        ```json
        {
          "ip": "192.168.1.1"
        }
        ```

### 🖥️ Monitoreo de Host (SSH)
*   **`GET`** `/m1/host/scheduler/status` $\rightarrow$ *Sin Body (Consulta estado del motor APScheduler)*
*   **`POST`** `/m1/host/scheduler/pause` $\rightarrow$ *Sin Body (Pausa la ejecución programada de tareas - Solo Admin)*
*   **`POST`** `/m1/host/scheduler/resume` $\rightarrow$ *Sin Body (Reanuda la ejecución programada - Solo Admin)*
*   **`GET`** `/m1/host/global-summary` $\rightarrow$ *Sin Body (Resumen de servidores sanos vs críticos para dashboard)*
*   **`GET`** `/m1/host/live-cache` $\rightarrow$ *Sin Body (Entrega métricas de tiempo real CPU/RAM desde memoria caché)*
*   **`GET`** `/m1/host/health-status/{server_id}` $\rightarrow$ *Sin Body (Consulta estado de salud del servidor basado en última sesión)*
*   **`POST`** `/m1/host/discover-filesystems/{servidor_id}` $\rightarrow$ *Sin Body (Ejecuta df -h vía SSH en caliente)*  **`[NUEVA UBICACIÓN]`**
*   **`GET`** `/m1/host/{server_id}/{cred_id}` $\rightarrow$ *Sin Body (Dispara monitoreo SSH manual en caliente e inserta en BD)*

### 🛢️ Monitoreo de Bases de Datos (DB Agents)
*   **`GET`** `/m1/db/health-status/{instancia_id}` $\rightarrow$ *Sin Body*
*   **`POST`** `/m1/db/run-adhoc/{instancia_id}/{credencial_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/m1/mongodb/{servidor_id}/{credencial_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/m1/mysql5/{servidor_id}/{credencial_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/m1/mysql8/{servidor_id}/{credencial_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/m1/oracle/{id_instancia}/{id_credencial}` $\rightarrow$ *Sin Body*
*   **`GET`** `/m1/mysql5/metrics/{id_instancia}` $\rightarrow$ *Sin Body*

---

## 🔍 Módulo 2: Auto-Descubrimiento & CMDB
Endpoints enfocados en la extracción automatizada y sincronización del inventario de infraestructura. El prefijo global de estos endpoints es `/sgir/v1/m2`.

*   **`GET`** `/m2/host/discover-cron/{servidor_id}/{credencial_id}` $\rightarrow$ *Sin Body*
*   **`GET`** `/m2/inventory/assets` $\rightarrow$ *Sin Body (Consolidado de toda la CMDB en una sola tabla)*
*   **`POST`** `/m2/inventory/discover-all` $\rightarrow$ *Sin Body (Auto-búsqueda paralela en todas las instancias activas)*
*   **`POST`** `/m2/inventory/discover/{instancia_id}/{credencial_id}` $\rightarrow$ *Sin Body (Auto-búsqueda puntual en una sola BD)*
*   **`GET`** `/m2/inventory/summary/{servidor_id}` $\rightarrow$ *Sin Body (Resumen de bases y almacenamiento en MB)*

---

## 💾 Módulo 3: Automatización de Respaldos (Operativo)
Endpoints para interactuar con la gestión, retención y escaneo remoto de backups. El prefijo global de estos endpoints es `/sgir/v1/m3`.

*   **`POST`** `/m3/host/scheduler/trigger-backup-retention` $\rightarrow$ *Sin Body (Ejecuta manualmente purga nocturna)*
*   **`POST`** `/m3/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}` $\rightarrow$ *Sin Body (Escanea archivos físicos por antigüedad de una sola instancia)*
*   **`POST`** `/m3/inventory/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}` $\rightarrow$ *Sin Body (Escanea archivos de todo el servidor)*
