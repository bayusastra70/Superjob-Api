
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

# def init_database():
    # """Initialize database with required tables"""
    # try:
    #     conn = get_db_connection()
    #     cursor = conn.cursor()

        
        
    #     # # Create users table
    #     # cursor.execute("""
    #     # CREATE TABLE IF NOT EXISTS users (
    #     #     id SERIAL PRIMARY KEY,
    #     #     email VARCHAR(255) UNIQUE NOT NULL,
    #     #     username VARCHAR(100) UNIQUE NOT NULL,
    #     #     full_name VARCHAR(255),
    #     #     password_hash VARCHAR(255) NOT NULL,
    #     #     is_active BOOLEAN DEFAULT true,
    #     #     is_superuser BOOLEAN DEFAULT false,
    #     #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     # );
    #     # """)

    #     cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS users (
    #         id SERIAL PRIMARY KEY,
    #         email VARCHAR(255) UNIQUE NOT NULL,
    #         username VARCHAR(100) UNIQUE NOT NULL,
    #         full_name VARCHAR(255),
    #         password_hash VARCHAR(255) NOT NULL,
    #         role VARCHAR(50) DEFAULT 'candidate' CHECK (role IN ('admin', 'employer', 'candidate')),
    #         is_active BOOLEAN DEFAULT true,
    #         is_superuser BOOLEAN DEFAULT false,
    #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     );
    #     """)
        
    #     # Create candidate_score table
    #     cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS candidate_score (
    #         id SERIAL PRIMARY KEY,
    #         application_id INTEGER NOT NULL UNIQUE,
    #         job_id INTEGER NOT NULL,
    #         candidate_name VARCHAR(255),
    #         fit_score DECIMAL(5,2) CHECK (fit_score >= 0 AND fit_score <= 100),
    #         skill_score DECIMAL(5,2),
    #         experience_score DECIMAL(5,2),
    #         education_score DECIMAL(5,2),
    #         reasons JSONB,
    #         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     );
        
    #     CREATE INDEX IF NOT EXISTS idx_candidate_score_application ON candidate_score(application_id);
    #     CREATE INDEX IF NOT EXISTS idx_candidate_score_job ON candidate_score(job_id);
    #     CREATE INDEX IF NOT EXISTS idx_candidate_score_fit ON candidate_score(fit_score);
    #     """)
        
    #     # # Check if admin user exists
    #     # cursor.execute("SELECT id FROM users WHERE email = 'admin@superjob.com'")
    #     # admin_exists = cursor.fetchone()
        
    #     # if not admin_exists:
    #     #     # Generate bcrypt hash for 'admin123'
    #     #     password = "admin123"
    #     #     password_bytes = password.encode('utf-8')
    #     #     salt = bcrypt.gensalt()
    #     #     hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
    #     #     cursor.execute("""
    #     #     INSERT INTO users (email, username, full_name, password_hash, is_superuser)
    #     #     VALUES (%s, %s, %s, %s, true)
    #     #     """, ('admin@superjob.com', 'admin', 'System Administrator', hashed_password))
            
    #     #     logger.info("Default admin user created with password: admin123")
    #     # else:
    #     #     logger.info("Admin user already exists")

    #     cursor.execute("SELECT id FROM users WHERE email = 'admin@superjob.com'")
    #     admin_exists = cursor.fetchone()
        
    #     if not admin_exists:
    #         # Generate bcrypt hash for 'admin123'
    #         password = "admin123"
    #         password_bytes = password.encode('utf-8')
    #         salt = bcrypt.gensalt()
    #         hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
    #         cursor.execute("""
    #         INSERT INTO users (email, username, full_name, password_hash, role, is_superuser)
    #         VALUES (%s, %s, %s, %s, 'admin', true)
    #         """, ('admin@superjob.com', 'admin', 'System Administrator', hashed_password))
            
    #         logger.info("Default admin user created with password: admin123")
    #     else:
    #         # Update existing admin to have 'admin' role
    #         cursor.execute("""
    #         UPDATE users 
    #         SET role = 'admin' 
    #         WHERE email = 'admin@superjob.com' AND (role IS NULL OR role != 'admin')
    #         """)
    #         if cursor.rowcount > 0:
    #             logger.info("Updated existing admin user role to 'admin'")
    #         else:
    #             logger.info("Admin user already exists")
        
    #     # Test insert some sample candidate scores for testing
    #     cursor.execute("""
    #     INSERT INTO candidate_score (application_id, job_id, candidate_name, fit_score, skill_score, experience_score, education_score, reasons)
    #     VALUES 
    #         (101, 1, 'John Doe', 85.5, 90.0, 80.0, 75.0, '{"skill_match": "Excellent Python skills", "experience": "5+ years"}'),
    #         (102, 1, 'Jane Smith', 92.3, 95.0, 85.0, 90.0, '{"skill_match": "Fullstack developer", "experience": "7+ years"}'),
    #         (103, 1, 'Bob Wilson', 78.9, 85.0, 70.0, 80.0, '{"skill_match": "Good backend skills", "experience": "3+ years"}')
    #     ON CONFLICT (application_id) DO NOTHING;
    #     """)

    #     # Create chat_threads table (gunakan VARCHAR untuk UUID)
    #     cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS chat_threads (
    #         id VARCHAR(36) PRIMARY KEY,
    #         application_id INTEGER NOT NULL,
    #         job_id INTEGER NOT NULL,
    #         employer_id INTEGER NOT NULL,
    #         candidate_id INTEGER NOT NULL,
    #         candidate_name VARCHAR(255),
    #         job_title VARCHAR(255),
    #         last_message TEXT,
    #         last_message_at TIMESTAMP,
    #         unread_count_employer INTEGER DEFAULT 0,
    #         unread_count_candidate INTEGER DEFAULT 0,
    #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     );
        
    #     CREATE INDEX IF NOT EXISTS idx_chat_threads_application ON chat_threads(application_id);
    #     CREATE INDEX IF NOT EXISTS idx_chat_threads_users ON chat_threads(employer_id, candidate_id);
    #     CREATE INDEX IF NOT EXISTS idx_chat_threads_job ON chat_threads(job_id);
    #     CREATE INDEX IF NOT EXISTS idx_chat_threads_updated ON chat_threads(updated_at DESC);
    #     """)
        
    #     # Create messages table (gunakan VARCHAR untuk UUID)
    #     cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS messages (
    #         id VARCHAR(36) PRIMARY KEY,
    #         thread_id VARCHAR(36) NOT NULL,
    #         sender_id INTEGER NOT NULL,
    #         receiver_id INTEGER NOT NULL,
    #         sender_name VARCHAR(255),
    #         receiver_name VARCHAR(255),
    #         message_text TEXT NOT NULL,
    #         status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'seen', 'failed')),
    #         is_ai_suggestion INTEGER DEFAULT 0,
    #         ai_suggestions JSONB,
    #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     );
        
    #     CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id, created_at);
    #     CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id, created_at);
    #     CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(thread_id, receiver_id, status);
    #     CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id, status, created_at);
    #     """)
        
    #     # Insert sample chat data for testing
    #     cursor.execute("""
    #     INSERT INTO chat_threads (id, application_id, job_id, employer_id, candidate_id, candidate_name, job_title, last_message, last_message_at, unread_count_employer, unread_count_candidate)
    #     VALUES 
    #         ('550e8400-e29b-41d4-a716-446655440000', 101, 1, 1, 1001, 'John Doe', 'Software Engineer', 'Hello, when can we schedule interview?', '2024-01-15 10:30:00', 2, 0),
    #         ('550e8400-e29b-41d4-a716-446655440001', 102, 1, 1, 1002, 'Jane Smith', 'Backend Developer', 'Thanks for applying!', '2024-01-14 14:20:00', 0, 1),
    #         ('550e8400-e29b-41d4-a716-446655440002', 103, 2, 2, 1003, 'Bob Wilson', 'Frontend Developer', 'Please send your portfolio', '2024-01-13 09:15:00', 1, 1)
    #     ON CONFLICT (id) DO NOTHING;
    #     """)
        
    #     cursor.execute("""
    #     INSERT INTO messages (id, thread_id, sender_id, receiver_id, sender_name, receiver_name, message_text, status, created_at)
    #     VALUES 
    #         ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '550e8400-e29b-41d4-a716-446655440000', 1001, 1, 'John Doe', 'HR Manager', 'Hello, I applied for the Software Engineer position', 'seen', '2024-01-15 09:00:00'),
    #         ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', '550e8400-e29b-41d4-a716-446655440000', 1, 1001, 'HR Manager', 'John Doe', 'Thanks for applying! When are you available for interview?', 'seen', '2024-01-15 09:30:00'),
    #         ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', '550e8400-e29b-41d4-a716-446655440000', 1001, 1, 'John Doe', 'HR Manager', 'I am available tomorrow after 2 PM', 'delivered', '2024-01-15 10:30:00'),
    #         ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', '550e8400-e29b-41d4-a716-446655440000', 1, 1001, 'HR Manager', 'John Doe', 'Perfect! Let schedule at 3 PM tomorrow', 'sent', '2024-01-15 10:35:00'),
    #         ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', '550e8400-e29b-41d4-a716-446655440001', 1, 1002, 'HR Manager', 'Jane Smith', 'Hi Jane, we received your application', 'seen', '2024-01-14 14:00:00'),
    #         ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', '550e8400-e29b-41d4-a716-446655440001', 1002, 1, 'Jane Smith', 'HR Manager', 'Thank you! Looking forward to hearing back', 'delivered', '2024-01-14 14:20:00')
    #     ON CONFLICT (id) DO NOTHING;
    #     """)
        
    #     logger.info("Chat tables created with sample data")

    #     cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS jobs (
    #         id SERIAL PRIMARY KEY,
    #         job_code VARCHAR(50) UNIQUE NOT NULL,
    #         title VARCHAR(255) NOT NULL,
    #         department VARCHAR(100),
    #         location VARCHAR(100),
    #         employment_type VARCHAR(50),
    #         experience_level VARCHAR(50),
    #         education_requirement VARCHAR(100),
    #         salary_range VARCHAR(100),
    #         status VARCHAR(20) DEFAULT 'open',
    #         description TEXT,
    #         requirements TEXT,
    #         responsibilities TEXT,
    #         created_by INTEGER,
    #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     );
        
    #     CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
    #     CREATE INDEX IF NOT EXISTS idx_jobs_department ON jobs(department);
    #     """)
        
    #     # Create applications table
    #     cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS applications (
    #         id SERIAL PRIMARY KEY,
    #         job_id INTEGER NOT NULL,
    #         candidate_id INTEGER NOT NULL,
    #         candidate_name VARCHAR(255) NOT NULL,
    #         candidate_email VARCHAR(255) NOT NULL,
    #         candidate_phone VARCHAR(50),
    #         candidate_linkedin VARCHAR(255),
    #         candidate_cv_url TEXT,
    #         candidate_education VARCHAR(100),
    #         candidate_experience_years INTEGER,
    #         current_company VARCHAR(255),
    #         current_position VARCHAR(255),
    #         expected_salary VARCHAR(100),
    #         notice_period VARCHAR(50),
            
    #         -- Application status
    #         application_status VARCHAR(50) DEFAULT 'applied',
    #         interview_stage VARCHAR(50),
    #         interview_scheduled_by VARCHAR(100),
    #         interview_date TIMESTAMP,
            
    #         -- Scoring
    #         fit_score DECIMAL(5,2),
    #         skill_score DECIMAL(5,2),
    #         experience_score DECIMAL(5,2),
    #         overall_score DECIMAL(5,2),
            
    #         -- Additional info
    #         source VARCHAR(50),
    #         tags TEXT[],
    #         notes TEXT,
            
    #         -- Metadata
    #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #         applied_date DATE DEFAULT CURRENT_DATE
    #     );
        
    #     CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
    #     CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(application_status);
    #     CREATE INDEX IF NOT EXISTS idx_applications_stage ON applications(interview_stage);
    #     CREATE INDEX IF NOT EXISTS idx_applications_score ON applications(overall_score DESC);
    #     """)
        
    #     # Create application_history table
    #     cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS application_history (
    #         id SERIAL PRIMARY KEY,
    #         application_id INTEGER NOT NULL,
    #         changed_by INTEGER,
    #         previous_status VARCHAR(50),
    #         new_status VARCHAR(50),
    #         previous_stage VARCHAR(50),
    #         new_stage VARCHAR(50),
    #         change_reason TEXT,
    #         change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     );
        
    #     CREATE INDEX IF NOT EXISTS idx_app_history_application ON application_history(application_id);
    #     """)
        
    #     # Insert sample jobs data (matching Figma)
    #     cursor.execute("""
    #     INSERT INTO jobs (id, job_code, title, department, location, employment_type, 
    #                      experience_level, education_requirement, salary_range, status)
    #     VALUES 
    #         (1, 'UIUX-001', 'UI/UX Designer', 'Design', 'Jakarta', 'Full-time', 
    #          'Mid-level', 'S1/D4', 'Rp 10-15 juta', 'open'),
    #         (2, 'UIUX-002', 'Senior UI/UX Designer', 'Design', 'Bandung', 'Full-time',
    #          'Senior', 'S1/D4', 'Rp 15-20 juta', 'open'),
    #         (3, 'DEV-001', 'Backend Developer', 'Engineering', 'Jakarta', 'Full-time',
    #          'Mid-level', 'S1/D4', 'Rp 12-18 juta', 'open')
    #     ON CONFLICT (id) DO NOTHING;
    #     """)
        
    #     # Insert sample applications data (matching Figma table)
    #     cursor.execute("""
    #     INSERT INTO applications (
    #         id, job_id, candidate_id, candidate_name, candidate_email, candidate_phone,
    #         candidate_linkedin, candidate_cv_url, candidate_education, candidate_experience_years,
    #         current_company, current_position, expected_salary, notice_period,
    #         application_status, interview_stage, interview_scheduled_by,
    #         fit_score, skill_score, experience_score, overall_score, source
    #     )
    #     VALUES 
    #         -- Walter Gibson (Applied)
    #         (1, 1, 1001, 'Walter Gibson', 'walter@gmail.com', '+6281234567890',
    #          NULL, 'https://storage/cv_walter.pdf', 'SMA/SMK', 3,
    #          'TechCorp', 'Junior Designer', 'Rp 12 juta', '1 month',
    #          'applied', NULL, NULL,
    #          78.5, 75.0, 80.0, 77.8, 'job_portal'),
             
    #         -- Lewis Redenson (Qualified)
    #         (2, 1, 1002, 'Lewis Redenson', 'lewis@gmail.com', '+6281234567891',
    #          'linkedin.com/in/lewis', 'https://storage/cv_lewis.pdf', 'S1/D4', 5,
    #          'DesignStudio', 'UI Designer', 'Rp 14 juta', 'Immediate',
    #          'qualified', 'first_interview', 'by: A',
    #          85.0, 88.0, 82.0, 85.0, 'linkedin'),
             
    #         -- Delsey Tam (Qualified)
    #         (3, 1, 1003, 'Delsey Tam', 'delsey@gmail.com', '+6281234567892',
    #          'linkedin.com/in/delsey', 'https://storage/cv_delsey.pdf', 'S1/D4', 4,
    #          'CreativeAgency', 'UX Designer', 'Rp 13 juta', '2 weeks',
    #          'qualified', 'second_interview', NULL,
    #          82.5, 85.0, 80.0, 82.5, 'referral'),
             
    #         -- Alejandro Holland (Contract Signed)
    #         (4, 1, 1004, 'Alejandro Holland', 'alejandro@gmail.com', '+6281234567893',
    #          NULL, 'https://storage/cv_alejandro.pdf', 'D3', 2,
    #          'StartupXYZ', 'Design Intern', 'Rp 10 juta', 'Immediate',
    #          'contract_signed', 'contract_signed', NULL,
    #          70.0, 72.0, 68.0, 70.0, 'job_portal'),
             
    #         -- Rose Foster (Not Qualified)
    #         (5, 1, 1005, 'Rose Foster', 'rose@gmail.com', '+6281234567894',
    #          NULL, 'https://storage/cv_rose.pdf', 'S1/D4', 1,
    #          'FreshGraduate', 'Fresh Graduate', 'Rp 9 juta', 'Immediate',
    #          'not_qualified', NULL, NULL,
    #          65.0, 60.0, 62.0, 62.3, 'job_portal')
    #     ON CONFLICT (id) DO NOTHING;
    #     """)
        
    #     logger.info("Jobs and Applications tables created with sample data")
        
        
    #     logger.info("Database initialized successfully with sample data")
    #     cursor.close()
        
    # except Exception as e:
    #     logger.error(f"Error initializing database: {e}")
    #     raise