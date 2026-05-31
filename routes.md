# 🗺️ SGIR API Routes Reference Map

This document lists all active routes in the SGIR backend categorized by operational modules: **CRUD (Core & Catalog Configuration)**, **Módulo 1 (Observabilidad & Salud)**, **Módulo 2 (CMDB & Descubrimiento)**, and **Módulo 3 (Gestión de Respaldos)**. For each route, you will find the HTTP method, the endpoint path, the specific Python service executing the business logic, and the expected request body or response format.

---

## 🛠️ Módulo CRUD
Contiene las operaciones del catálogo relacional y configuraciones base. El prefijo global de estos endpoints es `/sgir/v1/crud`.

### 🔑 Seguridad y Control de Acceso

#### **`POST`** `/users/`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `create_user`
*   **Body Requerido (`UserCreate`):**
    ```json
    {
      "email": "juan.perez@example.com",
      "nombres": "Juan",
      "apellidos": "Pérez",
      "password": "PasswordSeguro123",
      "id_rol": 2,
      "id_estado_usuario": 1
    }
    ```
*   **Response Esperada (Status 201 - `UserResponse`):**
    ```json
    {
      "id_usuario": 1,
      "email": "juan.perez@example.com",
      "nombres": "Juan",
      "apellidos": "Pérez",
      "fecha_creacion": "2026-05-22T18:00:00Z",
      "id_rol": 2,
      "id_estado_usuario": 1
    }
    ```

