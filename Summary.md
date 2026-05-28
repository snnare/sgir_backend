# Resumen de Estado del Proyecto - SGIR

Este documento sirve como un registro exhaustivo de todos los cambios de arquitectura, endpoints desarrollados, guías de formato redactadas, decisiones de diseño tomadas y el listado de mejoras pendientes para retomar el desarrollo del sistema **SGIR** en cualquier sesión futura.

---

## 🏛️ Contexto y Stack del Proyecto

**SGIR** (*Sistema de Gestión de Infraestructura y Respaldos*) es una plataforma de backend para observabilidad SRE y automatización de respaldos desarrollada con:
*   **FastAPI (Python 3.14)** + **SQLAlchemy 2.0**
*   **PostgreSQL 16** (Base de datos relacional transaccional y CMDB)
*   **Paramiko** (SSH Connection Pooling con keep-alive de 30s)
*   **oracledb, pymysql, pymongo** (Drivers para monitoreo y pruebas dinámicas de motores)
*   **APScheduler** (Orquestador de tareas en segundo plano y purga automatizada)

---

## 🚀 Logros y Cambios Implementados (Historial de Sesiones)

### 1. Pruebas de Conexión Dinámicas a Bases de Datos (Oracle)
*   **Desacoplamiento Legacy / Estándar:** Dividimos formalmente las pruebas de conexión de Oracle en dos endpoints diferenciados:
    *   `/test/db/oracle/legacy`: Conexión mediante SSH al host destino, cargando las variables de entorno de `.bash_profile` y ejecutando localmente `sqlplus`.
    *   `/test/db/oracle/no-legacy`: Conexión estándar TCP Thin Mode de alta velocidad.
*   **Integración de `oracle_sid` en Request Payload:**
    *   Modificamos el esquema global `ConnectionTestRequest` en `infrastructure_schemas.py` para admitir de forma opcional el campo `oracle_sid`.
    *   Actualizamos la lógica de ambos endpoints en `conexion_routes.py` para priorizar el `oracle_sid` enviado directamente en el JSON body.
    *   **Resultado:** El endpoint `no-legacy` ahora se comporta de manera **100% independiente** (no toca ninguna tabla de base de datos para validar credenciales si se le provee el SID). El endpoint `legacy` sigue haciendo lookup en la CMDB pero únicamente para extraer las credenciales SSH correspondientes del host.

### 2. Suite Completa de Carga Masiva (CSV Imports)
Originalmente, solo existía la importación asíncrona de servidores. Implementamos toda la lógica y endpoints faltantes para lograr una inicialización masiva en lotes de toda la jerarquía relacional del sistema:
*   **Endpoints `/import-bulk` Creados:**
    *   `POST /sgir/v1/crud/servidores/import-bulk` (Servidores, particiones, credenciales e instancias en un solo CSV).
    *   `POST /sgir/v1/crud/rutas-respaldo/import-bulk` (Asociación de directorios a hosts mediante IPs).
    *   `POST /sgir/v1/crud/bases-de-datos/import-bulk` (Registro masivo de esquemas/DBs en base a su IP, puerto e instancia).
    *   `POST /sgir/v1/crud/politicas-respaldo/import-bulk` (Configuración masiva de políticas, crontabs y retenciones).
    *   `POST /sgir/v1/crud/asignacion-politica/import-bulk` (Tabla intermedia relacional N:M).
*   **Manejo Inteligente de Duplicidad:** Todo el importador procesa los registros fila por fila evaluando claves de unicidad lógica. Si se ingresan múltiples credenciales para una sola IP, el sistema **reutiliza el mismo servidor** evitando colisiones en la base de datos.

### 3. Plantillas de Producción (Directorio `plantillas/`)
Creamos el directorio [`plantillas/`](file:///home/angel/src/titulacion/sgir_backend/plantillas/) en la raíz del proyecto, el cual contiene 5 archivos CSV de ejemplo estructurados con datos ficticios pero coherentes entre sí para inicializar el sistema de forma masiva en el orden numérico correcto (`01_servidores_import.csv` a `05_asignaciones_import.csv`).

### 4. Guías de Formato Oficiales (Directorio `plantilla/`)
Dentro de la carpeta original [`plantilla/`](file:///home/angel/src/titulacion/sgir_backend/plantilla/) del proyecto, creamos 6 documentos en formato Markdown:
*   `guia_rapida_importacion.md`: Muestra el diagrama de flujo topological (Mermaid) y el orden de los 5 pasos a seguir con sus endpoints y checklists.
*   `guia_formato_servidores.md`, `guia_formato_rutas.md`, `guia_formato_bases_de_datos.md`, `guia_formato_politicas.md`, `guia_formato_asignaciones.md`: Guías exhaustivas columna por columna detallando tipos de datos, opcionalidad, encriptación AES-256 automática y lógica de duplicación.

### 5. Nuevo Endpoint `GET` Detallado para Rutas de Respaldo
Implementamos un nuevo endpoint enriquecido que facilita el consumo directo de datos para el frontend:
*   **Endpoint:** `GET /sgir/v1/crud/rutas-respaldo/details`
*   **Comportamiento:** Realiza un join directo en base de datos (`RutaRespaldo`, `Servidor`, `UserStatus`) y retorna los registros limpios exponiendo el nombre literal del estado y la IP del servidor en lugar de sus IDs numéricos internos.
*   **Body de Respuesta:** `List[RutaRespaldoEnriquecidaResponse]` (`ip`, `path`, `descripcion`, `estado`).

---

## 🛠️ Mejoras Pendientes / Próximos Pasos

Para continuar expandiendo el sistema de observabilidad y respaldos, se proponen las siguientes mejoras:

### 1. Interfaz de Usuario (Frontend / Dashboard)
*   **Componente Drag-and-Drop:** Crear un componente visual en React/Vue para arrastrar las plantillas CSV y subirlas progresivamente, mostrando el resumen JSON de filas procesadas y errores reportados por el backend en tiempo real.
*   **Filtros de Trazabilidad:** Integrar en la UI de "Rutas de Respaldo" la visualización enriquecida obtenida mediante el nuevo endpoint `GET /details`.

### 2. Robustez y Validación en Importadores
*   **Pre-validación Pydantic en CSV:** En lugar de lanzar errores directo de SQLAlchemy, procesar temporalmente cada fila del CSV instanciando sus modelos Pydantic base (ej. `ServidorCreate`) para reportar de forma amigable formatos incorrectos de IPs o puertos antes de tocar la base de datos.
*   **Paralelización de Carga:** Si la CMDB crece a miles de servidores, evaluar el uso de `asyncio.gather` dentro de `import_service.py` para procesar bloques de registros concurrentemente.

### 3. Orquestación SRE & Respaldos
*   **Scheduler Automatizado de Descubrimientos:** Conectar el servicio `run_integrated_file_discovery` (descubridor SSH) al scheduler base para que escanee de forma recurrente las `RutaRespaldo` de los servidores y registre automáticamente en la tabla `Respaldo` cualquier dump físico recién creado en red.
*   **Notificaciones de Fallo:** Implementar un servicio de alerta (ej. correo, Slack o endpoint en RAM) que notifique inmediatamente cuando el *Retention Manager* nocturno (4:00 AM) falle al purgar un backup obsoleto.

### 4. Auditoría y Seguridad
*   **Filtros en Auditoría:** Extender `GET /sgir/v1/crud/audit-logs/` para permitir paginación, ordenamiento y filtrado por rango de fechas o usuario ejecutor.
*   **Masking de Credenciales:** Asegurar que los endpoints unitarios de `GET` sobre credenciales enmascaren o no expongan el `password_hash` descifrado accidentalmente.
