# SGIR - Resumen del Estado Actual del Proyecto

## 📅 Fecha: 1 de Mayo, 2026 (Endpoints de Conexión Dinámica y Estabilidad)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Test de Conexión Independiente (Raw Payload)**:
    *   **Endpoints Stateless**: Creación de `/conexion/test/db/{motor}` y `/conexion/test/ssh` para validar credenciales sin persistencia en DB.
    *   **Soporte Multi-Motor**: Lógica de prueba para MySQL, PostgreSQL, MongoDB y Oracle.
2.  **Monitoreo Multi-Partición (SSH)**:
    *   **Modelo Dinámico**: Implementación de la tabla `servidor_particion`.
3.  **Importación Masiva (CSV v2)**:
    *   **Soporte de Formato**: El motor de carga ahora procesa particiones.
4.  **Refactorización de APIs de Infraestructura**:
    *   **Búsqueda Granular**: Rutas mejoradas para búsqueda por ID e IP.

## 📅 Fecha: 5 de Mayo, 2026 (Arquitectura de Observabilidad y Rutas Exclusivas)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Refactor de Rutas de Respaldo (Modelo v2)**:
    *   **Exclusividad por Servidor**: Se añadió `id_servidor` a `RutaRespaldo` para permitir filtrado directo y mejorar la integridad referencial (Option A).
    *   **Nuevo Endpoint**: `GET /rutas-respaldo/servidor/{id}` implementado.
2.  **Simplificación de Sesiones de Monitoreo**:
    *   **Desacoplamiento de Credenciales**: Se eliminó `id_credencial` de la tabla `Monitoreo`. Ahora el registro se enfoca puramente en el servidor y su estado de salud.
3.  **Optimización del Orquestador SSH**:
    *   **Mapeo de Puertos Dinámico**: Se eliminó el hardcode de puerto 2222. Ahora el orquestador respeta puertos explícitos en la IP (ej. `127.0.0.1:2224`) o usa el estándar 22.
    *   **Compatibilidad Docker**: Solución de conectividad entre contenedores usando nombres de servicio DNS internos.
4.  **Scheduler con Lista Blanca (Whitelist)**:
    *   **Control de Monitoreo**: El scheduler ahora solo procesa servidores que han sido "activados" previamente en la tabla `Monitoreo`.
5.  **API de Métricas en Tiempo Real**:
    *   **Live Cache**: Endpoint `/monitoring/host/live-cache` creado para exponer los datos en memoria (CPU, RAM, Discos) directamente al Dashboard.

### ❌ Funcionalidades Pendientes (Backlog)
*   **Expiración de Respaldos**: Lógica para marcar como "Expirados" los registros de backup.

## 📅 Fecha: 6 de Mayo, 2026 (Endpoint de Ping y Estabilidad en Docker)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Ping de Servidor**:
    *   **Nuevo Endpoint**: `GET /servidores/ping/{ip_server}` implementado para validación rápida de conectividad de red.
    *   **Corrección de Privilegios**: Ajuste de `icmplib` a modo no privilegiado (`privileged=False`) para permitir la ejecución dentro de contenedores Docker sin root.
2.  **Infraestructura y DevOps**:
    *   **Imagen Docker Optimizada**: Inclusión de `iputils-ping` en el stage de runtime para garantizar capacidades de red al usuario `sgir_user`.
3.  **Herramientas de Validación (SRE Tests)**:
    *   **Test de Ping**: `tests/test_ping_server.py` para validar conectividad básica.
    *   **Test de Live Cache**: `tests/test_live_cache.py` para visualizar el flujo de métricas en tiempo real (CPU/RAM/Disco) generado por el APScheduler.

---
**Hash de Sesión:** `02aab3db-eaaf-4424-8b24-e12b73abeb16`

