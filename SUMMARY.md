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

## 📅 Fecha: 6 de Mayo, 2026 (Endpoint de Ping de Infraestructura)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Ping de Servidor**:
    *   **Nuevo Endpoint**: `GET /servidores/ping/{ip_server}` implementado para validación rápida de conectividad de red.
    *   **Integración icmplib**: Reutilización de la lógica de ping estándar del sistema.

---
**Hash de Sesión:** `02aab3db-eaaf-4424-8b24-e12b73abeb16`

---
### 🏁 ¿Dónde nos quedamos?
Hemos logrado la **observabilidad completa y en tiempo real** de un servidor Fedora corriendo en Docker. El sistema es capaz de:
1. Onboardear el servidor con criticidad Crítica.
2. Realizar ping de conectividad básica vía `/servidores/ping/`.
3. Establecer conexión SSH dinámica (puerto 22).
4. Capturar métricas y exponerlas vía Live Cache.
5. Filtrar el monitoreo automático basándose en una lista blanca.

El próximo paso es atacar el backlog de **Expiración de Respaldos** dentro del Scheduler.
