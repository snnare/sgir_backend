# SGIR - Resumen del Estado Actual del Proyecto

## 📅 Fecha: 28 de Abril, 2026 (Plataforma de Observabilidad Unificada Validada)

### ✅ Módulos Implementados (Hitos Críticos)
1.  **Monitoreo Unificado de Bases de Datos**:
    *   **Motor Dual**: Implementado `db_unified_service.py` que soporta Oracle, MySQL y MongoDB bajo una misma estructura de métricas (Ping, Capacidad, Procesos).
    *   **Lógica de Criticidad**: El nivel de detalle de las métricas de DB se adapta automáticamente al nivel del servidor (Bajo -> Crítico).
2.  **Scheduler de Alta Disponibilidad**:
    *   **Ejecución Paralela**: Configurado con un Pool de **80 workers** para procesar múltiples servidores simultáneamente (Host + DB) aprovechando los 4-6 CPUs.
    *   **Live Cache en RAM**: Capa de memoria volátil para alimentar las tarjetas del Frontend en milisegundos sin latencia de base de datos.
    *   **Optimización de Almacenamiento**: Implementado **Monitoreo Silencioso**; la base de datos solo guarda métricas cuando superan el umbral del **90%**.
3.  **Gestión de Alertas y Notificaciones**:
    *   **Centro de Notificaciones**: Nuevos endpoints para listar alertas activas, ver resúmenes por nivel y "Resolver/Cerrar" incidentes desde la interfaz.
4.  **Soporte Legacy e Importación**:
    *   Validación exitosa de monitoreo en **RHEL 4** (Host de 20+ años).
    *   Importación masiva vía CSV operativa con normalización de catálogos y cifrado AES-256.

### ❌ Funcionalidades Pendientes (Backlog)
*   **Retention Manager (Urgente)**: Implementar tarea automática para purgar métricas y sesiones de monitoreo de más de 30 días de antigüedad.
*   **Expiración de Respaldos**: Lógica para marcar como "Expirados" los registros de backup que superen los días de retención de su política.
*   **Roles y Permisos**: Aplicar seguridad a nivel de endpoint para restringir acciones administrativas (Delete/Bulk Import) solo a usuarios Admin.
*   **SSH Tunneling**: Añadir soporte para Jump Servers (Bastión) en el orquestador para alcanzar redes aisladas.

### 🛠️ Oportunidades de Mejora (Optimización)
*   **Endpoint de Salud Global**: Crear un resumen consolidado para el Dashboard (ej: "45 Verdes, 2 Rojos") en una sola petición.
*   **Filtros de Búsqueda Avanzados**: Implementar filtrado por fecha, usuario y texto en los logs de auditoría e historial de respaldos.
*   **Validación de Backup Dinámica**: Mejorar el matching de archivos físicos con expresiones regulares más flexibles.
*   **Sistema de Logging Profesional**: Migrar los prints de depuración a un logger que rote archivos dentro del contenedor Docker.

### 🚀 Próximo Paso Sugerido
Implementar el **Endpoint de Salud Global** y el **Retention Manager** para asegurar la escalabilidad del Dashboard y la integridad del almacenamiento.
