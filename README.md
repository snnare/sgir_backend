# SGIR - Sistema de Gestión de Infraestructura y Respaldos

SGIR es una plataforma de backend robusta desarrollada con **FastAPI** y **PostgreSQL**, diseñada para la observabilidad de infraestructura crítica, gestión de respaldos y monitoreo de bases de datos.

## 🚀 Características Principales

### 🔐 Seguridad y Compliance
*   **JWT & Bcrypt:** Gestión de sesiones seguras con endpoint de **Logout** auditado.
*   **Cifrado Reversible (Fernet/AES):** Almacenamiento seguro de credenciales para acceso remoto automatizado.
*   **Gestión de Perfiles:** Separación estricta entre actualización de datos básicos y cambio de contraseñas (con validación de credencial anterior).
*   **Auditoría Total:** Registro inmutable de operaciones (Logins, Logout, CRUD, Monitoreo).

### 🏗️ CMDB e Inventario
*   **Discovery Service:** Escaneo remoto para descubrir bases de datos y tamaños.
*   **Integridad de Datos:** Validación automática de **IPs duplicadas** en el registro de servidores.
*   **Inventario Dinámico:** Gestión de servidores, DBMS, instancias y BDs.
*   **Estados Generales:** Sistema centralizado para definir estados (Activo, Inactivo, En Progreso, etc.) aplicables a todo el inventario.

### 📊 Monitoreo Multi-Motor y Conectividad (SRE)
*   **Orquestador SSH Robusto:** Módulo especializado con perfiles diferenciados (`Legacy` vs `Modern`), lógica de **3 reintentos** y esperas de 5s para alta disponibilidad en el monitoreo.
*   **Motores Soportados:** MySQL 5, MySQL 8, MongoDB.
*   **Host Monitoring:** Monitoreo vía SSH de CPU, RAM, Disco y Uptime (compatible con RHEL 4+).
*   **Validación de Políticas:** Protección contra valores inválidos (negativos) en frecuencias y periodos de retención.

## 🛠️ Stack Tecnológico

*   **Framework:** FastAPI (Python 3.14)
*   **ORM:** SQLAlchemy 2.0 (PostgreSQL)
*   **Gestión:** `uv` (Fastest Python package manager)
*   **Contenerización:** Docker (Multi-stage build)

## 📁 Estructura y Documentación

*   `/docs`: Swagger UI interactivo (con el servidor corriendo).
*   `/ping`: Endpoint de prueba de conectividad pública para el Frontend.
*   `workflow.txt`: Catálogo exhaustivo de endpoints con ejemplos `curl` probados.
*   `app/core/ssh_orchestrator.py`: Núcleo de conectividad remota segura.

## 🧪 Pruebas Rápidas
Consulta `workflow.txt` para encontrar los comandos `curl` de registro, seguridad y monitoreo listos para copiar y pegar.
