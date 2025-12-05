
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
import logging
import bcrypt  # ← Add import

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
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = True
            logger.info(f"Connected to database: {settings.DB_NAME} on {settings.DB_HOST}:{settings.DB_PORT}")
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

def init_database():
    """Initialize database with required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(100) UNIQUE NOT NULL,
            full_name VARCHAR(255),
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT true,
            is_superuser BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Create candidate_score table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_score (
            id SERIAL PRIMARY KEY,
            application_id INTEGER NOT NULL UNIQUE,
            job_id INTEGER NOT NULL,
            candidate_name VARCHAR(255),
            fit_score DECIMAL(5,2) CHECK (fit_score >= 0 AND fit_score <= 100),
            skill_score DECIMAL(5,2),
            experience_score DECIMAL(5,2),
            education_score DECIMAL(5,2),
            reasons JSONB,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_candidate_score_application ON candidate_score(application_id);
        CREATE INDEX IF NOT EXISTS idx_candidate_score_job ON candidate_score(job_id);
        CREATE INDEX IF NOT EXISTS idx_candidate_score_fit ON candidate_score(fit_score);
        """)
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE email = 'admin@superjob.com'")
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            # Generate bcrypt hash for 'admin123'
            password = "admin123"
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
            cursor.execute("""
            INSERT INTO users (email, username, full_name, password_hash, is_superuser)
            VALUES (%s, %s, %s, %s, true)
            """, ('admin@superjob.com', 'admin', 'System Administrator', hashed_password))
            
            logger.info("Default admin user created with password: admin123")
        else:
            logger.info("Admin user already exists")
        
        # Test insert some sample candidate scores for testing
        cursor.execute("""
        INSERT INTO candidate_score (application_id, job_id, candidate_name, fit_score, skill_score, experience_score, education_score, reasons)
        VALUES 
            (101, 1, 'John Doe', 85.5, 90.0, 80.0, 75.0, '{"skill_match": "Excellent Python skills", "experience": "5+ years"}'),
            (102, 1, 'Jane Smith', 92.3, 95.0, 85.0, 90.0, '{"skill_match": "Fullstack developer", "experience": "7+ years"}'),
            (103, 1, 'Bob Wilson', 78.9, 85.0, 70.0, 80.0, '{"skill_match": "Good backend skills", "experience": "3+ years"}')
        ON CONFLICT (application_id) DO NOTHING;
        """)
        
        logger.info("Database initialized successfully with sample data")
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise