# Resumen de Estado del Proyecto - SGIR (Actualizado: 3 de Junio, 2026)

Este documento registra los avances, decisiones técnicas, lógica de negocio incorporada y estado de los repositorios durante las sesiones de desarrollo para garantizar la continuidad del sistema **SGIR**.

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
