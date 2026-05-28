# Guía de Formato: Carga Masiva de Rutas de Respaldo

Esta guía explica detalladamente la estructura, columnas, tipos de datos y reglas de negocio necesarias para construir correctamente el archivo `02_rutas_import.csv` para la carga masiva en **SGIR**.

---

## 📋 Estructura de Columnas (Headers)

El archivo CSV debe contener exactamente las siguientes columnas en su primera línea (cabecera):

| # | Nombre de Columna | ¿Obligatorio? | Tipo de Dato / Catálogo | Descripción y Reglas de Negocio |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `direccion_ip` | **Sí** | IPv4 / IPv6 | IP del servidor físico al que pertenece la ruta. **Debe existir previamente en la CMDB**. |
| **2** | `descripcion_ruta` | No | Texto (máx 150) | Nombre descriptivo o etiqueta de la ruta (ej: `Respaldo Diario MySQL`). |
| **3** | `path` | **Sí** | Ruta absoluta (Text) | Directorio del sistema de archivos donde se almacenan físicamente los backups (ej: `/data/respaldos`). |
| **4** | `tipo_almacenamiento`| **Sí** | Catálogo Almacenamiento | Debe coincidir con: `Local`, `NAS`, `S3`, `SCP`. |
| **5** | `estado` | No | Catálogo Estado | Estado de la ruta: `Activo`, `Inactivo` (por defecto `Activo`). |

---

## 💡 Reglas de Negocio Clave

### 1. Dependencia de Servidor (`direccion_ip`)
Para que una ruta de respaldo se cargue de manera exitosa, el servidor al que está asociada debe haber sido importado previamente (en el Paso 1: `01_servidores_import.csv`). El backend realiza una búsqueda automática en la CMDB mediante la `direccion_ip` provista para obtener la llave foránea `id_servidor`. Si la IP no existe, la fila será rechazada.

### 2. Evitar Rutas Duplicadas
El backend valida la unicidad de las rutas combinando **`id_servidor` + `path`**. 
*   Puedes tener el mismo `path` (ej: `/var/backup`) en diferentes servidores sin problema.
*   Si intentas importar exactamente el mismo `path` para el mismo servidor dos veces, el importador omitirá silenciosamente el registro duplicado para proteger la base de datos de datos redundantes.

### 3. Catálogo de Almacenamiento
Asegúrate de escribir correctamente los valores de `tipo_almacenamiento` (sin importar mayúsculas), ya que el importador hace un matching contra el catálogo base de almacenamiento. Valores comunes pre-configurados:
*   `Local` (ej: directorios en el propio disco duro).
*   `NAS` / `SAN` (ej: puntos de montaje de red compartidos).
*   `S3` (ej: almacenamiento en la nube).

---

## 📝 Ejemplo Práctico de CSV

Copia este ejemplo para poblar tu archivo `02_rutas_import.csv`:

```csv
direccion_ip,descripcion_ruta,path,tipo_almacenamiento,estado
192.168.12.10,Respaldo Diario MySQL,/data/respaldos,Local,Activo
192.168.12.20,Respaldo Oracle RMAN,/u01/app/oracle/backups,NAS,Activo
```