#### **`POST`** `/users/login`
*   **Servicio Ejecutor:** [`app/routes/core_crud/security/user_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/security/user_routes.py) $\rightarrow$ `login_user` (Valida con `user_crud.get_user_by_email` y hash)
*   **Body Requerido (Form-Data / OAuth2 Flow):**
    ```ini
    username = juan.perez@example.com
    password = PasswordSeguro123
    ```
*   **Response Esperada (Status 200 - `Token`):**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
      "token_type": "bearer"
    }
    ```

#### **`POST`** `/users/logout`
*   **Servicio Ejecutor:** [`app/routes/core_crud/security/user_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/security/user_routes.py) $\rightarrow$ `logout_user` (Registra en auditoría)
*   **Body Requerido:** *Sin Body (Requiere Token Bearer)*
*   **Response Esperada (Status 200):**
    ```json
    {
      "message": "Sesión cerrada exitosamente"
    }
    ```

#### **`PUT`** `/users/{user_id}`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `update_user`
*   **Body Requerido (`UserUpdate`):**
    ```json
    {
      "email": "juan.perez@example.com",
      "nombres": "Juan Modificado",
      "apellidos": "Pérez",
      "id_estado_usuario": 1
    }
    ```
*   **Response Esperada (Status 200 - `UserResponse`):**
    ```json
    {
      "id_usuario": 1,
      "email": "juan.perez@example.com",
      "nombres": "Juan Modificado",
      "apellidos": "Pérez",
      "fecha_creacion": "2026-05-22T18:00:00Z",
      "id_rol": 2,
      "id_estado_usuario": 1
    }
    ```

#### **`PUT`** `/users/{user_id}/password`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `update_user_password`
*   **Body Requerido (`UserPasswordUpdate`):**
    ```json
    {
      "old_password": "PasswordSeguro123",
      "new_password": "NuevoPassword456"
    }
    ```
*   **Response Esperada (Status 200):**
    ```json
    {
      "message": "Contraseña actualizada exitosamente"
    }
    ```

#### **`POST`** `/roles/`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `create_role`
*   **Body Requerido (`RoleCreate`):**
    ```json
    {
      "nombre_rol": "Operador"
    }
    ```
*   **Response Esperada (Status 201 - `RoleResponse`):**
    ```json
    {
      "id_rol": 3,
      "nombre_rol": "Operador"
    }
    ```

#### **`GET`** `/users/`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `get_users`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[UserResponse]`):**
    ```json
    [
      {
        "id_usuario": 1,
        "email": "admin@admin.com",
        "nombres": "Admin",
        "apellidos": "Sgir",
        "fecha_creacion": "2026-05-22T18:00:00Z",
        "id_rol": 1,
        "id_estado_usuario": 1
      }
    ]
    ```

#### **`GET`** `/users/{user_id}`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `get_user`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `UserResponse`):**
    ```json
    {
      "id_usuario": 1,
      "email": "juan.perez@example.com",
      "nombres": "Juan",
      "apellidos": "Pérez",
      "fecha_creacion": "2026-05-22T18:00:00Z",
      "id_rol": 2,
      "id_estado_usuario": 1
    }
    ```

#### **`GET`** `/users/email/{email}`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `get_user_by_email`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `UserResponse`):**
    ```json
    {
      "id_usuario": 1,
      "email": "juan.perez@example.com",
      "nombres": "Juan",
      "apellidos": "Pérez",
      "fecha_creacion": "2026-05-22T18:00:00Z",
      "id_rol": 2,
      "id_estado_usuario": 1
    }
    ```

#### **`GET`** `/users/me`
*   **Servicio Ejecutor:** [`app/routes/core_crud/security/user_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/security/user_routes.py) $\rightarrow$ `read_user_me` (Valores extraídos de la sesión/token actual)
*   **Body Requerido:** *Sin Body (Requiere Token Bearer)*
*   **Response Esperada (Status 200 - `UserResponse`):**
    ```json
    {
      "id_usuario": 1,
      "email": "admin@admin.com",
      "nombres": "Admin",
      "apellidos": "Sgir",
      "fecha_creacion": "2026-05-22T18:00:00Z",
      "id_rol": 1,
      "id_estado_usuario": 1
    }
    ```

#### **`DELETE`** `/users/{user_id}`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `delete_user`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`DELETE`** `/users/email/{email}`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `delete_user_by_email`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/roles/`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `get_roles`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[RoleResponse]`):**
    ```json
    [
      {
        "id_rol": 1,
        "nombre_rol": "Administrador"
      },
      {
        "id_rol": 2,
        "nombre_rol": "Técnico"
      }
    ]
    ```

#### **`GET`** `/roles/{role_id}`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `get_role_by_id`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `RoleResponse`):**
    ```json
    {
      "id_rol": 1,
      "nombre_rol": "Administrador"
    }
    ```

#### **`DELETE`** `/roles/{role_id}`
*   **Servicio Ejecutor:** [`app/services/security/user_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/security/user_crud.py) $\rightarrow$ `delete_role`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

---

### 🖥️ Infraestructura y Servidores (CMDB CRUD)

#### **`POST`** `/servidores/`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `create_servidor`
*   **Body Requerido (`ServidorCreate`):**
    ```json
    {
      "nombre_servidor": "Svr-Linux-01",
      "direccion_ip": "192.168.1.50",
      "es_legacy": false,
      "descripcion": "Servidor principal de producción",
      "monitoreo_host": true,
      "monitoreo_db": false,
      "id_nivel_criticidad": 2,
      "id_estado_servidor": 1
    }
    ```
*   **Response Esperada (Status 201 - `ServidorResponse`):**
    ```json
    {
      "id_servidor": 1,
      "nombre_servidor": "Svr-Linux-01",
      "direccion_ip": "192.168.1.50",
      "es_legacy": false,
      "descripcion": "Servidor principal de producción",
      "monitoreo_host": true,
      "monitoreo_db": false,
      "id_nivel_criticidad": 2,
      "id_estado_servidor": 1,
      "fecha_registro": "2026-05-22T18:00:00Z",
      "particiones": []
    }
    ```

#### **`POST`** `/servidores/import-bulk`
*   **Servicio Ejecutor:** [`app/services/infrastructure/import_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/import_service.py) $\rightarrow$ `process_infrastructure_csv`
*   **Body Requerido (Multipart/File Upload):** Archivo CSV adjunto con columnas del inventario de infraestructura.
*   **Response Esperada (Status 200):**
    ```json
    {
      "servidores_creados": 3,
      "instancias_creadas": 2,
      "credenciales_creadas": 3,
      "errores": []
    }
    ```

#### **`PUT`** `/servidores/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `update_servidor`
*   **Body Requerido (`ServidorUpdate`):**
    ```json
    {
      "nombre_servidor": "Svr-Linux-01-Prod",
      "monitoreo_db": true
    }
    ```
*   **Response Esperada (Status 200 - `ServidorResponse`):**
    ```json
    {
      "id_servidor": 1,
      "nombre_servidor": "Svr-Linux-01-Prod",
      "direccion_ip": "192.168.1.50",
      "es_legacy": false,
      "descripcion": "Servidor principal de producción",
      "monitoreo_host": true,
      "monitoreo_db": true,
      "id_nivel_criticidad": 2,
      "id_estado_servidor": 1,
      "fecha_registro": "2026-05-22T18:00:00Z",
      "particiones": []
    }
    ```

#### **`POST`** `/particiones/`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `create_particion`
*   **Body Requerido (`ServidorParticionCreate`):**
    ```json
    {
      "path": "/data",
      "etiqueta": "Disco de Datos",
      "id_servidor": 1
    }
    ```
*   **Response Esperada (Status 201 - `ServidorParticionResponse`):**
    ```json
    {
      "id_particion": 1,
      "path": "/data",
      "etiqueta": "Disco de Datos",
      "id_servidor": 1,
      "fecha_registro": "2026-05-22T18:00:00Z"
    }
    ```

#### **`POST`** `/particiones/register-upsert`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `register_partition_upsert`
*   **Body Requerido (`ServidorParticionCreate`):**
    ```json
    {
      "path": "/data",
      "etiqueta": "Disco de Datos",
      "id_servidor": 1
    }
    ```
*   **Response Esperada (Status 200 - `ServidorParticionResponse`):**
    ```json
    {
      "id_particion": 1,
      "path": "/data",
      "etiqueta": "Disco de Datos",
      "id_servidor": 1,
      "fecha_registro": "2026-05-22T18:00:00Z"
    }
    ```

#### **`POST`** `/credenciales/`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `create_credencial` (Encripta el password internamente)
*   **Body Requerido (`CredencialCreate`):**
    ```json
    {
      "usuario": "db_user",
      "password": "SuperPasswordDB123",
      "id_tipo_acceso": 2,
      "id_estado_credencial": 1,
      "id_servidor": 1
    }
    ```
*   **Response Esperada (Status 201 - `CredencialResponse`):**
    ```json
    {
      "id_credencial": 1,
      "usuario": "db_user",
      "id_tipo_acceso": 2,
      "id_estado_credencial": 1,
      "id_servidor": 1,
      "fecha_creacion": "2026-05-22T18:00:00Z"
    }
    ```

#### **`PUT`** `/credenciales/{credencial_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `update_credencial`
*   **Body Requerido (`CredencialUpdate`):**
    ```json
    {
      "usuario": "db_user_prod",
      "password": "NewSecretPassword456"
    }
    ```
*   **Response Esperada (Status 200 - `CredencialResponse`):**
    ```json
    {
      "id_credencial": 1,
      "usuario": "db_user_prod",
      "id_tipo_acceso": 2,
      "id_estado_credencial": 1,
      "id_servidor": 1,
      "fecha_creacion": "2026-05-22T18:00:00Z"
    }
    ```

#### **`POST`** `/dbms/`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `create_dbms`
*   **Body Requerido (`DBMSCreate`):**
    ```json
    {
      "nombre_dbms": "MySQL 8.x",
      "version": "8.0.32",
      "descripcion": "Motor relacional estándar para transacciones rápidas"
    }
    ```
*   **Response Esperada (Status 201 - `DBMSResponse`):**
    ```json
    {
      "id_dbms": 1,
      "nombre_dbms": "MySQL 8.x",
      "version": "8.0.32",
      "descripcion": "Motor relacional estándar para transacciones rápidas"
    }
    ```

#### **`POST`** `/instancias/`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `create_instancia`
*   **Body Requerido (`InstanciaCreate`):**
    ```json
    {
      "nombre_instancia": "mysql_prod_01",
      "puerto": 3306,
      "id_servidor": 1,
      "id_dbms": 1,
      "id_estado_instancia": 1,
      "parametros_conexion": {
        "sid": "OptionalOracleSIDOrMongoAuthSource"
      }
    }
    ```
*   **Response Esperada (Status 201 - `Instancia`):**
    ```json
    {
      "id_instancia": 1,
      "nombre_instancia": "mysql_prod_01",
      "puerto": 3306,
      "id_servidor": 1,
      "id_dbms": 1,
      "id_estado_instancia": 1,
      "parametros_conexion": {
        "sid": "OptionalOracleSIDOrMongoAuthSource"
      },
      "fecha_inicio": "2026-05-22T18:00:00Z"
    }
    ```

#### **`POST`** `/bases-de-datos/`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `create_base_datos`
*   **Body Requerido (`BaseDatosCreate`):**
    ```json
    {
      "nombre_base": "sgir_catalog",
      "tamano_mb": 120.50,
      "id_instancia": 1,
      "id_estado_bd": 1
    }
    ```
*   **Response Esperada (Status 201 - `BaseDatos`):**
    ```json
    {
      "id_base_datos": 1,
      "nombre_base": "sgir_catalog",
      "tamano_mb": 120.50,
      "id_instancia": 1,
      "id_estado_bd": 1,
      "fecha_creacion": "2026-05-22T18:00:00Z"
    }
    ```

#### **`POST`** `/conexion/test/db/{motor}`
*   **Servicio Ejecutor:** [`app/routes/core_crud/infrastructure/conexion_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/infrastructure/conexion_routes.py) $\rightarrow$ `test_db_connection` (Usa drivers pymysql, pymongo, etc., en caliente)
*   **Body Requerido (`ConnectionTestRequest`):**
    ```json
    {
      "direccion_ip": "192.168.1.100",
      "puerto": 3306,
      "usuario": "root",
      "password": "SuperSecurePassword"
    }
    ```
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "success",
      "message": "Conexión exitosa con MySQL"
    }
    ```

#### **`POST`** `/conexion/test/db/oracle/legacy`
*   **Servicio Ejecutor:** [`app/routes/core_crud/infrastructure/conexion_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/infrastructure/conexion_routes.py) $\rightarrow$ `test_oracle_legacy_connection` (Usa SSH y sqlplus local leyendo el SID de la CMDB)
*   **Body Requerido (`ConnectionTestRequest`):**
    ```json
    {
      "direccion_ip": "192.168.1.100",
      "puerto": 1521,
      "usuario": "system",
      "password": "Password10g"
    }
    ```
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "success",
      "message": "Conexión legacy exitosa con Oracle SID 'DbEvapem' (vía SSH/sqlplus local)"
    }
    ```

#### **`POST`** `/conexion/test/db/oracle/no-legacy`
*   **Servicio Ejecutor:** [`app/routes/core_crud/infrastructure/conexion_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/infrastructure/conexion_routes.py) $\rightarrow$ `test_oracle_no_legacy_connection` (Usa oracledb Thin Mode leyendo el ORACLE_SID de la CMDB)
*   **Body Requerido (`ConnectionTestRequest`):**
    ```json
    {
      "direccion_ip": "192.168.1.100",
      "puerto": 1521,
      "usuario": "system",
      "password": "Password19c"
    }
    ```
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "success",
      "message": "Conexión TCP estándar (No-Legacy) exitosa con Oracle"
    }
    ```


#### **`POST`** `/conexion/test/ssh`
*   **Servicio Ejecutor:** [`app/routes/core_crud/infrastructure/conexion_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/infrastructure/conexion_routes.py) $\rightarrow$ `test_ssh_connection` (Usa `ssh_no_legacy`/`ssh_legacy` en caliente)
*   **Body Requerido (`ConnectionTestRequest`):**
    ```json
    {
      "direccion_ip": "192.168.1.100",
      "puerto": 22,
      "usuario": "ubuntu",
      "password": "OptionalPassword"
    }
    ```
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "success",
      "message": "Conexión SSH estándar exitosa",
      "details": {
        "perfil": "Estándar"
      }
    }
    ```

#### **`GET`** `/servidores/`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_servidores`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[ServidorResponse]`):**
    ```json
    [
      {
        "id_servidor": 1,
        "nombre_servidor": "Svr-Linux-01",
        "direccion_ip": "192.168.1.50",
        "es_legacy": false,
        "descripcion": "Servidor principal de producción",
        "monitoreo_host": true,
        "monitoreo_db": false,
        "id_nivel_criticidad": 2,
        "id_estado_servidor": 1,
        "fecha_registro": "2026-05-22T18:00:00Z",
        "particiones": []
      }
    ]
    ```

#### **`GET`** `/servidores/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_servidor`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `ServidorResponse`):**
    ```json
    {
      "id_servidor": 1,
      "nombre_servidor": "Svr-Linux-01",
      "direccion_ip": "192.168.1.50",
      "es_legacy": false,
      "descripcion": "Servidor principal de producción",
      "monitoreo_host": true,
      "monitoreo_db": false,
      "id_nivel_criticidad": 2,
      "id_estado_servidor": 1,
      "fecha_registro": "2026-05-22T18:00:00Z",
      "particiones": [
        {
          "id_particion": 1,
          "path": "/data",
          "etiqueta": "Disco de Datos",
          "id_servidor": 1,
          "fecha_registro": "2026-05-22T18:00:00Z"
        }
      ],
      "instancias": [
        {
          "id_instancia": 1,
          "nombre_instancia": "mysql_prod_01",
          "puerto": 3306,
          "id_servidor": 1,
          "id_dbms": 1,
          "id_estado_instancia": 1,
          "parametros_conexion": null
        }
      ]
    }
    ```

#### **`GET`** `/servidores/ip/{ip}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_servidor_by_ip`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "message": "Servidor registrado",
      "server": {
        "id_servidor": 1,
        "nombre_servidor": "Svr-Linux-01",
        "direccion_ip": "192.168.1.50",
        "es_legacy": false,
        "id_nivel_criticidad": 2,
        "id_estado_servidor": 1,
        "fecha_registro": "2026-05-22T18:00:00Z"
      }
    }
    ```

#### **`GET`** `/servidores/ping/{ip_server}`
*   **Servicio Ejecutor:** [`app/routes/core_crud/infrastructure/servidor_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/infrastructure/servidor_routes.py) $\rightarrow$ `ping_server` (Dispara un ping ICMP rápido)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):** `true` si el host es alcanzable, `false` de lo contrario.

#### **`DELETE`** `/servidores/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `delete_servidor`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/particiones/servidor/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_particiones_by_servidor`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[ServidorParticionResponse]`):**
    ```json
    [
      {
        "id_particion": 1,
        "path": "/data",
        "etiqueta": "Disco de Datos",
        "id_servidor": 1,
        "fecha_registro": "2026-05-22T18:00:00Z"
      }
    ]
    ```

#### **`DELETE`** `/particiones/{id_particion}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `delete_particion`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/credenciales/`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_credenciales_all` (Decodifica o enmascara passwords)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[CredencialFullResponse]`):**
    ```json
    [
      {
        "id_credencial": 1,
        "usuario": "db_user",
        "fecha_creacion": "2026-05-22T18:00:00Z",
        "id_servidor": 1,
        "servidor_nombre": "Svr-Linux-01",
        "tipo": {
          "id_tipo_acceso": 2,
          "nombre_tipo": "Database Native"
        },
        "estado": {
          "id_estado": 1,
          "nombre_estado": "Activo"
        }
      }
    ]
    ```

#### **`GET`** `/credenciales/servidor/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_credenciales_by_servidor`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[CredencialResponse]`):**
    ```json
    [
      {
        "id_credencial": 1,
        "usuario": "db_user",
        "id_tipo_acceso": 2,
        "id_estado_credencial": 1,
        "id_servidor": 1,
        "fecha_creacion": "2026-05-22T18:00:00Z"
      }
    ]
    ```

#### **`POST`** `/credenciales/test-ssh/{id_servidor}/{id_credencial}`
*   **Servicio Ejecutor:** [`app/routes/core_crud/infrastructure/credencial_acceso_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/infrastructure/credencial_acceso_routes.py) $\rightarrow$ `test_ssh_connectivity` (Orquesta la conexión SSH con parámetros persistidos)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "success",
      "message": "Conexión exitosa a 192.168.1.100",
      "details": {
        "perfil_utilizado": "Estándar",
        "usuario_remoto": "ubuntu",
        "uptime_servidor": "up 12 days, 4 hours"
      }
    }
    ```

#### **`DELETE`** `/credenciales/{credencial_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `delete_credencial`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/dbms/`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_dbms_all`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[DBMSResponse]`):**
    ```json
    [
      {
        "id_dbms": 1,
        "nombre_dbms": "MySQL 8.x",
        "version": "8.0.32",
        "descripcion": "Motor relacional estándar para transacciones rápidas"
      }
    ]
    ```

#### **`GET`** `/instancias/servidor/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_instancias_by_servidor`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[Instancia]`):**
    ```json
    [
      {
        "id_instancia": 1,
        "nombre_instancia": "mysql_prod_01",
        "puerto": 3306,
        "id_servidor": 1,
        "id_dbms": 1,
        "id_estado_instancia": 1,
        "fecha_inicio": "2026-05-22T18:00:00Z"
      }
    ]
    ```

#### **`POST`** `/instancias/test-db/{id_instancia}/{id_credencial}`
*   **Servicio Ejecutor:** [`app/routes/core_crud/infrastructure/instancia_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/core_crud/infrastructure/instancia_routes.py) $\rightarrow$ `test_db_connectivity` (Orquesta la conexión al motor de base de datos)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "success",
      "message": "Conexión exitosa a la base de datos en 192.168.1.100:3306",
      "details": {
        "dbms_id": 3,
        "version_detectada": "8.0.32",
        "puerto_utilizado": 3306
      }
    }
    ```

#### **`GET`** `/bases-de-datos/servidor/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_bases_de_datos_by_servidor`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[BaseDatos]`):**
    ```json
    [
      {
        "id_base_datos": 1,
        "nombre_base": "sgir_catalog",
        "tamano_mb": 120.50,
        "id_instancia": 1,
        "id_estado_bd": 1,
        "fecha_creacion": "2026-05-22T18:00:00Z"
      }
    ]
    ```

#### **`GET`** `/bases-de-datos/search`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `search_bases_de_datos`
*   **Query Params:** `query` (Filtro por coincidencia parcial de nombre)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    [
      {
        "id_base_datos": 1,
        "nombre_base": "sgir_catalog",
        "ip_servidor": "192.168.1.100",
        "nombre_servidor": "Svr-Linux-01",
        "tipo_dbms": "MySQL 8.x",
        "version_dbms": "8.0.32",
        "estado_bd": "Activo"
      }
    ]
    ```

#### **`GET`** `/bases-de-datos/filter`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `filter_bases_de_datos`
*   **Query Params:** `nombre` (opcional), `ip` (opcional)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[BaseDatosSearchResult]`):**
    ```json
    [
      {
        "id_base_datos": 1,
        "nombre_base": "sgir_catalog",
        "ip_servidor": "192.168.1.100",
        "nombre_servidor": "Svr-Linux-01",
        "tipo_dbms": "MySQL 8.x",
        "version_dbms": "8.0.32",
        "estado_bd": "Activo"
      }
    ]
    ```

---

### 📂 Respaldos (CRUD & Políticas)

#### **`POST`** `/tipo-respaldo/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `create_tipo_respaldo`
*   **Body Requerido (`TipoRespaldoCreate`):**
    ```json
    {
      "nombre_tipo": "Físico"
    }
    ```
*   **Response Esperada (Status 201 - `TipoRespaldoResponse`):**
    ```json
    {
      "id_tipo_respaldo": 1,
      "nombre_tipo": "Físico"
    }
    ```

#### **`POST`** `/tipo-almacenamiento/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `create_tipo_almacenamiento`
*   **Body Requerido (`TipoAlmacenamientoCreate`):**
    ```json
    {
      "nombre_tipo": "S3 Bucket"
    }
    ```
*   **Response Esperada (Status 201 - `TipoAlmacenamientoResponse`):**
    ```json
    {
      "id_tipo_almacenamiento": 1,
      "nombre_tipo": "S3 Bucket"
    }
    ```

#### **`POST`** `/rutas-respaldo/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `create_ruta_respaldo`
*   **Body Requerido (`RutaRespaldoCreate`):**
    ```json
    {
      "descripcion_ruta": "Almacenamiento Local de Respaldos",
      "path": "/mnt/backups/mysql",
      "id_servidor": 1,
      "id_tipo_almacenamiento": 1,
      "id_estado_ruta": 1
    }
    ```
*   **Response Esperada (Status 201 - `RutaRespaldoResponse`):**
    ```json
    {
      "id_ruta": 1,
      "descripcion_ruta": "Almacenamiento Local de Respaldos",
      "path": "/mnt/backups/mysql",
      "id_servidor": 1,
      "id_tipo_almacenamiento": 1,
      "id_estado_ruta": 1
    }
    ```

#### **`PUT`** `/rutas-respaldo/{ruta_id}`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `update_ruta_respaldo`
*   **Body Requerido (`RutaRespaldoUpdate`):**
    ```json
    {
      "path": "/mnt/backups/mysql_v2"
    }
    ```
*   **Response Esperada (Status 200 - `RutaRespaldoResponse`):**
    ```json
    {
      "id_ruta": 1,
      "descripcion_ruta": "Almacenamiento Local de Respaldos",
      "path": "/mnt/backups/mysql_v2",
      "id_servidor": 1,
      "id_tipo_almacenamiento": 1,
      "id_estado_ruta": 1
    }
    ```

#### **`POST`** `/politicas-respaldo/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `create_politica_respaldo`
*   **Body Requerido (`PoliticaRespaldoCreate`):**
    ```json
    {
      "nombre_politica": "Semanal Retención 15d",
      "descripcion": "Respaldo completo semanal con ciclo de vida de 15 días",
      "frecuencia_horas": 168,
      "retencion_dias": 15,
      "id_tipo_respaldo": 1,
      "id_estado_politica": 1
    }
    ```
*   **Response Esperada (Status 201 - `PoliticaRespaldoResponse`):**
    ```json
    {
      "id_politica": 1,
      "nombre_politica": "Semanal Retención 15d",
      "descripcion": "Respaldo completo semanal con ciclo de vida de 15 días",
      "frecuencia_horas": 168,
      "retencion_dias": 15,
      "id_tipo_respaldo": 1,
      "id_estado_politica": 1
    }
    ```

#### **`PUT`** `/politicas-respaldo/{politica_id}`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `update_politica_respaldo`
*   **Body Requerido (`PoliticaRespaldoUpdate`):**
    ```json
    {
      "retencion_dias": 30
    }
    ```
*   **Response Esperada (Status 200 - `PoliticaRespaldoResponse`):**
    ```json
    {
      "id_politica": 1,
      "nombre_politica": "Semanal Retención 15d",
      "descripcion": "Respaldo completo semanal con ciclo de vida de 15 días",
      "frecuencia_horas": 168,
      "retencion_dias": 30,
      "id_tipo_respaldo": 1,
      "id_estado_politica": 1
    }
    ```

#### **`POST`** `/asignacion-politica/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `assign_policy_to_db`
*   **Body Requerido (`AsignacionPoliticaBDCreate`):**
    ```json
    {
      "id_base_datos": 1,
      "id_politica": 1
    }
    ```
*   **Response Esperada (Status 200):**
    ```json
    {
      "message": "Política 1 asignada correctamente a la base de datos 1"
    }
    ```

#### **`POST`** `/respaldos/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `create_registro_respaldo`
*   **Body Requerido (`RespaldoCreate`):**
    ```json
    {
      "id_base_datos": 1,
      "id_politica": 1,
      "id_credencial": 1,
      "id_ruta_respaldo": 1,
      "id_estado_ejecucion": 4,
      "tamano_mb": 420.50,
      "hash_integridad": "a3b2c1..."
    }
    ```
*   **Response Esperada (Status 201 - `RespaldoResponse`):**
    ```json
    {
      "id_respaldo": 1,
      "fecha_inicio": "2026-05-22T18:00:00Z",
      "fecha_fin": "2026-05-22T18:02:00Z",
      "tamano_mb": 420.50,
      "hash_integridad": "a3b2c1...",
      "id_base_datos": 1,
      "id_politica": 1,
      "id_credencial": 1,
      "id_ruta_respaldo": 1,
      "id_estado_ejecucion": 4
    }
    ```

#### **`GET`** `/tipo-respaldo/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `get_tipos_respaldo`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[TipoRespaldoResponse]`):**
    ```json
    [
      {
        "id_tipo_respaldo": 1,
        "nombre_tipo": "Físico"
      },
      {
        "id_tipo_respaldo": 2,
        "nombre_tipo": "Lógico"
      }
    ]
    ```

#### **`DELETE`** `/tipo-respaldo/{tipo_id}`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `delete_tipo_respaldo`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/tipo-almacenamiento/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `get_tipos_almacenamiento`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[TipoAlmacenamientoResponse]`):**
    ```json
    [
      {
        "id_tipo_almacenamiento": 1,
        "nombre_tipo": "S3 Bucket"
      },
      {
        "id_tipo_almacenamiento": 2,
        "nombre_tipo": "Local / NFS"
      }
    ]
    ```

#### **`DELETE`** `/tipo-almacenamiento/{tipo_id}`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `delete_tipo_almacenamiento`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/rutas-respaldo/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `get_rutas_respaldo`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[RutaRespaldoResponse]`):**
    ```json
    [
      {
        "id_ruta": 1,
        "descripcion_ruta": "Almacenamiento Local de Respaldos",
        "path": "/mnt/backups/mysql",
        "id_servidor": 1,
        "id_tipo_almacenamiento": 1,
        "id_estado_ruta": 1
      }
    ]
    ```

#### **`GET`** `/rutas-respaldo/servidor/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `get_rutas_respaldo_by_servidor`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[RutaRespaldoResponse]`):**
    ```json
    [
      {
        "id_ruta": 1,
        "descripcion_ruta": "Almacenamiento Local de Respaldos",
        "path": "/mnt/backups/mysql",
        "id_servidor": 1,
        "id_tipo_almacenamiento": 1,
        "id_estado_ruta": 1
      }
    ]
    ```

#### **`DELETE`** `/rutas-respaldo/{ruta_id}`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `delete_ruta_respaldo`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/politicas-respaldo/`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `get_politicas_respaldo`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[PoliticaRespaldoResponse]`):**
    ```json
    [
      {
        "id_politica": 1,
        "nombre_politica": "Semanal Retención 15d",
        "descripcion": "Respaldo completo semanal con ciclo de vida de 15 días",
        "frecuencia_horas": 168,
        "retencion_dias": 15,
        "id_tipo_respaldo": 1,
        "id_estado_politica": 1
      }
    ]
    ```

#### **`GET`** `/politicas-respaldo/{politica_id}/assets`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `get_politica_assets_grouped` (Agrupa base de datos e IP por servidor)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `PoliticaDetalleAssetsResponse`):**
    ```json
    {
      "id_politica": 1,
      "nombre_politica": "Semanal Retención 15d",
      "descripcion": "Respaldo completo semanal con ciclo de vida de 15 días",
      "frecuencia_horas": 168,
      "retencion_dias": 15,
      "servidores_vinculados": [
        {
          "ip": "192.168.1.100",
          "motor": "MySQL 8.x",
          "databases": [
            {
              "id_base_datos": 1,
              "nombre_base": "sgir_catalog",
              "tamano_mb": 120.50,
              "estado": "Activo"
            }
          ]
        }
      ]
    }
    ```

#### **`DELETE`** `/politicas-respaldo/{politica_id}`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `delete_politica_respaldo`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`DELETE`** `/asignacion-politica/{id_base_datos}/{id_politica}`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `unassign_policy_from_db`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "message": "Asignación eliminada exitosamente"
    }
    ```

#### **`GET`** `/respaldos/historial`
*   **Servicio Ejecutor:** [`app/services/backups/backup_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/backups/backup_crud.py) $\rightarrow$ `get_historial_respaldos`
*   **Query Params:** `id_base_datos` (opcional)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[RespaldoResponse]`):**
    ```json
    [
      {
        "id_respaldo": 1,
        "fecha_inicio": "2026-05-22T18:00:00Z",
        "fecha_fin": "2026-05-22T18:02:00Z",
        "tamano_mb": 420.50,
        "hash_integridad": "a3b2c1...",
        "id_base_datos": 1,
        "id_politica": 1,
        "id_credencial": 1,
        "id_ruta_respaldo": 1,
        "id_estado_ejecucion": 4
      }
    ]
    ```

---

### 🚨 Catálogos de Monitoreo & Alerting

#### **`POST`** `/alertas/`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `create_alert`
*   **Body Requerido (`AlertaCreate`):**
    ```json
    {
      "descripcion": "El uso del disco superó el umbral crítico del 90%",
      "id_servidor": 1,
      "id_monitoreo": null,
      "id_nivel_alerta": 3,
      "id_estado_alerta": 1
    }
    ```
*   **Response Esperada (Status 201 - `AlertaResponse`):**
    ```json
    {
      "id_alerta": 1,
      "descripcion": "El uso del disco superó el umbral crítico del 90%",
      "id_servidor": 1,
      "id_monitoreo": null,
      "id_nivel_alerta": 3,
      "id_estado_alerta": 1,
      "fecha_alerta": "2026-05-22T18:00:00Z"
    }
    ```

#### **`PUT`** `/alertas/{alerta_id}/resolve`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `resolve_alert`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `AlertaResponse`):**
    ```json
    {
      "id_alerta": 1,
      "descripcion": "El uso del disco superó el umbral crítico del 90%",
      "id_servidor": 1,
      "id_monitoreo": null,
      "id_nivel_alerta": 3,
      "id_estado_alerta": 2,
      "fecha_alerta": "2026-05-22T18:00:00Z"
    }
    ```

#### **`POST`** `/estados/`
*   **Servicio Ejecutor:** [`app/services/catalogs/status_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/status_crud.py) $\rightarrow$ `create_estado`
*   **Body Requerido (`StatusCreate`):**
    ```json
    {
      "nombre_estado": "Activo"
    }
    ```
*   **Response Esperada (Status 201 - `StatusResponse`):**
    ```json
    {
      "id_estado": 1,
      "nombre_estado": "Activo"
    }
    ```

#### **`POST`** `/metricas/`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `create_metric`
*   **Body Requerido (`MetricaCreate`):**
    ```json
    {
      "valor": 95.5,
      "id_monitoreo": 1,
      "id_tipo_metrica": 1
    }
    ```
*   **Response Esperada (Status 201 - `MetricaResponse`):**
    ```json
    {
      "id_metrica": 1,
      "valor": 95.5,
      "id_monitoreo": 1,
      "id_tipo_metrica": 1,
      "fecha_registro": "2026-05-22T18:00:00Z"
    }
    ```

#### **`POST`** `/monitoreo/`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `create_monitoring_session`
*   **Body Requerido (`MonitoreoCreate`):**
    ```json
    {
      "id_servidor": 1,
      "id_estado_monitoreo": 3
    }
    ```
*   **Response Esperada (Status 201 - `MonitoreoResponse`):**
    ```json
    {
      "id_monitoreo": 1,
      "id_servidor": 1,
      "id_estado_monitoreo": 3,
      "fecha_inicio": "2026-05-22T18:00:00Z",
      "fecha_fin": null,
      "metricas": []
    }
    ```

#### **`PUT`** `/monitoreo/{monitoreo_id}/close`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `close_monitoring_session`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `MonitoreoResponse`):**
    ```json
    {
      "id_monitoreo": 1,
      "id_servidor": 1,
      "id_estado_monitoreo": 4,
      "fecha_inicio": "2026-05-22T18:00:00Z",
      "fecha_fin": "2026-05-22T18:05:00Z",
      "metricas": []
    }
    ```

#### **`POST`** `/nivel-alerta/`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `create_alert_level`
*   **Body Requerido (`NivelAlertaCreate`):**
    ```json
    {
      "nombre_nivel": "Crítico"
    }
    ```
*   **Response Esperada (Status 201 - `NivelAlertaResponse`):**
    ```json
    {
      "id_nivel_alerta": 1,
      "nombre_nivel": "Crítico"
    }
    ```

#### **`POST`** `/criticidad/`
*   **Servicio Ejecutor:** [`app/services/catalogs/status_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/status_crud.py) $\rightarrow$ `create_criticidad`
*   **Body Requerido (`NivelCriticidadCreate`):**
    ```json
    {
      "nombre_criticidad": "Alta",
      "descripcion": "Servidores core de negocio"
    }
    ```
*   **Response Esperada (Status 201 - `NivelCriticidadResponse`):**
    ```json
    {
      "id_nivel_criticidad": 1,
      "nombre_criticidad": "Alta",
      "descripcion": "Servidores core de negocio"
    }
    ```

#### **`POST`** `/tipo-acceso/`
*   **Servicio Ejecutor:** [`app/services/catalogs/status_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/status_crud.py) $\rightarrow$ `create_tipo_acceso`
*   **Body Requerido (`TipoAccesoCreate`):**
    ```json
    {
      "nombre_tipo": "SSH"
    }
    ```
*   **Response Esperada (Status 201 - `TipoAccesoResponse`):**
    ```json
    {
      "id_tipo_acceso": 1,
      "nombre_tipo": "SSH"
    }
    ```

#### **`POST`** `/tipo-metrica/`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `create_metric_type`
*   **Body Requerido (`TipoMetricaCreate`):**
    ```json
    {
      "nombre_tipo": "CPU_USAGE",
      "unidad_medida": "%"
    }
    ```
*   **Response Esperada (Status 201 - `TipoMetricaResponse`):**
    ```json
    {
      "id_tipo_metrica": 1,
      "nombre_tipo": "CPU_USAGE",
      "unidad_medida": "%"
    }
    ```

#### **`GET`** `/alertas/active`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `get_active_alerts`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[AlertaResponse]`):**
    ```json
    [
      {
        "id_alerta": 1,
        "descripcion": "El uso del disco superó el umbral crítico del 90%",
        "id_servidor": 1,
        "id_monitoreo": 1,
        "id_nivel_alerta": 3,
        "id_estado_alerta": 1,
        "fecha_alerta": "2026-05-22T18:00:00Z"
      }
    ]
    ```

#### **`GET`** `/alertas/summary`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `get_alerts_summary`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "Crítico": 5,
      "Advertencia": 12
    }
    ```

#### **`GET`** `/alertas/today`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `get_alerts_today`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[AlertaResponse]`):**
    ```json
    [
      {
        "id_alerta": 1,
        "descripcion": "El uso del disco superó el umbral crítico del 90%",
        "id_servidor": 1,
        "id_monitoreo": null,
        "id_nivel_alerta": 3,
        "id_estado_alerta": 1,
        "fecha_alerta": "2026-05-22T18:00:00Z"
      }
    ]
    ```

#### **`GET`** `/alertas/recent`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `get_recent_alerts`
*   **Query Params:** `limit` (Por defecto 50)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[AlertaResponse]`):**
    ```json
    [
      {
        "id_alerta": 1,
        "descripcion": "El uso del disco superó el umbral crítico del 90%",
        "id_servidor": 1,
        "id_monitoreo": null,
        "id_nivel_alerta": 3,
        "id_estado_alerta": 1,
        "fecha_alerta": "2026-05-22T18:00:00Z"
      }
    ]
    ```

#### **`GET`** `/alertas/servidor/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `get_alerts_by_server`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[AlertaResponse]`):**
    ```json
    [
      {
        "id_alerta": 1,
        "descripcion": "El uso del disco superó el umbral crítico del 90%",
        "id_servidor": 1,
        "id_monitoreo": null,
        "id_nivel_alerta": 3,
        "id_estado_alerta": 1,
        "fecha_alerta": "2026-05-22T18:00:00Z"
      }
    ]
    ```

#### **`GET`** `/estados/`
*   **Servicio Ejecutor:** [`app/services/catalogs/status_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/status_crud.py) $\rightarrow$ `get_estados`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[StatusResponse]`):**
    ```json
    [
      {
        "id_estado": 1,
        "nombre_estado": "Activo"
      },
      {
        "id_estado": 2,
        "nombre_estado": "Inactivo"
      }
    ]
    ```

#### **`DELETE`** `/estados/{status_id}`
*   **Servicio Ejecutor:** [`app/services/catalogs/status_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/status_crud.py) $\rightarrow$ `delete_estado`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/monitoreo/{monitoreo_id}`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `get_monitoring_session`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `MonitoreoResponse`):**
    ```json
    {
      "id_monitoreo": 1,
      "id_servidor": 1,
      "id_estado_monitoreo": 4,
      "fecha_inicio": "2026-05-22T18:00:00Z",
      "fecha_fin": "2026-05-22T18:05:00Z",
      "metricas": [
        {
          "id_metrica": 1,
          "valor": 95.5,
          "id_monitoreo": 1,
          "id_tipo_metrica": 1,
          "fecha_registro": "2026-05-22T18:00:05Z"
        }
      ]
    }
    ```

#### **`GET`** `/nivel-alerta/`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `get_alert_levels`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[NivelAlertaResponse]`):**
    ```json
    [
      {
        "id_nivel_alerta": 1,
        "nombre_nivel": "Crítico"
      },
      {
        "id_nivel_alerta": 2,
        "nombre_nivel": "Advertencia"
      }
    ]
    ```

