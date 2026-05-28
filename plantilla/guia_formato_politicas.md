# Guía de Formato: Carga Masiva de Políticas de Respaldo

Esta guía explica detalladamente la estructura, columnas, tipos de datos y reglas de negocio necesarias para construir correctamente el archivo `04_politicas_import.csv` para la carga masiva en **SGIR**.

---

## 📋 Estructura de Columnas (Headers)

El archivo CSV debe contener exactamente las siguientes columnas en su primera línea (cabecera):

| # | Nombre de Columna | ¿Obligatorio? | Tipo de Dato / Catálogo | Descripción y Reglas de Negocio |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `nombre_politica` | **Sí** | Texto (máx 100) | Nombre identificativo único de la política (ej: `Politica_Diaria`). |
| **2** | `descripcion` | No | Texto libre | Detalles del alcance o propósito de la política. |
| **3** | `expression_cron` | No | Expresión Cron (máx 100) | Sintaxis estándar crontab de planificación (ej: `0 2 * * *` para las 2:00 AM). |
| **4** | `hora_ejecuccion` | No | Hora (`HH:MM:SS` / `HH:MM`) | Hora específica de ejecución de la política (ej: `02:00:00`). |
| **5** | `dias_semana` | No | Texto (máx 50) | Días en los que se debe ejecutar (ej: `Lunes-Domingo`). |
| **6** | `frecuencia_horas` | **Sí** | Entero (mínimo 1) | Periodicidad en horas de la verificación o ejecución de respaldos. |
| **7** | `retencion_dias` | **Sí** | Entero (mínimo 1) | Número de días que el archivo de backup se conservará antes de ser purgado. |
| **8** | `script_path` | No | Ruta de script (máx 512) | Ruta absoluta al script que realiza el backup en el host (ej: `/opt/scripts/backup.sh`). |
| **9** | `tipo_respaldo` | **Sí** | Catálogo Tipo Respaldo | Tipo de copia de seguridad: `Completo`, `Incremental`, `Diferencial`. |
| **10**| `estado` | No | Catálogo Estado | Estado de la política: `Activo`, `Inactivo` (por defecto `Activo`). |

---

## 💡 Reglas de Negocio Clave

### 1. Planificación Flexible (Cron, Hora y Días)
Las políticas de respaldo en **SGIR** soportan planificaciones avanzadas alineadas con crontabs locales de Linux o tareas internas del planificador:
*   Puedes usar `expression_cron` para planificaciones estándar de 5 campos (ej: `0 2 * * *` $\rightarrow$ cada día a las 2:00 AM).
*   Puedes usar `hora_ejecuccion` en formato `HH:MM:SS` (ej: `02:00:00`) o `HH:MM` (ej: `02:00`). El importador convertirá automáticamente este valor a un objeto `time` nativo.
*   Si dejas estos campos vacíos, la política usará exclusivamente la frecuencia base en horas (`frecuencia_horas`) para su orquestación.

### 2. Evitar Políticas Duplicadas
El backend valida la unicidad de las políticas mediante el **`nombre_politica`** (que actúa como llave única). Si el nombre de la política ya está registrado en la base de datos, el importador omitirá el registro para evitar conflictos de planificación.

### 3. Integración con el Catálogo de Respaldos
El campo `tipo_respaldo` debe coincidir exactamente con los strings pre-registrados en tu catálogo base (sin distinguir mayúsculas):
*   `Completo`
*   `Incremental`
*   `Diferencial`

---

## 📝 Ejemplo Práctico de CSV

Copia este ejemplo para poblar tu archivo `04_politicas_import.csv`:

```csv
nombre_politica,descripcion,expression_cron,hora_ejecuccion,dias_semana,frecuencia_horas,retencion_dias,script_path,tipo_respaldo,estado
Politica_Diaria,Respaldo completo diario,0 2 * * *,02:00:00,Lunes-Domingo,24,30,/opt/scripts/backup_diario.sh,Completo,Activo
Politica_Semanal,Respaldo incremental semanal,0 4 * * 0,04:00:00,Domingo,168,90,/opt/scripts/backup_semanal.sh,Incremental,Activo
```
