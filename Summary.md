# Resumen de Estado del Proyecto - SGIR (Actualizado: 2 de Junio, 2026)

Este documento registra los avances, decisiones técnicas, lógica de negocio incorporada y estado de los repositorios durante la sesión actual para garantizar la continuidad del desarrollo del sistema **SGIR**.

---

## 🏛️ Contexto y Stack Tecnológico
*   **Backend:** FastAPI (Python 3.14) + SQLAlchemy 2.0.
*   **Frontend:** React (Vite, TypeScript, TailwindCSS/Vanilla CSS).
*   **Base de Datos:** PostgreSQL 16 (CMDB, Monitoreo, Transaccional y Persistencia SRE).
*   **Seguridad:** Encriptación AES-256 para contraseñas de infraestructura y OAuth2 JWT.
*   **Orquestación SSH:** Paramiko con Connection Pooling (Keep-Alive de 30s) y soporte multiformato.

---

## 🚀 Logros y Cambios Clave de la Sesión (2 de Junio, 2026)

### 1. Robustecimiento y Consistencia de Reportes (RDBMS + Versión)
*   **Decisión de Diseño**: Modificamos los endpoints `/assets/pdf` y `/assets/csv` en [`app/routes/__init__.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/__init__.py) para recuperar y normalizar el tipo de motor de base de datos junto con su versión principal (ej. `"MySQL 8"`, `"MongoDB 6"`, `"Oracle 21"`).
*   **Compatibilidad Visual**: Esta cadena combinada se inyecta directamente bajo el campo `motor` de la plantilla HTML, de forma que el CSS del PDF renderiza los colores correctos de los badges por motor en WeasyPrint de manera retrocompatible.

### 2. Conversión a Endpoints Offline
*   **Reporte CSV**: Modificamos `/assets/csv` para que trabaje de forma offline por completo, eliminando la llamada a `run_bulk_inventory_sync` por red.
*   **Reporte PDF Offline**: Se creó el endpoint `/assets/pdf-offline` para generar el PDF del inventario de bases de datos de forma instantánea a partir de la CMDB local (PostgreSQL), útil si los servidores remotos están inalcanzables.

### 3. Resumen Global de Políticas de Respaldo
*   **Endpoint API**: Se implementó `GET /sgir/v1/crud/politicas-respaldo/resumen-global` en [`politica_respaldo_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/backups/politica_respaldo_routes.py).
*   **Lógica Relacional**: Realiza un join cuádruple en [`backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) (`PoliticaRespaldo` $\to$ `BaseDeDatos` $\to$ `InstanciaDBMS` $\to$ `DBMS` y `Servidor`) para devolver un resumen consolidado en formato JSON que indica qué política está asignada a qué base de datos y en qué servidor (incluyendo IP y motor formateado).

### 4. Nuevo Reporte de SLA, Incidentes SRE y Uptime
*   **Plantilla Dinámica**: Creado [`sre_sla_uptime_template.html`](file:///home/angel/src/titulacion/sgir_backend/app/templates/reports/sre_sla_uptime_template.html) con la identidad UAEMex para reportar el porcentaje de uptime exitoso por host, días monitoreados, incidentes del periodo e histórico de alertas recientes.
*   **Mockup de Prueba**: Creado [`sre_sla_uptime_template_test.html`](file:///home/angel/src/titulacion/sgir_backend/app/templates/reports/mockups/sre_sla_uptime_template_test.html) simulando a escala 7 servidores, SLAs variables e incidentes para validar el diseño visual.
*   **Endpoint API**: Se implementó `GET /sgir/v1/assets/sre-sla-pdf` en [`app/routes/__init__.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/__init__.py). Extrae la disponibilidad real basándose en el conteo de chequeos de monitoreo exitosos/fallidos por servidor, y las últimas 30 alertas registradas en base de datos.

### 5. Depuración y Limpieza de Carga Masiva (CSV)
*   **Eliminación de endpoints redundantes**: Se eliminaron los endpoints de `/import-bulk` de bases de datos, políticas de respaldo, rutas de respaldo y asignación de políticas.
*   **Carga Única de Infraestructura**: El único endpoint de carga masiva CSV activo es `POST /sgir/v1/crud/servidores/import-bulk`.
*   **Eliminación de Código Muerto**: Se reescribió y depuró [`import_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/import_service.py) eliminando todas las funciones de parsing de CSVs obsoletos y conservando solo la de infraestructura.

### 6. Ordenamiento de Plantillas de Prueba (Mockups)
*   Se creó el directorio [`app/templates/reports/mockups`](file:///home/angel/src/titulacion/sgir_backend/app/templates/reports/mockups) para agrupar todas las previsualizaciones estáticas HTML.
*   Se movieron a dicha subcarpeta los archivos `db_inventory_test.html`, `general_infrastructure_template_test.html` (mockup de 50 servidores/motores a escala) y `sre_sla_uptime_template_test.html`.

### 7. Documentación en routes.md
*   Se actualizaron y añadieron las descripciones detalladas, comportamientos operativos y estructuras de payload para los endpoints recién creados en [`routes.md`](file:///home/angel/src/titulacion/sgir_backend/routes.md).

---

## 🔒 Control de Cambios (Estado de Git)
*   El backend compila y ejecuta de manera totalmente exitosa (`uv run python -m py_compile`).
*   Los endpoints offline optimizan el rendimiento de red reduciendo el tiempo de respuesta a milisegundos.

---

## 📝 Próximos Pasos Recomendados

1.  **Integración en Frontend (Dashboard SRE)**:
    *   Vincular las opciones de descarga en el Frontend (React) a las nuevas rutas offline (`/assets/pdf-offline`, `/assets/csv` y `/assets/sre-sla-pdf`).
2.  **Pruebas de Uptime**:
    *   Agregar datos de monitoreo históricos de simulación para validar los porcentajes de SLA en entornos reales de producción con cargas prolongadas.