#### **`DELETE`** `/nivel-alerta/{nivel_id}`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `delete_alert_level`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/criticidad/`
*   **Servicio Ejecutor:** [`app/services/catalogs/status_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/status_crud.py) $\rightarrow$ `get_criticidades`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[NivelCriticidadResponse]`):**
    ```json
    [
      {
        "id_nivel_criticidad": 1,
        "nombre_criticidad": "Baja",
        "descripcion": "Servidores de desarrollo o pruebas"
      },
      {
        "id_nivel_criticidad": 2,
        "nombre_criticidad": "Media",
        "descripcion": "Servidores de staging o QA"
      },
      {
        "id_nivel_criticidad": 3,
        "nombre_criticidad": "Alta",
        "descripcion": "Servidores productivos críticos"
      }
    ]
    ```

#### **`DELETE`** `/criticidad/{nivel_id}`
*   **Servicio Ejecutor:** [`app/services/catalogs/status_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/status_crud.py) $\rightarrow$ `delete_criticidad`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/tipo-acceso/`
*   **Servicio Ejecutor:** [`app/services/catalogs/status_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/status_crud.py) $\rightarrow$ `get_tipos_acceso`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[TipoAccesoResponse]`):**
    ```json
    [
      {
        "id_tipo_acceso": 1,
        "nombre_tipo": "SSH"
      },
      {
        "id_tipo_acceso": 2,
        "nombre_tipo": "Database Native"
      }
    ]
    ```

#### **`DELETE`** `/tipo-acceso/{tipo_id}`
*   **Servicio Ejecutor:** [`app/services/catalogs/status_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/status_crud.py) $\rightarrow$ `delete_tipo_acceso`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

#### **`GET`** `/tipo-metrica/`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `get_metric_types`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[TipoMetricaResponse]`):**
    ```json
    [
      {
        "id_tipo_metrica": 1,
        "nombre_tipo": "CPU_USAGE",
        "unidad_medida": "%"
      },
      {
        "id_tipo_metrica": 2,
        "nombre_tipo": "RAM_USAGE",
        "unidad_medida": "%"
      }
    ]
    ```

#### **`DELETE`** `/tipo-metrica/{tipo_id}`
*   **Servicio Ejecutor:** [`app/services/catalogs/monitoring_persistence_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/catalogs/monitoring_persistence_crud.py) $\rightarrow$ `delete_metric_type`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

---

### 📋 Auditoría

#### **`POST`** `/audit-types/`
*   **Servicio Ejecutor:** [`app/services/audit/audit_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/audit/audit_crud.py) $\rightarrow$ `create_tipo_evento`
*   **Body Requerido (`TipoEventoCreate`):**
    ```json
    {
      "nombre_evento": "Creación"
    }
    ```
*   **Response Esperada (Status 201 - `TipoEventoResponse`):**
    ```json
    {
      "id_tipo_evento": 1,
      "nombre_evento": "Creación"
    }
    ```

#### **`GET`** `/audit-logs/`
*   **Servicio Ejecutor:** [`app/services/audit/audit_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/audit/audit_crud.py) $\rightarrow$ `get_bitacoras`
*   **Query Params:** `skip` (Por defecto 0), `limit` (Por defecto 100)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[BitacoraResponse]`):**
    ```json
    [
      {
        "id_bitacora": 1,
        "entidad_afectada": "Servidor",
        "id_entidad": 1,
        "descripcion_evento": "Se registró el servidor Svr-Linux-01",
        "id_usuario": 1,
        "id_tipo_evento": 1,
        "fecha_evento": "2026-05-22T18:00:00Z"
      }
    ]
    ```

#### **`GET`** `/audit-logs/{bitacora_id}`
*   **Servicio Ejecutor:** [`app/services/audit/audit_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/audit/audit_crud.py) $\rightarrow$ `get_bitacora_by_id`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `BitacoraResponse`):**
    ```json
    {
      "id_bitacora": 1,
      "entidad_afectada": "Servidor",
      "id_entidad": 1,
      "descripcion_evento": "Se registró el servidor Svr-Linux-01",
      "id_usuario": 1,
      "id_tipo_evento": 1,
      "fecha_evento": "2026-05-22T18:00:00Z"
    }
    ```

#### **`GET`** `/audit-types/`
*   **Servicio Ejecutor:** [`app/services/audit/audit_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/audit/audit_crud.py) $\rightarrow$ `get_tipo_eventos`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[TipoEventoResponse]`):**
    ```json
    [
      {
        "id_tipo_evento": 1,
        "nombre_evento": "Creación"
      },
      {
        "id_tipo_evento": 2,
        "nombre_evento": "Modificación"
      }
    ]
    ```

#### **`DELETE`** `/audit-types/{tipo_id}`
*   **Servicio Ejecutor:** [`app/services/audit/audit_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/audit/audit_crud.py) $\rightarrow$ `delete_tipo_evento`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 204):** *Sin contenido*

