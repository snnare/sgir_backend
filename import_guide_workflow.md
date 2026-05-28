# Guía de Flujo de Importación - Estado Inicial de CMDB

Esta guía describe el orden secuencial, los endpoints y los cuerpos (tanto para peticiones unitarias `POST` en formato JSON como para cargas masivas `/import-bulk` mediante archivos CSV) requeridos para realizar la inicialización e importación masiva de infraestructura y políticas de respaldo en la base de datos de **SGIR**.

> [!NOTE]
> **Precondiciones asumidas:**
> 1. Los catálogos maestros (`Estado_General`, `Rol_Usuario`, `Nivel_Criticidad`, `Tipo_Acceso`, `DBMS`, `Tipo_Respaldo`, `Tipo_Almacenamiento`) ya se encuentran pre-llenados en la base de datos.
> 2. Ya se encuentra registrado al menos un usuario activo (`Usuario`) para autenticar los tokens de sesión.

---

## 🗺️ Mapa General del Flujo de Importación

El inventario de la plataforma se puede cargar de dos maneras:
1. **Importación Unitaria (JSON):** Realizando llamadas `POST` por cada registro individual respetando las llaves foráneas (`id`).
2. **Carga Masiva (CSV - Recomendado):** Subiendo archivos de hoja de cálculo en el orden numérico establecido para jalar dependencias de forma inteligente sin requerir IDs autogenerados de antemano (utilizando IPs, nombres e identificadores lógicos).

