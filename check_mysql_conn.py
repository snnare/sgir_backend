import sys
from sqlalchemy import create_engine, text

print("--- Testing MySQL 5 with 'sgir_monitoreo' on port 3305 ---")
try:
    engine5 = create_engine("mysql+pymysql://sgir_monitoreo:123Nokia$@127.0.0.1:3305/performance_schema")
    with engine5.connect() as conn:
        print("MySQL 5 connection successful!")
        
        # 1. Probar performance_schema.global_status
        print("Querying performance_schema.global_status...")
        try:
            status_res = conn.execute(text("""
                SELECT VARIABLE_NAME, VARIABLE_VALUE 
                FROM performance_schema.global_status 
                WHERE LOWER(VARIABLE_NAME) IN ('uptime', 'threads_connected')
            """)).fetchall()
            print("performance_schema.global_status result:", status_res)
        except Exception as e5_status:
            print("Query to performance_schema.global_status failed:", e5_status)
            
        # 2. Probar performance_schema.global_variables
        print("Querying performance_schema.global_variables...")
        try:
            var_res = conn.execute(text("""
                SELECT VARIABLE_VALUE 
                FROM performance_schema.global_variables 
                WHERE LOWER(VARIABLE_NAME) = 'max_connections'
            """)).fetchone()
            print("performance_schema.global_variables result:", var_res)
        except Exception as e5_var:
            print("Query to performance_schema.global_variables failed:", e5_var)
            
except Exception as e:
    print("MySQL 5 main connection failed:", e)


print("\n--- Testing MySQL 8 with 'sgir_monitoreo' on port 3308 ---")
try:
    engine8 = create_engine("mysql+pymysql://sgir_monitoreo:123Nokia$@127.0.0.1:3308/performance_schema")
    with engine8.connect() as conn:
        print("MySQL 8 connection successful!")
        
        # 1. Probar performance_schema.global_status
        print("Querying performance_schema.global_status...")
        try:
            status_res = conn.execute(text("""
                SELECT VARIABLE_NAME, VARIABLE_VALUE 
                FROM performance_schema.global_status 
                WHERE LOWER(VARIABLE_NAME) IN ('uptime', 'threads_connected')
            """)).fetchall()
            print("performance_schema.global_status result:", status_res)
        except Exception as e8_status:
            print("Query to performance_schema.global_status failed:", e8_status)
            
        # 2. Probar performance_schema.global_variables
        print("Querying performance_schema.global_variables...")
        try:
            var_res = conn.execute(text("""
                SELECT VARIABLE_VALUE 
                FROM performance_schema.global_variables 
                WHERE LOWER(VARIABLE_NAME) = 'max_connections'
            """)).fetchone()
            print("performance_schema.global_variables result:", var_res)
        except Exception as e8_var:
            print("Query to performance_schema.global_variables failed:", e8_var)
            
except Exception as e:
    print("MySQL 8 main connection failed:", e)