---

## 📈 Módulo 1: Observabilidad & Monitoreo Operativo
Endpoints para consulta de salud, estadísticas en tiempo real y ejecución de tareas de monitoreo del Scheduler. El prefijo global de estos endpoints es `/sgir/v1/m1`.

### 🫀 Chequeos de Salud (Health Checks)

#### **`GET`** `/health/postgres`
*   **Servicio Ejecutor:** [`app/routes/healths/health_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/healths/health_routes.py) $\rightarrow$ `health_postgres` (Ejecuta un SELECT básico en caliente)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "ok",
      "db": "PostgreSQL",
      "result": 2
    }
    ```

#### **`POST`** `/health/ping`
*   **Servicio Ejecutor:** [`app/routes/healths/health_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/healths/health_routes.py) $\rightarrow$ `ping_host` (Dispara un ping rápido usando `icmplib` sockets UDP)
*   **Body Requerido (`PingRequest`):**
    ```json
    {
      "ip": "192.168.1.1"
    }
    ```
*   **Response Esperada (Status 200):** `true` si el host es alcanzable, `false` de lo contrario.

---

### 🖥️ Monitoreo de Host (SSH)

#### **`GET`** `/host/scheduler/status`
*   **Servicio Ejecutor:** [`app/core/scheduler_manager.py`](file:///home/angel/src/titulacion/sgir_backend/app/core/scheduler_manager.py) $\rightarrow$ `get_scheduler_status`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "running"
    }
    ```

#### **`POST`** `/host/scheduler/pause`
*   **Servicio Ejecutor:** [`app/core/scheduler_manager.py`](file:///home/angel/src/titulacion/sgir_backend/app/core/scheduler_manager.py) $\rightarrow$ `pause_scheduler` (Solo Administrador)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "message": "Monitoreo pausado exitosamente",
      "status": "paused"
    }
    ```

#### **`POST`** `/host/scheduler/resume`
*   **Servicio Ejecutor:** [`app/core/scheduler_manager.py`](file:///home/angel/src/titulacion/sgir_backend/app/core/scheduler_manager.py) $\rightarrow$ `resume_scheduler` (Solo Administrador)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "message": "Monitoreo reanudado exitosamente",
      "status": "running"
    }
    ```

#### **`GET`** `/host/global-summary`
*   **Servicio Ejecutor:** [`app/services/monitoring/ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py) $\rightarrow$ `get_global_health_summary`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "sanos": 5,
      "criticos": 2,
      "desactualizados": 1,
      "total": 8
    }
    ```

#### **`GET`** `/host/live-cache`
*   **Servicio Ejecutor:** Caché global en memoria en [`app/services/monitoring/ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py) $\rightarrow$ `LIVE_METRICS_CACHE`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "192.168.1.100": {
        "cpu_usage": 45.2,
        "ram_usage": 67.8,
        "disk_usage": 82.1,
        "uptime": "12 days",
        "last_update": "2026-05-22T18:00:00Z"
      }
    }
    ```

#### **`GET`** `/host/health-status/{server_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py) $\rightarrow$ `get_server_health_status`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "servidor_id": 1,
      "ip": "192.168.1.100",
      "estado": "healthy",
      "alertas_activas": 0,
      "metricas": {
        "cpu": 45.2,
        "ram": 67.8,
        "disk": 82.1
      }
    }
    ```

#### **`POST`** `/host/discover-filesystems/{servidor_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py) $\rightarrow$ `run_filesystem_discovery` (Ejecuta un escaneo en caliente vía SSH)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "servidor_id": 1,
      "ip": "192.168.1.100",
      "particiones_detectadas": [
        {
          "punto_montaje": "/",
          "tamano_total_gb": 50.0,
          "tamano_usado_gb": 12.3
        },
        {
          "punto_montaje": "/data",
          "tamano_total_gb": 500.0,
          "tamano_usado_gb": 320.5
        }
      ]
    }
    ```

#### **`GET`** `/host/{server_id}/{cred_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py) $\rightarrow$ `run_ssh_monitoring` (Monitoreo ad-hoc instantáneo)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "monitoreo_id": 45,
      "servidor_id": 1,
      "status": "success",
      "metrics": {
        "cpu_usage": 15.5,
        "ram_usage": 45.2,
        "disk_usage": 32.1,
        "uptime": "24 days"
      }
    }
    ```

---

### 🛢️ Monitoreo de Bases de Datos (DB Agents)

#### **`GET`** `/db/live-cache`
*   **Servicio Ejecutor:** Caché global consolidada en [`app/services/monitoring/db_unified_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/db_unified_service.py) $\rightarrow$ `LIVE_DB_CACHE`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "sgir_mysql8_3_performance_schema": "online|1078652|3|151|1.99|1|2412|0.00|0|0|0|0|0|99.85|2026-05-22T17:59:52Z",
      "sgir_mongodb_5_None": {
        "engine": "MongoDB",
        "metrics": {
          "ping": 1,
          "capacity_pct": 0.0,
          "stuck_processes": 0,
          "specific_value": 1.0
        },
        "last_update": "2026-05-22T17:56:00Z"
      }
    }
    ```

#### **`GET`** `/db/health-status/{instancia_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/db_unified_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/db_unified_service.py) $\rightarrow$ `get_db_health_status`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "instancia_id": 3,
      "nombre_instancia": "sgir_mysql8",
      "engine": "MySQL",
      "ping": 1,
      "status": "healthy",
      "capacidad": "0%",
      "procesos_atorados": 0,
      "valor_especifico": 151.0,
      "origen": "cache",
      "ultima_actualizacion": "2026-05-22T17:59:52Z"
    }
    ```

#### **`POST`** `/db/run-adhoc/{instancia_id}/{credencial_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/db_unified_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/db_unified_service.py) $\rightarrow$ `run_unified_db_monitoring` (Fuerza recolección directa)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "instancia_id": 3,
      "engine": "MySQL",
      "metrics": {
        "ping": 1,
        "capacity_pct": 0.0,
        "stuck_processes": 0,
        "specific_value": 151.0
      },
      "last_update": "2026-05-22T17:59:52Z"
    }
    ```

#### **`GET`** `/mongodb/{servidor_id}/{credencial_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/mongodb/mongodb_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/mongodb/mongodb_service.py) $\rightarrow$ `get_mongodb_metrics`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `MongoDBMetrics`):**
    ```json
    {
      "status": "online",
      "uptime": 259200,
      "connections_current": 5,
      "connections_available": 100,
      "connections_total_created": 35,
      "op_inserts": 120,
      "op_queries": 450,
      "op_updates": 32,
      "op_deletes": 12,
      "mem_resident_mb": 45,
      "mem_virtual_mb": 120,
      "ok": 1.0
    }
    ```