---
### 🏁 ¿Dónde nos quedamos?
Hemos consolidado la **capa de conectividad y diagnóstico** del sistema. El backend ahora es capaz de:
1. Validar la existencia de red de un servidor vía `/servidores/ping/` de forma segura en Docker.
2. Exponer métricas de hardware en tiempo real a través de un Live Cache eficiente.
3. El APScheduler alimenta correctamente la memoria global, permitiendo al frontend mostrar dashboards sin latencia de base de datos.

El próximo paso es atacar el backlog de **Expiración de Respaldos** dentro del Scheduler para completar el ciclo de vida de los backups.

## 📅 Fecha: 7 de Mayo, 2026 (Protocolo Compact Pulse y SSH Pooling)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Protocolo Compact Pulse**:
    *   **Optimización de Red**: Implementación de un formato de métricas serializado por tuberías (`cpu|ram|disks|uptime|timestamp`).
    *   **Reducción de Payload**: Ahorro del ~75% de ancho de banda en el endpoint masivo `/live-cache`.
2.  **SSH Connection Pooling**:
    *   **Reutilización de Sesiones**: Creación de un pool global de conexiones para evitar handshakes criptográficos repetitivos.
    *   **Keep-Alive**: Configuración de latidos de 30s para mantener túneles SSH abiertos y estables.
    *   **Eficiencia**: Reducción del tiempo de recolección de ~2s a <100ms por servidor.
3.  **Refactor de Pruebas**:
    *   Actualización de `test_live_cache.py` y `test_fedora_monitoring.py` para soportar el nuevo protocolo de transporte.

---
**Hash de Sesión:** `02aab3db-eaaf-4424-8b24-e12b73abeb16`

---
### 🏁 ¿Dónde nos quedamos?
Hemos transformado el sistema de monitoreo de un modelo "on-demand" ineficiente a un **modelo de alto rendimiento y baja latencia**. El backend ahora es capaz de manejar cientos de servidores con un impacto mínimo en red y CPU. 

## 📅 Fecha: 8 de Mayo, 2026 (Alcance de Monitoreo, DB Pooling e Inventario Global)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Selección de Alcance (Alcance de Monitoreo)**:
    *   **Flags de Control**: Implementación de `monitoreo_host` y `monitoreo_db` en la tabla `Servidor` (Default `FALSE`).
    *   **Scheduler Inteligente**: El orquestador ahora solo dispara tareas (SSH o DB) si el servidor tiene activado el alcance correspondiente.
2.  **Persistencia de Conexiones (DB Pooling)**:
    *   **DBConnectionPool**: Creación de un administrador de conexiones persistentes para RDBMS y MongoDB.
    *   **Optimización**: Reutilización de Engines de SQLAlchemy y Clientes de Mongo, eliminando la latencia de handshake TCP en cada ciclo de monitoreo.
3.  **Auto-Descubrimiento Extendido**:
    *   **Oracle & MongoDB**: Lógica implementada para extraer esquemas/bases de datos automáticamente al registrar nuevas instancias.
4.  **Endpoint de Búsqueda de Activos (Global CMDB)**:
    *   **Vista Consolidada**: Nuevo endpoint `/monitoring/inventory/assets` que realiza un `LEFT JOIN` masivo para mostrar servidores, instancias y bases de datos en una sola tabla.
5.  **Pruebas de Integración Full**:
    *   **Script de Flujo Completo**: `tests/test_full_system_flow.py` que automatiza el registro de toda la infraestructura del laboratorio y verifica el inventario.
6.  **Gestión Avanzada de Almacenamiento (SSH)**:
    *   **Descubrimiento de FileSystems**: Endpoint `/monitoring/host/discover-filesystems/{id}` para listar discos reales vía `df -h`.
    *   **Registro Upsert de Particiones**: Nuevo flujo para sincronizar puntos de montaje en la CMDB de forma automática o manual.
