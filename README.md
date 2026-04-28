# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para la observabilidad de infraestructura crítica (SRE), gestión automatizada de respaldos y monitoreo inteligente multi-motor.

## 📁 Estructura del Proyecto

El proyecto sigue una **Arquitectura Simétrica por Dominios**:

*   **`app/core/`**: Núcleo del sistema. Incluye el orquestador SSH (Moderno/Legacy), el **Scheduler de Alta Disponibilidad** y gestión de seguridad AES-256.
*   **`app/services/monitoring/`**: 
    *   `ssh_service`: Monitoreo de Host con **Live Cache** en memoria.
    *   `db_unified_service`: Monitoreo unificado de DBs (**Oracle, MySQL, MongoDB**) con lógica de criticidad.
    *   `import_service`: Motor de carga masiva (CSV) con normalización automática.
*   **`plantilla/`**: Plantillas CSV oficiales para despliegue rápido de inventario.
*   **`app/models/`**, **`app/schemas/`**, **`app/routes/`**: Persistencia, validación y APIs organizadas por dominios lógicos.

## 🚀 Capacidades Principales

### 📊 Observabilidad y Monitoreo (Full-Stack)
*   **Monitoreo de Host (SSH):** Extracción de CPU, RAM, Disco y Uptime (Soporta **Legacy RHEL 4/5**).
*   **Monitoreo Unificado de DB:** Un solo estándar para Oracle, MySQL y MongoDB.
*   **Live Cache:** Almacenamiento en RAM de métricas en tiempo real para alimentar las tarjetas (Cards) del Frontend sin latencia.
*   **Monitoreo Silencioso (Umbrales):** La base de datos solo persiste métricas cuando se supera el **90%** de uso, optimizando el almacenamiento.
*   **Scheduler por Criticidad:** Ejecución automática de tareas (Crítico: 1m, Alto: 5m, etc.) usando un **Pool de 80 hilos** paralelos.

### 🏗️ Gestión de Inventario y Respaldos
*   **Importación Masiva:** Alta de servidores, instancias y credenciales vía CSV con cifrado automático.
*   **Descubrimiento de Respaldos:** Rastreo SSH de archivos físicos (`.sql`, `.dmp`, `.archive`) y sincronización con la CMDB.

### 🔐 Seguridad y Notificaciones
*   **Centro de Notificaciones:** Endpoints dedicados para gestionar alertas activas y resolución de incidentes desde el Dashboard.
*   **Auditoría SRE:** Bitácora inmutable de cada acción realizada por usuarios o procesos automáticos.

## 🛠️ Stack Tecnológico
*   **Backend:** FastAPI (Python 3.14) + SQLAlchemy 2.0
*   **Motor de Tareas:** APScheduler (Async + ThreadPool)
*   **Base de Datos:** PostgreSQL 16
*   **Gestión SSH:** Paramiko (Algoritmos Legacy habilitados)
*   **DevOps:** Docker (Multi-stage) + `uv`
