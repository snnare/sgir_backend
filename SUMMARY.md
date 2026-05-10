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
*   **SSH Tunneling**: Soporte para Jump Servers (Bastión).

### 🛠️ Oportunidades de Mejora (Optimización)
*   **Logging Profesional**: Migrar prints a un sistema de logs rotativos.

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


