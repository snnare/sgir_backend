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
            # Creamos el Engine
            engine = create_engine(
                url, 
                pool_size=5, 
                max_overflow=10, 
                pool_recycle=3600,
                pool_pre_ping=True # Verifica si la conexión sigue viva antes de usarla
            )
            # Validamos si la conexión funciona para interceptar errores de charset (ej. MySQL legacy)
            try:
                with engine.connect() as conn:
                    pass
            except Exception as e:
                orig_err = getattr(e, 'orig', None)
                # Si el error subyacente de pymysql es 1115 (Unknown character set: 'utf8mb4')
                if orig_err and len(orig_err.args) > 0 and orig_err.args[0] == 1115:
                    if "charset=utf8mb4" in url:
                        fallback_url = url.replace("charset=utf8mb4", "charset=utf8")
                        logger.warning(f"Charset utf8mb4 no soportado para {pool_key}. Reintentando automáticamente con utf8.")
                        engine = create_engine(
                            fallback_url,
                            pool_size=5,
                            max_overflow=10,
                            pool_recycle=3600,
                            pool_pre_ping=True
                        )
                        # Validamos el fallback también
                        try:
                            with engine.connect() as conn:
                                pass
                        except Exception as e2:
                            orig_err2 = getattr(e2, 'orig', None)
                            if orig_err2 and len(orig_err2.args) > 0 and orig_err2.args[0] == 1115:
                                fallback_url2 = fallback_url.replace("charset=utf8", "charset=latin1")
                                logger.warning(f"Charset utf8 no soportado para {pool_key}. Reintentando automáticamente con latin1.")
                                engine = create_engine(
                                    fallback_url2,
                                    pool_size=5,
                                    max_overflow=10,
                                    pool_recycle=3600,
                                    pool_pre_ping=True
                                )
                            else:
                                raise e2
                    else:
                        raise e
                else:
                    raise e
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
