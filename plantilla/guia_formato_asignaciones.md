# Guía de Formato: Carga Masiva de Asignaciones de Políticas

Esta guía explica detalladamente la estructura, columnas, tipos de datos y reglas de negocio necesarias para construir correctamente el archivo `05_asignaciones_import.csv` para la carga masiva en **SGIR**.

---

## 📋 Estructura de Columnas (Headers)

El archivo CSV debe contener exactamente las siguientes columnas en su primera línea (cabecera):

| # | Nombre de Columna | ¿Obligatorio? | Tipo de Dato / Catálogo | Descripción y Reglas de Negocio |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `direccion_ip` | **Sí** | IPv4 / IPv6 | Dirección IP única del servidor que aloja la base de datos a asociar. |
| **2** | `puerto_db` | **Sí** | Entero | Puerto de red de la instancia DBMS (ej: `3306`, `1521`). |
| **3** | `nombre_instancia`| **Sí** | Texto (máx 100) | Nombre lógico de la instancia de DBMS. |
| **4** | `nombre_base` | **Sí** | Texto (máx 150) | Nombre de la base de datos/esquema que recibirá la política (ej: `ventas_db`). |
| **5** | `nombre_politica` | **Sí** | Texto (máx 100) | Nombre exacto de la política de respaldo a asignar (ej: `Politica_Diaria`). |

---

## 💡 Reglas de Negocio Clave

### 1. Resolución Dinámica de Llaves Primarias
Esta tabla intermedia relacional (`asignacion_politica_bd` en SQL) no contiene datos descriptivos; sirve únicamente para conectar una base de datos con una política.
*   Para encontrar la base de datos exacta, el importador busca en la CMDB la IP (`direccion_ip`), el puerto (`puerto_db`), el nombre de la instancia (`nombre_instancia`) y el nombre de la base (`nombre_base`) para obtener el `id_base_datos`.
*   Para encontrar la política exacta, busca en la CMDB por el `nombre_politica` para obtener el `id_politica`.

Si alguno de estos dos objetos lógicos no fue importado previamente en las fases anteriores (Paso 3 y Paso 4), el registro será descartado con un error descriptivo indicando la entidad faltante.

### 2. Prevención de Duplicados en la Relación
El backend valida la combinación única de **`id_base_datos` + `id_politica`**.
*   Una base de datos puede estar asociada a múltiples políticas de respaldo diferentes (ej: una política diaria y otra semanal).
*   Sin embargo, si intentas importar la misma asignación de política para la misma base de datos dos veces, el importador omitirá silenciosamente el registro redundante.

---

## 📝 Ejemplo Práctico de CSV

Copia este ejemplo para poblar tu archivo `05_asignaciones_import.csv`:

```csv
direccion_ip,puerto_db,nombre_instancia,nombre_base,nombre_politica
192.168.12.10,3306,instancia_prod,ventas_db,Politica_Diaria
192.168.12.20,1521,ORCL,ERP_PROD,Politica_Semanal
```