| Paso | Entidad Relacionada | Endpoint Unitario (JSON) | Endpoint Carga Masiva (CSV) | Plantilla CSV de Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| **1** | [Servidores e Instancias](#paso-1-servidores-e-instancias) | `POST /crud/servidores/` | `POST /crud/servidores/import-bulk` | [`01_servidores_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/01_servidores_import.csv) |
| **2** | [Rutas de Respaldo](#paso-2-rutas-de-respaldo) | `POST /crud/rutas-respaldo/` | `POST /crud/rutas-respaldo/import-bulk` | [`02_rutas_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/02_rutas_import.csv) |
| **3** | [Bases de Datos](#paso-3-bases-de-datos) | `POST /crud/bases-de-datos/` | `POST /crud/bases-de-datos/import-bulk` | [`03_bases_de_datos_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/03_bases_de_datos_import.csv) |
| **4** | [Políticas de Respaldo](#paso-4-politicas-de-respaldo) | `POST /crud/politicas-respaldo/` | `POST /crud/politicas-respaldo/import-bulk` | [`04_politicas_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/04_politicas_import.csv) |
| **5** | [Asignación de Políticas](#paso-5-asignacion-de-politicas) | `POST /crud/asignacion-politica/` | `POST /crud/asignacion-politica/import-bulk` | [`05_asignaciones_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/05_asignaciones_import.csv) |

---

## 🛠️ Especificación por Entidad: Carga Masiva (CSV) vs Petición Unitaria (JSON)

### Paso 1: Servidores e Instancias
El importador masivo es extremadamente potente: crea simultáneamente el **Servidor**, sus **Particiones**, la **Instancia DBMS** y las **Credenciales de Acceso**, auto-vinculándolas y encriptando contraseñas en tránsito.

*   **Carga Masiva (CSV):**
    *   **Endpoint:** `POST /sgir/v1/crud/servidores/import-bulk`
    *   **Headers del CSV:** `nombre_servidor,direccion_ip,es_legacy,descripcion,nivel_criticidad,estado,particiones,nombre_dbms,nombre_instancia,puerto_db,usuario,password,tipo_acceso`
    *   **Plantilla de Referencia:** [`plantillas/01_servidores_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/01_servidores_import.csv)

*   **Petición Unitaria (JSON):**
    *   **Endpoint:** `POST /sgir/v1/crud/servidores/`
    *   **Body JSON:**
    ```json
    {
      "nombre_servidor": "db-prod-oracle",
      "direccion_ip": "192.168.1.100",
      "es_legacy": false,
      "descripcion": "Servidor principal para la base de datos Oracle 19c",
      "monitoreo_host": true,
      "monitoreo_db": true,
      "id_nivel_criticidad": 4,      // ID catálogo criticidad (ej: 4 = Crítico)
      "id_estado_servidor": 1       // ID catálogo estado (ej: 1 = Activo)
    }
    ```

---

### Paso 2: Rutas de Respaldo
Directorio físico donde se depositarán o leerán los backups del servidor.

*   **Carga Masiva (CSV):**
    *   **Endpoint:** `POST /sgir/v1/crud/rutas-respaldo/import-bulk`
    *   **Headers del CSV:** `direccion_ip,descripcion_ruta,path,tipo_almacenamiento,estado`
    *   **Plantilla de Referencia:** [`plantillas/02_rutas_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/02_rutas_import.csv)

*   **Petición Unitaria (JSON):**
    *   **Endpoint:** `POST /sgir/v1/crud/rutas-respaldo/`
    *   **Body JSON:**
    ```json
    {
      "descripcion_ruta": "Almacenamiento Local de Backups",
      "path": "/u01/app/oracle/backups",
      "id_servidor": 1,              // ID devuelto al crear el servidor
      "id_tipo_almacenamiento": 1,   // ID catálogo tipo_almacenamiento (ej: 1 = Local)
      "id_estado_ruta": 1            // ID catálogo estado (ej: 1 = Activo)
    }
    ```

---

### Paso 3: Bases de Datos
Bases de datos lógicas o esquemas contenidos en cada Instancia DBMS.

*   **Carga Masiva (CSV):**
    *   **Endpoint:** `POST /sgir/v1/crud/bases-de-datos/import-bulk`
    *   **Headers del CSV:** `direccion_ip,puerto_db,nombre_instancia,nombre_base,tamano_mb,estado`
    *   **Plantilla de Referencia:** [`plantillas/03_bases_de_datos_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/03_bases_de_datos_import.csv)

*   **Petición Unitaria (JSON):**
    *   **Endpoint:** `POST /sgir/v1/crud/bases-de-datos/`
    *   **Body JSON:**
    ```json
    {
      "nombre_base": "ERP_PROD",
      "tamano_mb": 50480.50,
      "id_instancia": 1,             // ID devuelto al crear la instancia
      "id_estado_bd": 1              // ID catálogo estado (ej: 1 = Activo)
    }
    ```

---

### Paso 4: Políticas de Respaldo
Reglas de retención y planificación horaria de copias de seguridad.

*   **Carga Masiva (CSV):**
    *   **Endpoint:** `POST /sgir/v1/crud/politicas-respaldo/import-bulk`
    *   **Headers del CSV:** `nombre_politica,descripcion,expression_cron,hora_ejecuccion,dias_semana,frecuencia_horas,retencion_dias,script_path,tipo_respaldo,estado`
    *   **Plantilla de Referencia:** [`plantillas/04_politicas_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/04_politicas_import.csv)

*   **Petición Unitaria (JSON):**
    *   **Endpoint:** `POST /sgir/v1/crud/politicas-respaldo/`
    *   **Body JSON:**
    ```json
    {
      "nombre_politica": "Política Oracle Diaria",
      "descripcion": "Respaldo nocturno diario con retención de 30 días",
      "expression_cron": "0 1 * * *", // Opcional
      "hora_ejecuccion": "01:00:00", // Opcional
      "dias_semana": "Lunes-Domingo", // Opcional
      "frecuencia_horas": 24,
      "retencion_dias": 30,
      "script_path": "/u01/app/oracle/scripts/backup.sh", // Opcional
      "id_tipo_respaldo": 1,        // ID catálogo tipo_respaldo (ej: 1 = Completo)
      "id_estado_politica": 1       // ID catálogo estado (ej: 1 = Activo)
    }
    ```

---

### Paso 5: Asignación de Políticas
Vincula relacionalmente una Base de Datos con una Política específica.

*   **Carga Masiva (CSV):**
    *   **Endpoint:** `POST /sgir/v1/crud/asignacion-politica/import-bulk`
    *   **Headers del CSV:** `direccion_ip,puerto_db,nombre_instancia,nombre_base,nombre_politica`
    *   **Plantilla de Referencia:** [`plantillas/05_asignaciones_import.csv`](file:///home/angel/src/titulacion/sgir_backend/plantillas/05_asignaciones_import.csv)

*   **Petición Unitaria (JSON):**
    *   **Endpoint:** `POST /sgir/v1/crud/asignacion-politica/`
    *   **Body JSON:**
    ```json
    {
      "id_base_datos": 1,            // ID devuelto al crear la BD
      "id_politica": 1               // ID devuelto al crear la Política
    }
    ```
