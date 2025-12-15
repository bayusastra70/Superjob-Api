import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


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
            logger.info(
                f"Connected to database: {settings.DB_NAME} on {settings.DB_HOST}:{settings.DB_PORT}"
            )
            return self.connection
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
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
            logger.warning("Database connection broken, reconnecting...")
            self.close()
            return self.connect()

        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")


# Global database instance
db = Database()


def get_db_connection():
    return db.get_connection()