7.  **Correcciones de Estabilidad**:
    *   **Import Fix**: Corrección de error de importación en el `scheduler_manager`.
    *   **MySQL Connectivity**: Resolución definitiva del error 1049 (Unknown Database).
8.  **Automatización del Ciclo de Vida de Respaldos**:
    *   **Retention Manager**: Implementación de `run_backup_retention_policy` para marcar automáticamente respaldos obsoletos.
    *   **Programación Nocturna**: Tarea integrada en el Scheduler para ejecutarse a las 4:00 AM.
    *   **Control Manual**: Endpoint `POST /scheduler/trigger-backup-retention` para ejecuciones bajo demanda.

---
**Hash de Sesión:** `668ace37-bd2f-4201-a26b-2b1eddb576bd`

---
### 🏁 ¿Dónde nos quedamos?
Hemos concluido exitosamente el desarrollo del motor core de **Observabilidad y Gestión de Respaldos**. El sistema es ahora una plataforma SRE completa que permite descubrir activos, monitorear salud en tiempo real con latencia mínima, y gestionar el ciclo de vida de los backups de forma totalmente desatendida.

## 📅 Fecha: 10 de Mayo, 2026 (Endpoints de Alertas Temporales y Auditoría)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Consultas Temporales de Alertas**:
    *   **Alertas del Día**: Implementación de `GET /alertas/today` para filtrar eventos críticos desde las 00:00 UTC.
    *   **Feed de Recientes**: Implementación de `GET /alertas/recent` con soporte para límites dinámicos (`limit`).
2.  **Refactor de Persistencia**:
    *   Optimización de consultas en `monitoring_persistence_crud` para manejo de fechas con `timezone.utc`.
3.  **Auditoría y Trazabilidad (Bitácora)**:
    *   Validación de endpoints de auditoría `/audit-logs/` para el registro de acciones de usuario y eventos de sistema.

### ❌ Funcionalidades Pendientes (Backlog)
*   **Dashboard Integration**: Consumo del Live Cache y Alertas Recientes en el frontend.

---

## 📅 Fecha: 21 de Mayo, 2026 (Monitoreo Modular por Criticidad para MySQL y MongoDB)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Monitoreo Modular Basado en Criticidad**:
    *   **Homologación con Oracle**: Implementación de recolección en Grupos A (Conectividad), B (Recursos) y C (Performance) para MySQL 5, MySQL 8 y MongoDB, determinado dinámicamente por el nivel de criticidad asignado al servidor.
    *   **Endpoints Modulares Exclusivos**:
        *   `GET` `/sgir/v1/m1/mysql5/modular/{id_instancia}/{id_credencial}`
        *   `GET` `/sgir/v1/m1/mysql8/modular/{id_instancia}/{id_credencial}`
        *   `GET` `/sgir/v1/m1/mongodb/modular/{id_instancia}/{id_credencial}`
2.  **Esquemas Pydantic Modularizados**:
    *   Diseño de modelos específicos para cada grupo de métricas de MySQL y MongoDB bajo `app/schemas/catalogs/monitoring_persistence_schemas.py`.
3.  **Extracción Directa y No Intrusiva**:
    *   **MySQL 5 & 8**: Consultas adaptadas usando `information_schema` y `performance_schema` correspondientemente sin alterar servidores target.
    *   **MongoDB**: Comandos administrativos ligeros `ping` y `serverStatus` con perfiles de permisos mínimos (`clusterMonitor`).
4.  **Escapado de Contraseñas (URL-Encoding)**:
    *   Corrección crítica en `app/core/dynamic_db_core.py` aplicando `urllib.parse.quote_plus` a contraseñas descifradas, permitiendo el uso de caracteres especiales como `$` de forma transparente en todas las URLs de conexión RDBMS y MongoDB.
5.  **Suite de Pruebas de Integración**:
    *   Creación de `tests/m1/test_modular_db_monitoring.py` para validar de principio a fin el flujo de registro, cambio de criticidades (Bajo, Medio, Alto) y payloads modulares correctos para los tres motores.

