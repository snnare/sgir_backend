# SGIR - Resumen del Estado Actual del Proyecto

## 📅 Fecha: 22 de Abril, 2026 (Monitoreo Modular de Oracle Validado)

### ✅ Módulos Implementados y Mejorados
1.  **Monitoreo Modular de Oracle (Nuevo)**:
    *   **Arquitectura de Proveedores**: Implementados proveedores independientes para Conectividad (Grupo A), Recursos (Grupo B) y Rendimiento (Grupo C).
    *   **Lógica de Criticidad**: El sistema ahora decide qué grupos de métricas recolectar basándose en el catálogo de `Nivel_Criticidad` del servidor (Bajo -> A; Medio -> A+B; Alto/Crítico -> A+B+C).
    *   **Corrección de Core Dinámico**: Se ajustó `dynamic_db_core.py` para eliminar parámetros incompatibles con el driver `oracledb` y soportar el Service Name `XEPDB1` por defecto.
    *   **Validación Real**: Verificado exitosamente con un contenedor Oracle 21c Express Edition, obteniendo métricas de SGA, sesiones y CPU.
2.  **Auto-Descubrimiento de Inventario (Validado)**:
    *   **MySQL 5 & 8**: Consultas unificadas a `information_schema` con sincronización automatizada (Upserts) en la CMDB.
3.  **Simetría Arquitectónica y CRUD**:
    *   Estructura de capas (`routes`, `schemas`, `services`) totalmente simétrica.
    *   Verificación de integridad referencial completada en todas las tablas del modelo físico (Catálogos, Infraestructura, Respaldos y Monitoreo).
4.  **Motor SSH Modular**:
    *   **Orquestador Inteligente**: Soporte para perfiles Legacy (RHEL 4/5) y Modernos con gestión de reintentos.
    *   **Discovery Provider**: Motor listo para búsqueda de archivos remotos (find adaptativo), pendiente de exposición vía endpoint.

### 🔐 Infraestructura Registrada (Entorno de Pruebas)
*   **Servidores**: `127.0.0.1` (MySQL) y `172.18.0.4` (Oracle 21c).
*   **Instancias**: `MYSQL5_PROD`, `MYSQL8_PROD` y `XEPDB1` (Oracle).
*   **Credenciales**: Usuario `SYSTEM` validado para Oracle y `sgir_monitoreo` para MySQL.

### 🚀 Próximos Pasos Sugeridos
*   **Endpoint de Rastreo SSH**: Exponer el `discovery_provider.py` para permitir la búsqueda de archivos de respaldo físicos desde la API.
*   **SSH Tunneling (Jump Server)**: Implementar el soporte de túneles para alcanzar bases de datos en redes segmentadas.
*   **Implementar el Scheduler (APScheduler)**: Automatizar la ejecución periódica de las tareas de monitoreo modular y descubrimiento.
