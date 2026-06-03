# 📈 SGIR API - MÓDULO 1: OBSERVABILIDAD Y MONITOREO OPERATIVO

Este módulo agrupa los endpoints destinados a los chequeos de salud (health checks), estadísticas en tiempo real y el monitoreo asíncrono tanto de hardware como de bases de datos. El prefijo global de estos endpoints es `/sgir/v1/m1`.

A continuación se documentan técnicamente los primeros dos endpoints de este módulo:

---

## 1. Chequeo de Salud de PostgreSQL

Verifica la conectividad y el correcto funcionamiento en caliente de la base de datos PostgreSQL ejecutando una consulta SQL básica (`SELECT 1 + 1 AS sum`).

* **Método HTTP:** `GET`
* **Ruta:** `/sgir/v1/m1/health/postgres`
* **Servicio Ejecutor:** [`app/routes/healths/health_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/healths/health_routes.py) $\rightarrow$ `health_postgres`

### 📥 Cuerpo de la Petición (Request Body)
No requiere cuerpo de petición.

### 📤 Respuestas Esperadas

#### **Status 200 OK**
Devuelto cuando la conexión con PostgreSQL se realiza y responde de manera exitosa.

```json
{
  "status": "ok",
  "db": "PostgreSQL",
  "result": 2
}
```

#### **Status 500 Internal Server Error**
Devuelto si ocurre algún fallo o excepción al intentar comunicarse con el motor de base de datos.

```json
{
  "detail": "PostgreSQL failed: <mensaje_del_error>"
}
```

---

## 2. Ping a un Host/Servidor de Red

Realiza una comprobación de conectividad ICMP (ping) rápida a un host específico utilizando sockets UDP no privilegiados de la librería `icmplib`. Es útil para validar de forma básica si una IP de red es alcanzable.

* **Método HTTP:** `POST`
* **Ruta:** `/sgir/v1/m1/health/ping`
* **Servicio Ejecutor:** [`app/routes/healths/health_routes.py`](file:///home/angel/src/titulacion/sgir_backend/app/routes/healths/health_routes.py) $\rightarrow$ `ping_host`

### 📥 Cuerpo de la Petición (Request Body - `PingRequest`)
```json
{
  "ip": "192.168.1.1"
}
```

### 📤 Respuesta Esperada

#### **Status 200 OK**
Devuelve un valor booleano simple que indica el estado de conectividad con el host.

```json
true
```
*(o `false` si el host no responde o es inalcanzable)*

> [!NOTE]
> La ejecución del ping utiliza privilegios normales (`privileged=False`), lo que permite correr el backend dentro de contenedores Docker no privilegiados sobre sistemas Linux empleando sockets UDP.
