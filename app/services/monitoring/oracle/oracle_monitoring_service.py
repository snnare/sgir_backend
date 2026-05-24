from sqlalchemy.orm import Session
from datetime import datetime
from app.core.dynamic_db_core import get_dynamic_session
from app.models.infrastructure_models import InstanciaDBMS
from app.services.monitoring.oracle.metrics.connectivity_provider import get_group_a_connectivity
from app.services.monitoring.oracle.metrics.resource_provider import get_group_b_resources
from app.services.monitoring.oracle.metrics.performance_provider import get_group_c_performance

def run_oracle_modular_monitoring(db: Session, id_instancia: int, id_credencial: int) -> dict:
    # 1. Obtener Metadatos del Servidor e Instancia
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == id_instancia).first()
    if not instancia:
        return {"error": "Instancia no encontrada"}
    
    servidor = instancia.servidor
    criticidad_id = servidor.id_nivel_criticidad # 1: Bajo, 2: Medio, 3: Alto, 4: Crítico
    
    # Obtener el nombre del nivel de criticidad manualmente para evitar problemas de relación
    from app.models.infrastructure_models import NivelCriticidad
    criticidad_obj = db.query(NivelCriticidad).filter(NivelCriticidad.id_nivel_criticidad == criticidad_id).first()
    criticidad_nombre = criticidad_obj.nombre_nivel if criticidad_obj else "Desconocido"
    
    # 2. Conexión Dinámica a Oracle
    # Reutilizamos la credencial pasada por el endpoint
    from app.services import get_credencial
    credencial = get_credencial(db, id_credencial)
    
    remote_session = None
    try:
        remote_session = get_dynamic_session(
            servidor, 
            credencial, 
            dbms_id=4, 
            db_name=instancia.nombre_instancia, 
            parametros=instancia.parametros_conexion
        )
        
        # 3. Recolección Modular basada en Criticidad
        timestamp = datetime.now()
        
        # Grupo A (Siempre se ejecuta)
        grupo_a = get_group_a_connectivity(remote_session)
        
        grupo_b = None
        if criticidad_id >= 2: # Medio, Alto, Crítico
            grupo_b = get_group_b_resources(remote_session)
            
        grupo_c = None
        if criticidad_id >= 3: # Alto, Crítico
            grupo_c = get_group_c_performance(remote_session)
            
        return {
            "id_instancia": id_instancia,
            "id_servidor": servidor.id_servidor,
            "nivel_criticidad": criticidad_nombre,
            "timestamp": timestamp,
            "grupo_a": grupo_a,
            "grupo_b": grupo_b,
            "grupo_c": grupo_c
        }
        
    except Exception as e:
        error_str = str(e)
        print(f"[ORACLE FALLBACK] Conexión TCP estándar falló: {error_str}. Intentando fallback vía SSH...")
        
        try:
            from app.models.infrastructure_models import CredencialAcceso
            from app.core.ssh_orchestrator import get_ssh_connection
            from app.core.security.encryption import decrypt_password
            
            # Buscar credencial SSH activa (id_tipo_acceso == 1)
            ssh_cred = db.query(CredencialAcceso).filter(
                CredencialAcceso.id_servidor == servidor.id_servidor,
                CredencialAcceso.id_tipo_acceso == 1,
                CredencialAcceso.id_estado_credencial == 1
            ).first()
            
            if not ssh_cred:
                return {"error": f"Fallo en conexión TCP Oracle ({error_str}) y no se encontró credencial SSH activa para fallback."}
            
            # Obtener cliente SSH del pool global
            ssh_client = get_ssh_connection(servidor, ssh_cred)
            
            # Descifrar credenciales de BD
            db_user = credencial.usuario
            db_password = decrypt_password(credencial.password_hash)
            
            # Obtener SID
            params = instancia.parametros_conexion or {}
            sid = params.get("sid") or "ORCL"
            
            # Comando PL/SQL unificado vía sqlplus ejecutado de forma remota
            # Entra a /home/oracle, ejecuta source .bash_profile y exporta el ORACLE_SID
            cmd = f"""cd /home/oracle && source .bash_profile
export ORACLE_SID={sid}
sqlplus -S {db_user}/{db_password} << 'EOF'
SET SERVEROUTPUT ON;
SET HEAD OFF FEEDBACK OFF ECHO OFF PAGESIZE 0 TRIMSPOOL ON;
DECLARE
  v_active_conn NUMBER := 0;
  v_max_conn VARCHAR2(100) := '150';
  v_total_dbs NUMBER := 1;
  v_threads NUMBER := 0;
  v_mem_usage NUMBER := 0;
  v_mem_max VARCHAR2(100) := '0';
  v_locks NUMBER := 0;
  v_slow_queries NUMBER := 0;
  v_resp_time NUMBER := 0;
  v_cpu_usage NUMBER := 0;
  v_cpu_percent NUMBER := 0;
BEGIN
  -- 1. Active Connections
  BEGIN
    SELECT count(*) INTO v_active_conn FROM v$session WHERE status = 'ACTIVE';
  EXCEPTION WHEN OTHERS THEN NULL;
  END;

  -- 2. Max Connections
  BEGIN
    SELECT value INTO v_max_conn FROM v$parameter WHERE name = 'processes';
  EXCEPTION WHEN OTHERS THEN NULL;
  END;

  -- 3. Total PDBs (Check if v$pdbs is available, multitenant 12c+)
  BEGIN
    EXECUTE IMMEDIATE 'SELECT count(*) FROM v$pdbs' INTO v_total_dbs;
  EXCEPTION WHEN OTHERS THEN
    v_total_dbs := 1;
  END;

  -- 4. Threads (Processes in SO)
  BEGIN
    SELECT count(*) INTO v_threads FROM v$process;
  EXCEPTION WHEN OTHERS THEN NULL;
  END;

  -- 5. Memory SGA
  BEGIN
    SELECT sum(value)/1024/1024 INTO v_mem_usage FROM v$sga;
  EXCEPTION WHEN OTHERS THEN NULL;
  END;

  -- 6. Memory Target
  BEGIN
    SELECT value INTO v_mem_max FROM v$parameter WHERE name = 'memory_target';
  EXCEPTION WHEN OTHERS THEN NULL;
  END;
  IF v_mem_max IS NULL OR v_mem_max = '0' THEN
    v_mem_max := TO_CHAR(v_mem_usage);
  ELSE
    v_mem_max := TO_CHAR(TO_NUMBER(v_mem_max)/1024/1024);
  END IF;

  -- 7. Locks
  BEGIN
    SELECT count(*) INTO v_locks FROM v$lock WHERE block > 0;
  EXCEPTION WHEN OTHERS THEN NULL;
  END;

  -- 8. Slow Queries
  BEGIN
    SELECT count(*) INTO v_slow_queries FROM v$sqlarea WHERE elapsed_time/1000000 > 1;
  EXCEPTION WHEN OTHERS THEN NULL;
  END;

  -- 9. Response Time
  BEGIN
    SELECT average_wait INTO v_resp_time FROM v$system_event WHERE event = 'db file sequential read';
  EXCEPTION WHEN OTHERS THEN
    v_resp_time := 0;
  END;

  -- 10. CPU Usage
  BEGIN
    SELECT value INTO v_cpu_usage FROM v$sysstat WHERE name = 'CPU used by this session' AND rownum = 1;
    v_cpu_percent := MOD(v_cpu_usage, 100);
  EXCEPTION WHEN OTHERS THEN
    v_cpu_percent := 0;
  END;

  -- Output result line
  DBMS_OUTPUT.PUT_LINE(
    v_active_conn || '|' ||
    v_max_conn || '|' ||
    v_total_dbs || '|' ||
    v_threads || '|' ||
    ROUND(v_mem_usage, 2) || '|' ||
    ROUND(TO_NUMBER(v_mem_max), 2) || '|' ||
    v_locks || '|' ||
    v_slow_queries || '|' ||
    ROUND(v_resp_time, 2) || '|' ||
    ROUND(v_cpu_percent, 2)
  );
END;
/
EOF
"""
            stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=15)
            out = stdout.read().decode('utf-8').strip()
            err = stderr.read().decode('utf-8').strip()
            
            metric_line = None
            for line in out.splitlines():
                line = line.strip()
                if line.count('|') == 9:
                    metric_line = line
                    break
                    
            if not metric_line:
                error_msg = err if err else f"Salida inesperada de sqlplus: {out}"
                return {"error": f"Fallo en monitoreo de fallback vía SSH para Oracle: {error_msg}"}
                
            parts = metric_line.split('|')
            active_conn = int(parts[0])
            max_conn = int(parts[1])
            total_dbs = int(parts[2])
            threads = int(parts[3])
            mem_usage = float(parts[4])
            mem_max = float(parts[5])
            locks = int(parts[6])
            slow_queries = int(parts[7])
            resp_time = float(parts[8])
            cpu_percent = float(parts[9])
            
            return {
                "id_instancia": id_instancia,
                "id_servidor": servidor.id_servidor,
                "nivel_criticidad": criticidad_nombre,
                "timestamp": datetime.now(),
                "grupo_a": {
                    "status": "UP",
                    "active_connections": active_conn,
                    "max_connections": max_conn,
                    "total_databases": total_dbs
                },
                "grupo_b": {
                    "threads_count": threads,
                    "memory_usage_mb": mem_usage,
                    "memory_max_mb": mem_max,
                    "active_locks": locks
                } if criticidad_id >= 2 else None,
                "grupo_c": {
                    "slow_queries_count": slow_queries,
                    "avg_response_time_ms": resp_time,
                    "cpu_usage_percent": cpu_percent
                } if criticidad_id >= 3 else None
            }
            
        except Exception as ssh_err:
            return {"error": f"Fallo en monitoreo Oracle TCP ({error_str}) y Fallo en fallback SSH ({str(ssh_err)})"}
            
    finally:
        if remote_session:
            remote_session.close()
