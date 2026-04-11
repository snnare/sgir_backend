# SGIR - Resumen del Estado Actual del Proyecto

## 📅 Fecha: 11 de Abril, 2026 (Sesión Actualizada)

### ✅ Módulos Implementados
1.  **Core CRUD**: Gestión completa de Usuarios, Roles, Auditoría (Tipos y Logs), Infraestructura (Servidores, Criticidad, Accesos, Credenciales), DBMS, Instancias y Bases de Datos.
2.  **Backups**: Gestión de Políticas, Rutas de Respaldo, Asignaciones y Registro Histórico de Ejecuciones.
3.  **Seguridad**: Paquete modular `app/core/security/` con soporte para Hashing (Bcrypt), JWT Tokens y Cifrado Reversible (Fernet).
4.  **Monitoreo**: Implementación dinámica para MySQL 5, MySQL 8 y MongoDB.
5.  **Inventario Inteligente**: Servicio de sincronización (Upsert) que escanea motores remotos y actualiza la capacidad local.

### 🔐 Seguridad y Acceso
*   Rutas públicas: `/users/` (Registro) y `/users/login` (Auth).
*   Rutas protegidas: Todas las demás requieren cabecera `Authorization: Bearer <token>`.
*   Variable `SECRET_KEY` en `.env` debe ser de 32 bytes codificada en base64 para el funcionamiento de Fernet.

### ⚙️ Configuración de Puertos (Docker Test)
*   **MySQL 5**: Puerto `3305`
*   **MySQL 8**: Puerto `3308`
*   **MongoDB**: Puerto `27017`
*   **Backend**: Puerto `8000`

### 🚀 Próximos Pasos Sugeridos
*   Implementar el monitoreo vía **SSH** para la capa de Host (CPU, RAM, Disco).
*   Desarrollar el soporte para **Oracle 19c/10g**.
*   Añadir el **Scheduler** para automatizar la recolección de métricas y sincronización de inventario.
*   Implementar el frontend para consumir estos servicios.
