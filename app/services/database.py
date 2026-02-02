# import psycopg2
# from psycopg2.extras import RealDictCursor
# from app.core.config import settings
# from loguru import logger


# class Database:
#     def __init__(self):
#         self.connection = None

#     def connect(self):
#         """Connect to standalone PostgreSQL database"""
#         try:
#             self.connection = psycopg2.connect(
#                 host=settings.DB_HOST,
#                 port=settings.DB_PORT,
#                 database=settings.DB_NAME,
#                 user=settings.DB_USER,
#                 password=settings.DB_PASSWORD,
#                 cursor_factory=RealDictCursor,
#             )
#             self.connection.autocommit = True
#             logger.info(f"Connected to Database at {settings.DB_HOST}", event="db_connected", context={"db_host": settings.DB_HOST, "db_name": settings.DB_NAME})
#             return self.connection
#         except Exception as e:
#             logger.error(f"Failed to connect to Database", event="db_connection_failure", error={"type": e.__class__.__name__, "message": str(e), "code": "DB_CONNECT_ERROR"}, context={"db_host": settings.DB_HOST})
#             return None

#     def get_connection(self):
#         if self.connection is None or self.connection.closed:
#             return self.connect()

#         # Test connection
#         try:
#             cursor = self.connection.cursor()
#             cursor.execute("SELECT 1")
#             cursor.close()
#         except psycopg2.InterfaceError:
#             # Reconnect if connection is broken
#             logger.warning("Database connection broken, reconnecting", event="db_reconnect", context={"db_host": settings.DB_HOST})
#             self.close()
#             return self.connect()

#         return self.connection

#     def close(self):
#         if self.connection:
#             self.connection.close()
#             self.connection = None
#             logger.info("Database connection closed", event="db_disconnected")


# # Global database instance
# db = Database()


# def get_db_connection():
#     return db.get_connection()


import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
from loguru import logger
import threading
import queue

class DatabasePool:
    def __init__(self):
        self.pool = None
        self._lock = threading.Lock()
        self.max_connections = 10
    
    def create_pool(self):
        """Create connections for pool"""
        connections = queue.Queue(maxsize=self.max_connections)
        
        for _ in range(3):  # Start with 3 connections
            try:
                conn = psycopg2.connect(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    cursor_factory=RealDictCursor,
                )
                conn.autocommit = True
                connections.put(conn)
            except Exception as e:
                logger.error(f"Failed to create connection: {e}")
        
        self.pool = connections
        # logger.info(f"Database pool created with {connections.qsize()} connections")
    
    def get_connection(self):
        """Get connection from pool (thread-safe)"""
        with self._lock:
            if self.pool is None:
                self.create_pool()
            
            try:
                # Try to get connection from pool
                conn = self.pool.get_nowait()
                
                # Test if connection is still alive
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    return conn
                except:
                    # Connection is dead, create new one
                    logger.warning("Connection dead, creating new one")
                    try:
                        conn.close()
                    except:
                        pass
                    return self._create_new_connection()
                    
            except queue.Empty:
                # Pool is empty, create new connection
                logger.debug("Pool empty, creating new connection")
                return self._create_new_connection()
    
    def _create_new_connection(self):
        """Create new database connection"""
        try:
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                cursor_factory=RealDictCursor,
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            logger.error(f"Failed to create new connection: {e}")
            raise
    
    def return_connection(self, conn):
        """Return connection to pool"""
        if self.pool is None:
            self.create_pool()
        
        try:
            # Reset connection state
            try:
                conn.rollback()
            except:
                pass
            conn.autocommit = True
            
            # Put back to pool if there's space
            try:
                self.pool.put_nowait(conn)
            except queue.Full:
                # Pool is full, close this connection
                logger.debug("Pool full, closing connection")
                try:
                    conn.close()
                except:
                    pass
                
        except Exception as e:
            logger.warning(f"Error returning connection to pool: {e}")
            try:
                conn.close()
            except:
                pass
    
    def close_all(self):
        """Close all connections in pool"""
        if self.pool:
            while not self.pool.empty():
                try:
                    conn = self.pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
                except:
                    pass
            self.pool = None
            logger.info("Database pool closed")

# Global pool instance
db_pool = DatabasePool()

# Main function untuk backward compatibility
def get_db_connection():
    """Get raw connection (caller must call release_connection)"""
    return db_pool.get_connection()

def release_connection(conn):
    """Release connection back to pool"""
    db_pool.return_connection(conn)

# Optional: context manager for new code
from contextlib import contextmanager

@contextmanager
def db_connection():
    """Context manager for database connection"""
    conn = db_pool.get_connection()
    try:
        yield conn
    finally:
        db_pool.return_connection(conn)