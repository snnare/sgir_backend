from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import MySQLPerformanceMetrics

def get_group_c_performance(db: Session) -> MySQLPerformanceMetrics:
    """
    Grupo C: Rendimiento InnoDB de MySQL 8.
    Realiza consultas directas a performance_schema.
    """
    try:
        status_res = db.execute(text("""
            SELECT VARIABLE_NAME, VARIABLE_VALUE 
            FROM performance_schema.global_status 
            WHERE LOWER(VARIABLE_NAME) IN (
                'innodb_row_lock_waits', 'innodb_row_lock_time_avg', 
                'innodb_buffer_pool_pages_dirty', 'innodb_buffer_pool_read_requests', 
                'innodb_buffer_pool_reads'
            )
        """)).fetchall()
        stats = {row[0].lower(): int(row[1] or 0) for row in status_res}

        row_lock_waits = stats.get('innodb_row_lock_waits', 0)
        row_lock_time_avg = stats.get('innodb_row_lock_time_avg', 0)
        dirty_pages = stats.get('innodb_buffer_pool_pages_dirty', 0)
        read_requests = stats.get('innodb_buffer_pool_read_requests', 0)
        reads = stats.get('innodb_buffer_pool_reads', 0)

        # Hit ratio calculation
        if read_requests > 0:
            hit_ratio = round(((read_requests - reads) / read_requests) * 100, 2)
        else:
            hit_ratio = 100.0

        return MySQLPerformanceMetrics(
            innodb_row_lock_waits=row_lock_waits,
            innodb_row_lock_time_avg=row_lock_time_avg,
            innodb_buffer_pool_pages_dirty=dirty_pages,
            innodb_buffer_pool_read_requests=read_requests,
            innodb_buffer_pool_reads=reads,
            innodb_buffer_pool_hit_ratio=hit_ratio
        )
    except Exception:
        return MySQLPerformanceMetrics(
            innodb_row_lock_waits=0,
            innodb_row_lock_time_avg=0,
            innodb_buffer_pool_pages_dirty=0,
            innodb_buffer_pool_read_requests=0,
            innodb_buffer_pool_reads=0,
            innodb_buffer_pool_hit_ratio=0.0
        )
