# Guía de Formato: Carga Masiva de Bases de Datos

Esta guía explica detalladamente la estructura, columnas, tipos de datos y reglas de negocio necesarias para construir correctamente el archivo `03_bases_de_datos_import.csv` para la carga masiva en **SGIR**.

---

## 📋 Estructura de Columnas (Headers)

El archivo CSV debe contener exactamente las siguientes columnas en su primera línea (cabecera):

| # | Nombre de Columna | ¿Obligatorio? | Tipo de Dato / Catálogo | Descripción y Reglas de Negocio |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `direccion_ip` | **Sí** | IPv4 / IPv6 | Dirección IP única del servidor que aloja la base de datos. |
| **2** | `puerto_db` | **Sí** | Entero | Puerto de red en el que escucha la instancia de DBMS (ej: `3306`, `1521`). |
| **3** | `nombre_instancia`| **Sí** | Texto (máx 100) | Nombre de la instancia de base de datos a la que pertenece (ej: `instancia_prod`). |
| **4** | `nombre_base` | **Sí** | Texto (máx 150) | Nombre lógico de la base de datos o esquema (ej: `ventas_db`). |
| **5** | `tamano_mb` | No | Decimal | Tamaño físico actual estimado en megabytes (ej: `1024.50`). |
| **6** | `estado` | No | Catálogo Estado | Estado de la base de datos: `Activo`, `Inactivo` (por defecto `Activo`). |

---

## 💡 Reglas de Negocio Clave

### 1. Dependencia de Instancia DBMS (Llave Foránea Compuesta)
Para registrar exitosamente una base de datos lógica, el backend necesita mapear y vincular el registro a su **Instancia DBMS** correspondiente. Esto se hace mediante tres campos relacionales cruzados en el CSV:
1.  `direccion_ip`
2.  `puerto_db`
3.  `nombre_instancia`

El importador buscará automáticamente en la CMDB la instancia que cumpla exactamente con estas tres condiciones para obtener la llave foránea `id_instancia`. Si la instancia no está previamente registrada (en el Paso 1), la fila del CSV será rechazada con un error.

### 2. Control de Duplicidad
El sistema verifica la unicidad de las bases de datos mediante la combinación **`id_instancia` + `nombre_base`**.
*   Puedes tener bases de datos con el mismo nombre (ej: `test_db`) en diferentes instancias o servidores.
*   Si intentas importar el mismo nombre de base de datos para la misma instancia dos veces, el importador la omitirá automáticamente para proteger los históricos de auditoría y evitar redundancia.

---

## 📝 Ejemplo Práctico de CSV

Copia este ejemplo para poblar tu archivo `03_bases_de_datos_import.csv`:

```csv
direccion_ip,puerto_db,nombre_instancia,nombre_base,tamano_mb,estado
192.168.12.10,3306,instancia_prod,ventas_db,1024.50,Activo
192.168.12.10,3306,instancia_prod,clientes_db,512.00,Activo
192.168.12.20,1521,ORCL,ERP_PROD,20480.00,Activo
```
