from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
import logging

logger = logging.getLogger("db_pool_manager")

class DBConnectionPool:
    """
    Administrador de conexiones persistentes para bases de datos remotas.
    Mantiene Engines de SQLAlchemy y Clientes de MongoDB para evitar reconexiones.
    """
    def __init__(self):
        # Engines de SQLAlchemy (MySQL, Oracle, Postgres)
        self._engines = {} 
        # Clientes de MongoDB
        self._mongo_clients = {}

    def get_rdbms_session(self, pool_key: str, url: str):
        """Obtiene o crea un Engine de SQLAlchemy y retorna una sesión."""
        if pool_key not in self._engines:
            logger.info(f"Creando nuevo Engine persistente para: {pool_key}")
            # Pool de 5 conexiones con reciclaje de 1 hora para evitar 'stale connections'
            engine = create_engine(
                url, 
                pool_size=5, 
                max_overflow=10, 
                pool_recycle=3600,
                pool_pre_ping=True # Verifica si la conexión sigue viva antes de usarla
            )
            self._engines[pool_key] = engine
        
        engine = self._engines[pool_key]
        SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return SessionLocal()

    def get_mongo_client(self, pool_key: str, url: str):
        """Obtiene o crea un cliente persistente de MongoDB."""
        if pool_key not in self._mongo_clients:
            logger.info(f"Creando nuevo Cliente MongoDB persistente para: {pool_key}")
            client = MongoClient(url, serverSelectionTimeoutMS=5000)
            self._mongo_clients[pool_key] = client
        
        return self._mongo_clients[pool_key]

    def close_all(self):
        """Cierra todos los pools al apagar la aplicación."""
        for key, engine in self._engines.items():
            engine.dispose()
            logger.info(f"Engine disposal: {key}")
        
        for key, client in self._mongo_clients.items():
            client.close()
            logger.info(f"Mongo client closed: {key}")
        
        self._engines.clear()
        self._mongo_clients.clear()

# Instancia global del pool
db_pool = DBConnectionPool()
