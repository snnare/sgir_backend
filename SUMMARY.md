# SGIR - Resumen del Estado Actual del Proyecto

## 📅 Fecha: 14 de Abril, 2026 (Sesión de Robustez SSH y Conectividad)

### ✅ Módulos Implementados y Mejorados
1.  **Orquestador SSH Avanzado**: 
    *   Refactorización completa de `dynamic_ssh_core` a `ssh_orchestrator`.
    *   Implementación de perfiles `SSH_LEGACY` (RHEL 4/5) y `SSH_NO_LEGACY` (Modernos).
    *   Sistema de **3 reintentos con espera de 5 segundos** ante fallos de red.
    *   Garantía de **Responsabilidad Única**: El orquestador solo gestiona la conexión, no la ejecución.
2.  **Seguridad y Usuarios**: 
    *   Confirmación de endpoints de Login/Register con hashing Bcrypt y auditoría automática.
    *   Validación de tipo de acceso SSH obligatoria para credenciales.
3.  **Conectividad Front-Back**: 
    *   Nuevo endpoint `/ping` público para facilitar pruebas de integración con el Frontend.
    *   Configuración de red de host en Docker para acceso directo.
4.  **SRE & Monitoreo**: 
    *   Soporte funcional para extracción de métricas (CPU, RAM, Disco, Uptime) a través del nuevo orquestador.
5.  **Dockerización**: 
    *   Imagen optimizada basada en `Python 3.14` y `uv`, con usuario no privilegiado para mayor seguridad.

### 🔐 Documentación y Pruebas
*   **Pruebas de Stress SSH**: Verificación exitosa de reintentos mediante puertos cerrados y conexiones concurrentes a contenedores de prueba.
*   **Trazabilidad**: Cada intento de conexión (exitoso o fallido) queda registrado en los logs del backend y en la bitácora de auditoría.

### ⚠️ Notas de Estabilidad
*   El sistema ahora es resiliente a micro-cortes de red gracias a la lógica de reintentos en el orquestador SSH.

### 🚀 Próximos Pasos Sugeridos
*   Implementar el **Scheduler (APScheduler)** para automatizar la recolección periódica de métricas usando el nuevo orquestador.
*   Desarrollar el soporte para **Oracle 19c/10g**.
*   Diseñar el Frontend para la visualización de los tableros de control.