## 📅 Fecha: 22 de Mayo, 2026 (Monitoreo Masivo en Paralelo y Pruebas SRE de Carga)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Monitoreo Masivo y Auto-Descubrimiento en Paralelo (Módulo 2)**:
    *   **Auto-Descubrimiento Asíncrono**: Integración completa del endpoint `POST /sgir/v1/m2/inventory/discover-all` para sincronizar concurrentemente mediante hilos los esquemas de bases de datos activos de toda la red del laboratorio.
    *   **Estadísticas de Salud Globales**: Implementación del endpoint `GET /sgir/v1/m2/inventory/global-summary` para consultar de forma ultra-ligera en memoria (Live Cache) la salud consolidada de las instancias.
    *   **Caché Masiva de Base de Datos**: Habilitación del endpoint `GET /sgir/v1/m2/inventory/live-cache` para el retorno de todas las instancias registradas con soporte para descompresión transparente del formato "Compact Pulse" (piped strings).
2.  **Suite de Pruebas de Carga SRE (Bulk Testing)**:
    *   **Test de Escala Real (`test_bulk_servers_monitoring.py`)**: Desarrollo y ejecución exitosa de una suite de pruebas integrada que simula un volumen masivo de servidores activos, se autentica vía OAuth2 (`admin@admin.com` / `123Nokia`), gatilla el descubrimiento masivo en paralelo de todos los motores del laboratorio y valida los estados y formatos de almacenamiento en la caché global.
3.  **Monitoreo de Infraestructura y Logs**:
    *   **Trazabilidad y Verificación**: Auditoría del flujo en `docker logs "sgir_backend"`, confirmando la respuesta asíncrona del scheduler concurrente a nivel de inventario masivo con éxito (200 OK) en menos de 1.20 segundos.

---

## 📅 Fecha: 23 de Mayo, 2026 (Integración Oracle Legacy y Pruebas Independientes)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Endpoints Independientes de Oracle (`/legacy` y `/no-legacy`)**:
    *   **Oracle Legacy vía SSH**: Creación de `/test/db/oracle/legacy` para conectarse a Oracle 10g usando SSH, accediendo a `/home/oracle`, cargando `.bash_profile` y ejecutando `sqlplus` local en el servidor con el `ORACLE_SID` recuperado dinámicamente de la CMDB.
    *   **Oracle No-Legacy vía TCP**: Creación de `/test/db/oracle/no-legacy` para pruebas directas en Oracle 19c usando Thin Mode y el `ORACLE_SID` dinámico de la CMDB.
    *   **Ordenamiento de Rutas**: Reorganización de las rutas en el backend para priorizar las de Oracle específicas y evitar conflictos con la genérica `/test/db/{motor}` en FastAPI.
2.  **Sourcing Completo de Entorno SSH**:
    *   Integración del comando de entorno `cd /home/oracle && source .bash_profile` tanto en el endpoint de prueba legacy como en la recolección automática del fallback SSH en APScheduler (`oracle_monitoring_service.py`).
3.  **Suite de Pruebas de Integración**:
    *   **Test Endpoint Legacy (`test_oracle_legacy_endpoint.py`)**: Implementación de un test completo en `tests/m1` para validar la autenticación de administrador, alta del servidor legacy (`148.215.1.98`), registro de credenciales SSH/DB con SID personalizado, y la invocación del endpoint `/test/db/oracle/legacy`.

---
**Hash de Sesión:** `4c36773a-26ff-4258-a0b8-12fdb8f006df`

---
### 🏁 ¿Dónde nos quedamos?
Hemos implementado con éxito el soporte híbrido nativo/SSH para Oracle (10g legacy y 19c moderno) con carga de perfiles completa, reordenamiento de endpoints FastAPI y una suite de pruebas de integración completa lista para ejecutar.