#### **`GET`** `/mysql5/{servidor_id}/{credencial_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/mysql5/mysql5_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/mysql5/mysql5_service.py) $\rightarrow$ `get_mysql5_metrics`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `MySQL5Metrics`):**
    ```json
    {
      "status": "online",
      "uptime": 1078652,
      "threads_connected": 3,
      "threads_running": 1,
      "max_connections": 151,
      "questions": 2412,
      "queries_per_second": 1.99,
      "slow_queries": 0,
      "table_locks_waited": 0,
      "innodb_row_lock_waits": 0,
      "connection_usage_percent": 1.99
    }
    ```

#### **`GET`** `/mysql8/{servidor_id}/{credencial_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/mysql8/mysql8_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/mysql8/mysql8_service.py) $\rightarrow$ `get_mysql8_metrics`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `MySQL8Metrics`):**
    ```json
    {
      "status": "online",
      "uptime": 1078652,
      "threads_connected": 3,
      "threads_running": 1,
      "max_connections": 151,
      "questions": 2412,
      "queries_per_second": 1.99,
      "slow_queries": 0,
      "table_locks_waited": 0,
      "innodb_row_lock_waits": 0,
      "connection_usage_percent": 1.99
    }
    ```

#### **`GET`** `/oracle/{id_instancia}/{id_credencial}`
*   **Servicio Ejecutor:** [`app/services/monitoring/oracle/oracle_monitoring_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/oracle/oracle_monitoring_service.py) $\rightarrow$ `run_oracle_modular_monitoring`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `OracleMonitoringResponse`):**
    ```json
    {
      "id_instancia": 1,
      "id_servidor": 1,
      "nivel_criticidad": "Alta",
      "timestamp": "2026-05-22T18:00:00Z",
      "grupo_a": {
        "status": "online",
        "active_connections": 12,
        "max_connections": 150,
        "total_databases": 3
      },
      "grupo_b": {
        "threads_count": 45,
        "memory_usage_mb": 1420.50,
        "memory_max_mb": 4096.00,
        "active_locks": 0
      },
      "grupo_c": {
        "slow_queries_count": 0,
        "avg_response_time_ms": 12.50,
        "cpu_usage_percent": 4.50
      }
    }
    ```

#### **`GET`** `/mysql5/metrics/{id_instancia}`
*   **Servicio Ejecutor:** [`app/services/monitoring/mysql5/mysql5_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/mysql5/mysql5_service.py) $\rightarrow$ `get_mysql5_metrics` (Busca credenciales nativas del servidor en CMDB)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `MySQL5Metrics`):**
    ```json
    {
      "status": "online",
      "uptime": 1078652,
      "threads_connected": 3,
      "threads_running": 1,
      "max_connections": 151,
      "questions": 2412,
      "queries_per_second": 1.99,
      "slow_queries": 0,
      "table_locks_waited": 0,
      "innodb_row_lock_waits": 0,
      "connection_usage_percent": 1.99
    }
    ```

