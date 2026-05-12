# SGIR API Routes Map

This document lists all active endpoints in the SGIR Backend, their HTTP methods, and the files where they are implemented.

| Method | Endpoint | Source File |
|:-------|:---------|:------------|
| **ROOT** | | |
| GET | `/` | `app/main.py` |
| GET | `/ping` | `app/main.py` |
| **HEALTH** | | |
| GET | `/health/postgres` | `app/routes/healths/health_routes.py` |
| POST | `/health/ping` | `app/routes/healths/health_routes.py` |
| **SECURITY** | | |
| POST | `/users/login` | `app/routes/core_crud/security/user_routes.py` |
| POST | `/users/logout` | `app/routes/core_crud/security/user_routes.py` |
| GET | `/users/me` | `app/routes/core_crud/security/user_routes.py` |
| POST | `/users/` | `app/routes/core_crud/security/user_routes.py` |
| GET | `/users/` | `app/routes/core_crud/security/user_routes.py` |
| GET | `/users/{user_id}` | `app/routes/core_crud/security/user_routes.py` |
| GET | `/users/email/{email}` | `app/routes/core_crud/security/user_routes.py` |
| PUT | `/users/{user_id}` | `app/routes/core_crud/security/user_routes.py` |
| PUT | `/users/{user_id}/password` | `app/routes/core_crud/security/user_routes.py` |
| PUT | `/users/email/{email}` | `app/routes/core_crud/security/user_routes.py` |
| DELETE | `/users/{user_id}` | `app/routes/core_crud/security/user_routes.py` |
| DELETE | `/users/email/{email}` | `app/routes/core_crud/security/user_routes.py` |
| POST | `/roles/` | `app/routes/core_crud/security/rol_usuario_routes.py` |
| GET | `/roles/` | `app/routes/core_crud/security/rol_usuario_routes.py` |
| GET | `/roles/{role_id}` | `app/routes/core_crud/security/rol_usuario_routes.py` |
| DELETE | `/roles/{role_id}` | `app/routes/core_crud/security/rol_usuario_routes.py` |
| **INFRASTRUCTURE (CMDB)** | | |
| POST | `/servidores/import-bulk` | `app/routes/core_crud/infrastructure/servidor_routes.py` |
| POST | `/servidores/` | `app/routes/core_crud/infrastructure/servidor_routes.py` |
| GET | `/servidores/` | `app/routes/core_crud/infrastructure/servidor_routes.py` |
| GET | `/servidores/{servidor_id}` | `app/routes/core_crud/infrastructure/servidor_routes.py` |
| GET | `/servidores/ip/{ip}` | `app/routes/core_crud/infrastructure/servidor_routes.py` |
| GET | `/servidores/ping/{ip_server}` | `app/routes/core_crud/infrastructure/servidor_routes.py` |
| PUT | `/servidores/{servidor_id}` | `app/routes/core_crud/infrastructure/servidor_routes.py` |
| DELETE | `/servidores/{servidor_id}` | `app/routes/core_crud/infrastructure/servidor_routes.py` |
| POST | `/particiones/` | `app/routes/core_crud/infrastructure/servidor_particion_routes.py` |
| GET | `/particiones/servidor/{servidor_id}` | `app/routes/core_crud/infrastructure/servidor_particion_routes.py` |
| POST | `/particiones/register-upsert` | `app/routes/core_crud/infrastructure/servidor_particion_routes.py` |
| DELETE | `/particiones/{id_particion}` | `app/routes/core_crud/infrastructure/servidor_particion_routes.py` |
| POST | `/credenciales/` | `app/routes/core_crud/infrastructure/credencial_acceso_routes.py` |
| GET | `/credenciales/` | `app/routes/core_crud/infrastructure/credencial_acceso_routes.py` |
| GET | `/credenciales/servidor/{servidor_id}` | `app/routes/core_crud/infrastructure/credencial_acceso_routes.py` |
| PUT | `/credenciales/{credencial_id}` | `app/routes/core_crud/infrastructure/credencial_acceso_routes.py` |
| DELETE | `/credenciales/{credencial_id}` | `app/routes/core_crud/infrastructure/credencial_acceso_routes.py` |
| POST | `/credenciales/test-ssh/{id_servidor}/{id_credencial}` | `app/routes/core_crud/infrastructure/credencial_acceso_routes.py` |
| POST | `/dbms/` | `app/routes/core_crud/infrastructure/dbms_routes.py` |
| GET | `/dbms/` | `app/routes/core_crud/infrastructure/dbms_routes.py` |
| POST | `/instancias/` | `app/routes/core_crud/infrastructure/instancia_routes.py` |
| GET | `/instancias/servidor/{servidor_id}` | `app/routes/core_crud/infrastructure/instancia_routes.py` |
| POST | `/instancias/test-db/{id_instancia}/{id_credencial}` | `app/routes/core_crud/infrastructure/instancia_routes.py` |
| POST | `/bases-de-datos/` | `app/routes/core_crud/infrastructure/base_de_datos_routes.py` |
| GET | `/bases-de-datos/servidor/{servidor_id}` | `app/routes/core_crud/infrastructure/base_de_datos_routes.py` |
| GET | `/bases-de-datos/search` | `app/routes/core_crud/infrastructure/base_de_datos_routes.py` |
| GET | `/bases-de-datos/filter` | `app/routes/core_crud/infrastructure/base_de_datos_routes.py` |
| POST | `/conexion/test/db/{motor}` | `app/routes/core_crud/infrastructure/conexion_routes.py` |
| POST | `/conexion/test/ssh` | `app/routes/core_crud/infrastructure/conexion_routes.py` |
| **BACKUPS** | | |
| POST | `/tipo-respaldo/` | `app/routes/core_crud/backups/tipo_respaldo_routes.py` |
| GET | `/tipo-respaldo/` | `app/routes/core_crud/backups/tipo_respaldo_routes.py` |
| DELETE | `/tipo-respaldo/{tipo_id}` | `app/routes/core_crud/backups/tipo_respaldo_routes.py` |
| POST | `/tipo-almacenamiento/` | `app/routes/core_crud/backups/tipo_almacenamiento_routes.py` |
| GET | `/tipo-almacenamiento/` | `app/routes/core_crud/backups/tipo_almacenamiento_routes.py` |
| DELETE | `/tipo-almacenamiento/{tipo_id}` | `app/routes/core_crud/backups/tipo_almacenamiento_routes.py` |
| POST | `/rutas-respaldo/` | `app/routes/core_crud/backups/ruta_respaldo_routes.py` |
| GET | `/rutas-respaldo/` | `app/routes/core_crud/backups/ruta_respaldo_routes.py` |
| GET | `/rutas-respaldo/servidor/{servidor_id}` | `app/routes/core_crud/backups/ruta_respaldo_routes.py` |
| PUT | `/rutas-respaldo/{ruta_id}` | `app/routes/core_crud/backups/ruta_respaldo_routes.py` |
| DELETE | `/rutas-respaldo/{ruta_id}` | `app/routes/core_crud/backups/ruta_respaldo_routes.py` |
| POST | `/politicas-respaldo/` | `app/routes/core_crud/backups/politica_respaldo_routes.py` |
| GET | `/politicas-respaldo/` | `app/routes/core_crud/backups/politica_respaldo_routes.py` |
| PUT | `/politicas-respaldo/{politica_id}` | `app/routes/core_crud/backups/politica_respaldo_routes.py` |
| DELETE | `/politicas-respaldo/{politica_id}` | `app/routes/core_crud/backups/politica_respaldo_routes.py` |
| POST | `/asignacion-politica/` | `app/routes/core_crud/backups/asignacion_politica_routes.py` |
| DELETE | `/asignacion-politica/{id_base_datos}/{id_politica}` | `app/routes/core_crud/backups/asignacion_politica_routes.py` |
| POST | `/respaldos/` | `app/routes/core_crud/backups/respaldo_routes.py` |
| GET | `/respaldos/historial` | `app/routes/core_crud/backups/respaldo_routes.py` |
| **MONITORING & ALERTING** | | |
| GET | `/alertas/active` | `app/routes/core_crud/catalogs/alerta_routes.py` |
| GET | `/alertas/summary` | `app/routes/core_crud/catalogs/alerta_routes.py` |
| GET | `/alertas/today` | `app/routes/core_crud/catalogs/alerta_routes.py` |
| GET | `/alertas/recent` | `app/routes/core_crud/catalogs/alerta_routes.py` |
| GET | `/alertas/servidor/{servidor_id}` | `app/routes/core_crud/catalogs/alerta_routes.py` |
| POST | `/alertas/` | `app/routes/core_crud/catalogs/alerta_routes.py` |
| PUT | `/alertas/{alerta_id}/resolve` | `app/routes/core_crud/catalogs/alerta_routes.py` |
| GET | `/estados/` | `app/routes/core_crud/catalogs/estado_general_routes.py` |
| POST | `/estados/` | `app/routes/core_crud/catalogs/estado_general_routes.py` |
| DELETE | `/estados/{status_id}` | `app/routes/core_crud/catalogs/estado_general_routes.py` |
| POST | `/metricas/` | `app/routes/core_crud/catalogs/metrica_routes.py` |
| POST | `/monitoreo/` | `app/routes/core_crud/catalogs/monitoreo_routes.py` |
| GET | `/monitoreo/{monitoreo_id}` | `app/routes/core_crud/catalogs/monitoreo_routes.py` |
| PUT | `/monitoreo/{monitoreo_id}/close` | `app/routes/core_crud/catalogs/monitoreo_routes.py` |
| GET | `/nivel-alerta/` | `app/routes/core_crud/catalogs/nivel_alerta_routes.py` |
| POST | `/nivel-alerta/` | `app/routes/core_crud/catalogs/nivel_alerta_routes.py` |
| DELETE | `/nivel-alerta/{nivel_id}` | `app/routes/core_crud/catalogs/nivel_alerta_routes.py` |
| GET | `/criticidad/` | `app/routes/core_crud/catalogs/nivel_criticidad_routes.py` |
| POST | `/criticidad/` | `app/routes/core_crud/catalogs/nivel_criticidad_routes.py` |
| DELETE | `/criticidad/{nivel_id}` | `app/routes/core_crud/catalogs/nivel_criticidad_routes.py` |
| GET | `/tipo-acceso/` | `app/routes/core_crud/catalogs/tipo_acceso_routes.py` |
| POST | `/tipo-acceso/` | `app/routes/core_crud/catalogs/tipo_acceso_routes.py` |
| DELETE | `/tipo-acceso/{tipo_id}` | `app/routes/core_crud/catalogs/tipo_acceso_routes.py` |
| GET | `/tipo-metrica/` | `app/routes/core_crud/catalogs/tipo_metrica_routes.py` |
| POST | `/tipo-metrica/` | `app/routes/core_crud/catalogs/tipo_metrica_routes.py` |
| DELETE | `/tipo-metrica/{tipo_id}` | `app/routes/core_crud/catalogs/tipo_metrica_routes.py` |
| **AUDIT** | | |
| GET | `/audit-logs/` | `app/routes/core_crud/audit/bitacora_routes.py` |
| GET | `/audit-logs/{bitacora_id}` | `app/routes/core_crud/audit/bitacora_routes.py` |
| POST | `/audit-types/` | `app/routes/core_crud/audit/tipo_evento_auditoria_routes.py` |
| GET | `/audit-types/` | `app/routes/core_crud/audit/tipo_evento_auditoria_routes.py` |
| GET | `/audit-types/{tipo_id}` | `app/routes/core_crud/audit/tipo_evento_auditoria_routes.py` |
| DELETE | `/audit-types/{tipo_id}` | `app/routes/core_crud/audit/tipo_evento_auditoria_routes.py` |
| **MONITORING (OPERATIONAL)** | | |
| GET | `/monitoring/db/health-status/{instancia_id}` | `app/routes/monitoring/db_monitoring_routes.py` |
| POST | `/monitoring/db/run-adhoc/{instancia_id}/{credencial_id}` | `app/routes/monitoring/db_monitoring_routes.py` |
| GET | `/monitoring/host/scheduler/status` | `app/routes/monitoring/host_monitoring_routes.py` |
| POST | `/monitoring/host/scheduler/pause` | `app/routes/monitoring/host_monitoring_routes.py` |
| POST | `/monitoring/host/scheduler/resume` | `app/routes/monitoring/host_monitoring_routes.py` |
| POST | `/monitoring/host/scheduler/trigger-backup-retention` | `app/routes/monitoring/host_monitoring_routes.py` |
| GET | `/monitoring/host/global-summary` | `app/routes/monitoring/host_monitoring_routes.py` |
| GET | `/monitoring/host/live-cache` | `app/routes/monitoring/host_monitoring_routes.py` |
| GET | `/monitoring/host/health-status/{server_id}` | `app/routes/monitoring/host_monitoring_routes.py` |
| GET | `/monitoring/host/discover-filesystems/{servidor_id}` | `app/routes/monitoring/host_monitoring_routes.py` |
| GET | `/monitoring/host/{server_id}/{cred_id}` | `app/routes/monitoring/host_monitoring_routes.py` |
| GET | `/monitoring/inventory/assets` | `app/routes/monitoring/inventory_discovery_routes.py` |
| POST | `/monitoring/inventory/discover-all` | `app/routes/monitoring/inventory_discovery_routes.py` |
| POST | `/monitoring/inventory/discover/{instancia_id}/{credencial_id}` | `app/routes/monitoring/inventory_discovery_routes.py` |
| POST | `/monitoring/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}` | `app/routes/monitoring/inventory_discovery_routes.py` |
| POST | `/monitoring/inventory/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}` | `app/routes/monitoring/inventory_discovery_routes.py` |
| GET | `/monitoring/inventory/summary/{servidor_id}` | `app/routes/monitoring/inventory_discovery_routes.py` |
| GET | `/monitoring/mongodb/{servidor_id}/{credencial_id}` | `app/routes/monitoring/mongodb_monitoring_routes.py` |
| GET | `/monitoring/mysql5/{servidor_id}/{credencial_id}` | `app/routes/monitoring/mysql5_monitoring_routes.py` |
| GET | `/monitoring/mysql8/{servidor_id}/{credencial_id}` | `app/routes/monitoring/mysql8_monitoring_routes.py` |
| GET | `/monitoring/oracle/{id_instancia}/{id_credencial}` | `app/routes/monitoring/oracle_monitoring_routes.py` |
| GET | `/monitoring/mysql5/metrics/{id_instancia}` | `app/routes/monitoring/mysql/mysql5.py` |
