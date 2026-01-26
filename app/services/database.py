import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
from loguru import logger


class Database:
    def __init__(self):
        self.connection = None

    def connect(self):
        """Connect to standalone PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                cursor_factory=RealDictCursor,
            )
            self.connection.autocommit = True
            logger.info(f"Connected to Database at {settings.DB_HOST}", event="db_connected", context={"db_host": settings.DB_HOST, "db_name": settings.DB_NAME})
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to Database", event="db_connection_failure", error={"type": e.__class__.__name__, "message": str(e), "code": "DB_CONNECT_ERROR"}, context={"db_host": settings.DB_HOST})
            return None

    def get_connection(self):
        if self.connection is None or self.connection.closed:
            return self.connect()

        # Test connection
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        except psycopg2.InterfaceError:
            # Reconnect if connection is broken
            logger.warning("Database connection broken, reconnecting", event="db_reconnect", context={"db_host": settings.DB_HOST})
            self.close()
            return self.connect()

        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed", event="db_disconnected")


# Global database instance
db = Database()


def get_db_connection():
    return db.get_connection()