#### **`GET`** `/mysql5/modular/{id_instancia}/{id_credencial}`
*   **Servicio Ejecutor:** [`app/services/monitoring/mysql5/mysql5_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/mysql5/mysql5_service.py) $\rightarrow$ `run_mysql5_modular_monitoring` (Segmentado según la criticidad)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `MySQLModularMonitoringResponse`):**
    ```json
    {
      "id_instancia": 1,
      "id_servidor": 1,
      "nivel_criticidad": "Alta",
      "timestamp": "2026-05-22T18:00:00Z",
      "grupo_a": {
        "status": "online",
        "uptime": 1078652,
        "threads_connected": 3,
        "max_connections": 151,
        "connection_usage_percent": 1.99
      },
      "grupo_b": {
        "threads_running": 1,
        "questions": 2412,
        "queries_per_second": 1.99,
        "slow_queries": 0,
        "table_locks_waited": 0
      },
      "grupo_c": {
        "innodb_row_lock_waits": 0,
        "innodb_row_lock_time_avg": 0,
        "innodb_buffer_pool_pages_dirty": 0,
        "innodb_buffer_pool_read_requests": 152000,
        "innodb_buffer_pool_reads": 230,
        "innodb_buffer_pool_hit_ratio": 99.85
      }
    }
    ```

#### **`GET`** `/mysql8/modular/{id_instancia}/{id_credencial}`
*   **Servicio Ejecutor:** [`app/services/monitoring/mysql8/mysql8_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/mysql8/mysql8_service.py) $\rightarrow$ `run_mysql8_modular_monitoring`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `MySQLModularMonitoringResponse`):**
    ```json
    {
      "id_instancia": 1,
      "id_servidor": 1,
      "nivel_criticidad": "Alta",
      "timestamp": "2026-05-22T18:00:00Z",
      "grupo_a": {
        "status": "online",
        "uptime": 1078652,
        "threads_connected": 3,
        "max_connections": 151,
        "connection_usage_percent": 1.99
      },
      "grupo_b": {
        "threads_running": 1,
        "questions": 2412,
        "queries_per_second": 1.99,
        "slow_queries": 0,
        "table_locks_waited": 0
      },
      "grupo_c": {
        "innodb_row_lock_waits": 0,
        "innodb_row_lock_time_avg": 0,
        "innodb_buffer_pool_pages_dirty": 0,
        "innodb_buffer_pool_read_requests": 152000,
        "innodb_buffer_pool_reads": 230,
        "innodb_buffer_pool_hit_ratio": 99.85
      }
    }
    ```

