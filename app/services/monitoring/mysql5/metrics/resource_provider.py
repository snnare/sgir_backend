from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import MySQLResourceMetrics

def get_group_b_resources(db: Session, uptime: int) -> MySQLResourceMetrics:
    """
    Grupo B: Recursos y Carga de MySQL 5.
    Realiza consultas directas a information_schema.
    """
    try:
        try:
            status_res = db.execute(text("""
                SELECT VARIABLE_NAME, VARIABLE_VALUE 
                FROM information_schema.global_status 
                WHERE LOWER(VARIABLE_NAME) IN (
                    'threads_running', 'questions', 'slow_queries', 'table_locks_waited'
                )
            """)).fetchall()
        except Exception:
            status_res = db.execute(text("""
                SELECT VARIABLE_NAME, VARIABLE_VALUE 
                FROM performance_schema.global_status 
                WHERE LOWER(VARIABLE_NAME) IN (
                    'threads_running', 'questions', 'slow_queries', 'table_locks_waited'
                )
            """)).fetchall()
        stats = {row[0].lower(): int(row[1] or 0) for row in status_res}

        threads_running = stats.get('threads_running', 0)
        questions = stats.get('questions', 0)
        slow_queries = stats.get('slow_queries', 0)
        table_locks_waited = stats.get('table_locks_waited', 0)

        qps = round(questions / uptime, 2) if uptime > 0 else 0.0

        return MySQLResourceMetrics(
            threads_running=threads_running,
            questions=questions,
            queries_per_second=qps,
            slow_queries=slow_queries,
            table_locks_waited=table_locks_waited
        )
    except Exception:
        return MySQLResourceMetrics(
            threads_running=0,
            questions=0,
            queries_per_second=0.0,
            slow_queries=0,
            table_locks_waited=0
        )
