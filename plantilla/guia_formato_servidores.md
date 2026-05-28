# Guía de Formato: Carga Masiva de Servidores (CMDB)

Esta guía explica detalladamente la estructura, columnas, tipos de datos y reglas de negocio necesarias para construir correctamente el archivo `01_servidores_import.csv` para la carga masiva en **SGIR**.

---

## 📋 Estructura de Columnas (Headers)

El archivo CSV debe contener exactamente las siguientes columnas en su primera línea (cabecera):

| # | Nombre de Columna | ¿Obligatorio? | Tipo de Dato / Catálogo | Descripción y Reglas de Negocio |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `nombre_servidor` | **Sí** | Texto (máx 100) | Nombre identificativo del host (ej: `srv-prod-mysql-01`). |
| **2** | `direccion_ip` | **Sí** | IPv4 / IPv6 | Dirección IP única del servidor. **Actúa como llave de unicidad**. |
| **3** | `es_legacy` | **Sí** | Booleano (`true`/`false`) | `true` si es un sistema legacy (ej: RHEL 4/5, Oracle 10g). |
| **4** | `descripcion` | No | Texto libre | Comentarios o detalles generales del servidor. |
| **5** | `nivel_criticidad`| **Sí** | Catálogo Criticidad | Debe coincidir (sin importar mayúsculas) con: `Bajo`, `Medio`, `Alto`, `Crítico`. |
| **6** | `estado` | No | Catálogo Estado | Estado operativo del activo: `Activo`, `Inactivo` (por defecto `Activo`). |
| **7** | `particiones` | No | Texto (lista separada por comas) | Puntos de montaje a monitorear. Ej: `"/, /u01"` o `"(/, /var)"`. Si está vacío, crea `/`. |
| **8** | `nombre_dbms` | No | Catálogo DBMS | Requerido si deseas asociar base de datos: `MySQL`, `Oracle`, `MongoDB`. |
| **9** | `nombre_instancia`| No | Texto (máx 100) | Nombre lógico de la instancia de DBMS. |
| **10**| `puerto_db` | No | Entero | Puerto de escucha de la base de datos (ej: `3306`, `1521`). |
| **11**| `usuario` | No | Texto (máx 100) | Nombre de usuario de la credencial (SSH o Base de datos). |
| **12**| `password` | No | Texto plano | Contraseña asociada. **El backend la encriptará con AES-256 automáticamente**. |
| **13**| `tipo_acceso` | No | Catálogo Tipo Acceso | Tipo de credencial: `SSH` o `Base de Datos`. |

---

## 💡 Reglas de Negocio Clave

### 1. Reutilización Inteligente de Servidores (Evitar Duplicados)
Si necesitas registrar múltiples credenciales o múltiples instancias de base de datos para la misma dirección IP (un solo servidor físico), **crea múltiples filas en tu CSV compartiendo la misma IP**.
*   **Fila 1:** IP `192.168.1.1` con `usuario` `oracle` de tipo `SSH`. (El importador crea el servidor y la credencial SSH).
*   **Fila 2:** IP `192.168.1.1` con `usuario` `root` de tipo `Base de Datos`. (El importador detecta la IP, reutiliza el servidor anterior y le vincula la credencial de BD MySQL).
*   **Fila 3:** IP `192.168.1.1` con `usuario` `admin_bkp` de tipo `SSH`. (Reutiliza el servidor y le asocia un segundo acceso SSH).

### 2. Formato de las Particiones
El importador procesa listas de directorios físicos de manera flexible. Puedes ingresarlos separados por comas directamente o encerrados entre paréntesis:
*   *Formato Directo:* `"/, /var, /data"`
*   *Formato con Paréntesis:* `"(/, /u01)"`
*   Si dejas el campo vacío o nulo, el sistema registrará de forma predeterminada la partición raíz `/`.

### 3. Seguridad Automática de Contraseñas
Nunca ingreses contraseñas pre-encriptadas en la columna `password`. El backend recibe el texto en claro, lo procesa con una función criptográfica simétrica robusta (`AES-256`) y persiste únicamente el hash seguro en la base de datos.

---

## 📝 Ejemplo Práctico de CSV

Copia este ejemplo para poblar tu archivo `01_servidores_import.csv`:

```csv
nombre_servidor,direccion_ip,es_legacy,descripcion,nivel_criticidad,estado,particiones,nombre_dbms,nombre_instancia,puerto_db,usuario,password,tipo_acceso
srv-mysql-01,192.168.12.10,false,Servidor de Base de Datos MySQL Principal,Medio,Activo,"/, /var, /data",MySQL,instancia_prod,3306,root,MySQLPass123,Base de Datos
srv-oracle-01,192.168.12.20,true,Servidor Oracle Enterprise Legacy,Crítico,Activo,"/, /u01",Oracle,ORCL,1521,oracle,OraclePass123,SSH
```