#### **`GET`** `/mongodb/modular/{id_instancia}/{id_credencial}`
*   **Servicio Ejecutor:** [`app/services/monitoring/mongodb/mongodb_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/mongodb/mongodb_service.py) $\rightarrow$ `run_mongodb_modular_monitoring`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `MongoModularMonitoringResponse`):**
    ```json
    {
      "id_instancia": 1,
      "id_servidor": 1,
      "nivel_criticidad": "Alta",
      "timestamp": "2026-05-22T18:00:00Z",
      "grupo_a": {
        "status": "online",
        "uptime": 259200,
        "ok": 1.0
      },
      "grupo_b": {
        "connections_current": 5,
        "connections_available": 100,
        "connections_total_created": 35,
        "mem_resident_mb": 45,
        "mem_virtual_mb": 120
      },
      "grupo_c": {
        "op_inserts": 120,
        "op_queries": 450,
        "op_updates": 32,
        "op_deletes": 12
      }
    }
    ```

---

## 🔍 Módulo 2: Auto-Descubrimiento & CMDB
Endpoints enfocados en la extracción automatizada y sincronización del inventario de infraestructura. El prefijo global de estos endpoints es `/sgir/v1/m2`.

#### **`GET`** `/m2/host/discover-cron/{servidor_id}/{credencial_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py) $\rightarrow$ `run_cron_discovery` (Escanea `/etc/crontab` y crontabs locales)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "servidor_id": 1,
      "tareas_encontradas": [
        {
          "cron_expr": "0 2 * * *",
          "comando": "/usr/local/bin/backup.sh",
          "sugerencia_politica": "Semanal/Diario"
        }
      ]
    }
    ```

#### **`GET`** `/m2/inventory/assets`
*   **Servicio Ejecutor:** [`app/services/infrastructure/infrastructure_crud.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/infrastructure_crud.py) $\rightarrow$ `get_global_inventory`
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[GlobalAssetResponse]`):**
    ```json
    [
      {
        "ip": "192.168.1.100",
        "motor": "MySQL 8.x",
        "instancia": "mysql_prod_01",
        "servidor": "Svr-Linux-01",
        "criticidad": "Alta",
        "bases_de_datos": [
          {
            "nombre": "sgir_catalog",
            "tamano_mb": 120.50,
            "estado": "Activo"
          }
        ]
      }
    ]
    ```

#### **`GET`** `/assets/pdf`
*   **Servicio Ejecutor:** [`app/services/reports/pdf_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/reports/pdf_service.py) $\rightarrow$ `generate_db_inventory_pdf` (invocado por `get_assets_pdf` en `app/routes/__init__.py`)
*   **Comportamiento Operativo:** Ejecuta una sincronización en tiempo real de toda la infraestructura activa (`run_bulk_inventory_sync`), extrae las bases de datos activas de la CMDB ordenadas por motor de BD, e inyecta los datos en la plantilla HTML A4 (con logotipos y favicons locales de la DTIC UAEMex) para generar y retornar los bytes del reporte PDF mediante WeasyPrint.
*   **Body Requerido:** *Sin Body (Público, sin autenticación)*
*   **Response Esperada (Status 200 - application/pdf):** Flujo binario de archivo PDF con descarga adjunta (`reporte_inventario_dbs.pdf`).

#### **`GET`** `/assets/csv`
*   **Servicio Ejecutor:** `app/routes/__init__.py` $\rightarrow$ `get_assets_csv`
*   **Comportamiento Operativo:** Ejecuta una sincronización en tiempo real de toda la infraestructura activa (`run_bulk_inventory_sync`), extrae las bases de datos activas de la CMDB ordenadas por motor de BD, y construye e inyecta la información en un búfer de texto en memoria codificado en formato CSV (`utf-8-sig`) para compatibilidad directa con Microsoft Excel.
*   **Body Requerido:** *Sin Body (Público, sin autenticación)*
*   **Response Esperada (Status 200 - text/csv):** Flujo binario de archivo CSV con descarga adjunta (`reporte_inventario_dbs.csv`).

#### **`POST`** `/m2/inventory/discover-all`
*   **Servicio Ejecutor:** [`app/services/infrastructure/inventory_sync_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/inventory_sync_service.py) $\rightarrow$ `run_bulk_inventory_sync` (Auto-descubrimiento paralelo en todas las instancias)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "success",
      "instancias_procesadas": 5,
      "total_dbs_sincronizadas": 18,
      "detalles": []
    }
    ```

#### **`POST`** `/m2/inventory/discover/{instancia_id}/{credencial_id}`
*   **Servicio Ejecutor:** [`app/services/infrastructure/inventory_sync_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/infrastructure/inventory_sync_service.py) $\rightarrow$ `sync_databases_inventory` (Sincroniza bases de datos de una instancia particular en CMDB)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "status": "success",
      "instancia_id": 1,
      "dbs_detectadas": ["db_audit", "db_billing"],
      "dbs_sincronizadas": 2
    }
    ```

#### **`GET`** `/m2/inventory/summary/{servidor_id}`
*   **Servicio Ejecutor:** [`app/routes/monitoring/inventory_discovery_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/monitoring/inventory_discovery_routes.py) $\rightarrow$ `get_server_storage_summary` (Agrega almacenamiento)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "servidor_id": 1,
      "total_databases": 3,
      "total_size_mb": 540.50
    }
    ```

---

## 💾 Módulo 3: Automatización de Respaldos (Operativo)
Endpoints para interactuar con la gestión, retención y escaneo remoto de backups. El prefijo global de estos endpoints es `/sgir/v1/m3`.

#### **`POST`** `/m3/host/scheduler/trigger-backup-retention`
*   **Servicio Ejecutor:** [`app/services/monitoring/scheduler_tasks.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/scheduler_tasks.py) $\rightarrow$ `backup_retention_task` (Limpia ejecuciones expiradas)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "message": "Política de retención de respaldos ejecutada exitosamente"
    }
    ```

#### **`POST`** `/m3/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py) $\rightarrow$ `run_integrated_file_discovery` (Escanea archivos de respaldos físicos y los registra en la base relacional)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200):**
    ```json
    {
      "instancia_id": 1,
      "ruta_escaneada": "/mnt/backups/mysql",
      "archivos_procesados": 4,
      "nuevos_respaldos_registrados": 2,
      "detalles": [
        {
          "base_datos_id": 1,
          "nombre_base": "sgir_catalog",
          "politica_nombre": "Semanal Retención 15d",
          "ruta_path": "/mnt/backups/mysql/sgir_catalog_2026-05-22.sql",
          "archivo_encontrado": true,
          "tamano_encontrado_mb": 420.50
        }
      ]
    }
    ```

#### **`POST`** `/m3/inventory/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}`
*   **Servicio Ejecutor:** [`app/services/monitoring/ssh_service.py`](file:///home/angel/src/titulacion/sgir_backend/app/services/monitoring/ssh_service.py) $\rightarrow$ `run_server_integrated_file_discovery` (Escanea backups de todas las instancias del servidor)
*   **Body Requerido:** *Sin Body*
*   **Response Esperada (Status 200 - `List[BackupDiscoveryResult]`):**
    ```json
    [
      {
        "base_datos_id": 1,
        "nombre_base": "sgir_catalog",
        "politica_nombre": "Semanal Retención 15d",
        "ruta_path": "/mnt/backups/mysql/sgir_catalog_2026-05-22.sql",
        "archivo_encontrado": true,
        "tamano_encontrado_mb": 420.50,
        "timestamp_verificacion": "2026-05-22T18:00:00Z",
        "detalle": "Respaldo verificado con éxito"
      }
    ]
    ```
