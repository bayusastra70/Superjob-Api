"""Seed initial data (complete from Excel)

Revision ID: 0002_seed_initial_data
Revises: 0001_initial_database
Create Date: 2025-12-13 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from sqlalchemy.dialects import postgresql
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = "0002_seed_initial_data"
down_revision = "0001_initial_database"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== INSERT USERS ==========
    op.execute("""
    INSERT INTO users (id, email, username, full_name, password_hash, is_active, is_superuser, created_at, updated_at, role) VALUES
    (1, 'admin@superjob.com', 'admin', 'System Administrator', '$2b$12$Lx9h2EmZ6D9KirDL0FBkFO4ig0a9WrucMHKjzsHAdp60l0cLN5dB2', TRUE, TRUE, '2025-12-02 00:57:14.714', '2025-12-02 00:57:14.714', 'admin'),
    (2, 'fikri@gmail.com', 'fikri', 'mfikriab', '$2b$12$nLsrXyqpKqWB4fbQTeB6oe6uCF8sN/YxCRvYyzNax38yEF3i0PBHi', TRUE, FALSE, '2025-12-04 07:24:51.648', '2025-12-04 07:24:51.648', 'candidate'),
    (3, 'tanaka@gmail.com', 'tanaka', 'Tanakaaa', '$2b$12$LKJJzl6aHBC3UmPYdk8q9utp8Y9NMWa7Hi.G5oyFi9WrE3UKuZK..', TRUE, FALSE, '2025-12-04 07:53:09.330', '2025-12-04 07:53:09.330', 'employer'),
    (4, 'fikri2@gmail.com', 'fikri2', 'mfikriab2', '$2b$12$8IZjtoe0t/GaU6zFFqyWjeFZFsSwVhdvPMAcU3BPOUlvkx9SMGsgO', TRUE, FALSE, '2025-12-04 20:31:31.661', '2025-12-04 20:31:31.661', 'candidate'),
    (5, 'fikri3@gmail.com', 'fikri3', 'mfikriab3', '$2b$12$UU2bMhco7xAYVFabmuWirexPUKOXZRAQQKTwm1jYi5d7SoAkoHLXG', TRUE, FALSE, '2025-12-04 20:33:15.168', '2025-12-04 20:33:15.168', 'candidate'),
    (6, 'fikri10@gmail.com', 'fikri10', 'mfikriab10', '$2b$12$ctnENaiqw6eG6waEzeLKAuqH09mxlXeFoemtAMb3E6wGhRcpfhsRe', TRUE, FALSE, '2025-12-05 07:56:34.927', '2025-12-05 07:56:34.927', 'candidate'),
    (7, 'test@gmail.com', 'test', 'testing', '$2b$12$80UGvw7tNWvJLEDFKpbqUesNOBuzHZctOrdP5uwN7BBTBkKVA9B8K', TRUE, FALSE, '2025-12-06 14:11:23.592', '2025-12-06 14:11:23.592', 'candidate'),
    (8, 'employer@superjob.com', 'employer1', 'Employer 1', '$2b$12$vB2kyE4my4CtjNCLywfTDewa8rVzM1n3rqR/P4Abed/3zXbwfrTYq', TRUE, FALSE, '2025-12-07 15:38:05.306', '2025-12-07 15:38:05.306', 'employer'),
    (9, 'candidate@superjob.com', 'candidate1', 'Candidate 1', '$2b$12$XKTDMGCNGiPGxhS7plMv8.qRC3.ug44/Hfhm6S.G3pv2mlqS8tq3e', TRUE, FALSE, '2025-12-07 15:39:01.644', '2025-12-07 15:39:01.644', 'candidate'),
    (10, 'bintangmm15@gmail.com', 'terpaksa56', 'Bintang Amirul Mukminin', '$2b$12$Mvdgj84yTcrqNF8BW.xqZuP2UskWorbxKtLT7DuMEqXibuKbhabm6', TRUE, FALSE, '2025-12-08 10:19:02.345', '2025-12-08 10:19:02.345', 'candidate'),
    (1001, 'john.doe@example.com', 'johndoe', 'John Doe', '$2b$12$dummyhashforcandidates', TRUE, FALSE, '2024-01-01 00:00:00', '2024-01-01 00:00:00', 'candidate'),
    (1002, 'jane.smith@example.com', 'janesmith', 'Jane Smith', '$2b$12$dummyhashforcandidates', TRUE, FALSE, '2024-01-01 00:00:00', '2024-01-01 00:00:00', 'candidate'),
    (1003, 'bob.wilson@example.com', 'bobwilson', 'Bob Wilson', '$2b$12$dummyhashforcandidates', TRUE, FALSE, '2024-01-01 00:00:00', '2024-01-01 00:00:00', 'candidate'),
    (1004, 'alice.johnson@example.com', 'alicejohnson', 'Alice Johnson', '$2b$12$dummyhashforcandidates', TRUE, FALSE, '2024-01-01 00:00:00', '2024-01-01 00:00:00', 'candidate'),
    (1005, 'charlie.brown@example.com', 'charliebrown', 'Charlie Brown', '$2b$12$dummyhashforcandidates', TRUE, FALSE, '2024-01-01 00:00:00', '2024-01-01 00:00:00', 'candidate')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT JOBS ==========
    op.execute("""
    INSERT INTO jobs (id, job_code, title, department, location, employment_type, experience_level, education_requirement, salary_range, status, description, requirements, responsibilities, created_by, created_at, updated_at) VALUES
    (1, 'UIUX-001', 'UI/UX Designer', 'Design', 'Jakarta', 'Full-time', 'Mid-level', 'S1/D4', 'Rp 10-15 juta', 'open', '', '', '', NULL, '2025-12-07 04:40:27.079', '2025-12-07 04:40:27.079'),
    (2, 'UIUX-002', 'Senior UI/UX Designer', 'Design', 'Bandung', 'Full-time', 'Senior', 'S1/D4', 'Rp 15-20 juta', 'open', '', '', '', NULL, '2025-12-07 04:40:27.079', '2025-12-07 04:40:27.079'),
    (3, 'DEV-001', 'Backend Developer', 'Engineering', 'Jakarta', 'Full-time', 'Mid-level', 'S1/D4', 'Rp 12-18 juta', 'open', '', '', '', NULL, '2025-12-07 04:40:27.079', '2025-12-07 04:40:27.079'),
    (4, 'JOB_1765189217126', 'System Analis', 'IT/Communication', 'Surabaya', 'Full-Time', 'Fresh Graduate', '3000000-6000000', '', 'closed', 'Generated content based on System Analis in IT/Communication industry - Job Description. This is a sample generated description for the position.', 'Relevant degree or experience Strong problem-solving skills Good communication abilities Team player', 'Analyze business requirements Develop solutions Collaborate with team Monitor performance', 10, '2025-12-08 10:20:17.599', '2025-12-08 10:20:17.599'),
    (5, 'JOB_1765189558027', 'System Analis', 'IT/Communication', 'Surabaya', 'Full-Time', 'Fresh Graduate', '', '', 'closed', 'Generated content based on System Analis in IT/Communication industry - Job Description. This is a sample generated description for the position.', 'Relevant degree or experience Strong problem-solving skills Good communication abilities Team player', 'Analyze business requirements Develop solutions Collaborate with team Monitor performance', 10, '2025-12-08 10:25:58.450', '2025-12-08 10:25:58.450'),
    (6, 'JOB_1765189828636', 'System Analis', 'IT/Communication', 'Surabaya', 'Part-Time', 'Fresh Graduate', '200000-4000000', '', 'closed', 'Generated content based on System Analis in IT/Communication industry - Job Description. This is a sample generated description for the position.', 'Relevant degree or experience Strong problem-solving skills Good communication abilities Team player', 'Analyze business requirements Develop solutions Collaborate with team Monitor performance', 10, '2025-12-08 10:30:29.176', '2025-12-08 10:30:29.176'),
    (7, 'JOB_1765190347772', 'Front End', 'IT/Communication', 'Jakarta', 'Full-Time', 'Fresh Graduate', '', '', 'closed', 'Generated content based on Front End in IT/Communication industry - Job Description. This is a sample generated description for the position.', 'Relevant degree or experience Strong problem-solving skills Good communication abilities Team player', 'Analyze business requirements Develop solutions Collaborate with team Monitor performance', 10, '2025-12-08 10:39:08.206', '2025-12-08 10:39:08.206'),
    (8, 'JOB_1765190523752', 'System Analis', 'IT/Communication', 'Jakarta Selatan', 'Full-Time', 'Fresh Graduate', '400000-2000000', '', 'closed', 'Generated content based on  in IT/Communication industry - Job Description. This is a sample generated description for the position.', 'Relevant degree or experience Strong problem-solving skills Good communication abilities Team player', 'Analyze business requirements Develop solutions Collaborate with team Monitor performance', 10, '2025-12-08 10:42:04.179', '2025-12-08 10:42:04.179')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT APPLICATIONS ==========
    op.execute("""
    INSERT INTO applications (id, job_id, candidate_id, candidate_name, candidate_email, candidate_phone, candidate_linkedin, candidate_cv_url, candidate_education, candidate_experience_years, current_company, current_position, expected_salary, notice_period, application_status, interview_stage, interview_scheduled_by, interview_date, fit_score, skill_score, experience_score, overall_score, source, tags, notes, created_at, updated_at, applied_date) VALUES
    (1, 1, 1001, 'Walter Gibson', 'walter@gmail.com', '6281234567890', '', 'https://storage/cv_walter.pdf', 'SMA/SMK', 3, 'TechCorp', 'Junior Designer', 'Rp 12 juta', '1 month', 'applied', NULL, NULL, NULL, 78.50, 75.00, 80.00, 77.80, 'job_portal', NULL, '', '2025-12-07 04:40:27.120', '2025-12-07 04:40:27.120', '2025-12-07'),
    (2, 1, 1002, 'Lewis Redenson', 'lewis@gmail.com', '6281234567891', 'linkedin.com/in/lewis', 'https://storage/cv_lewis.pdf', 'S1/D4', 5, 'DesignStudio', 'UI Designer', 'Rp 14 juta', 'Immediate', 'qualified', 'first_interview', 'by: A', NULL, 85.00, 88.00, 82.00, 85.00, 'linkedin', NULL, '', '2025-12-07 04:40:27.120', '2025-12-11 07:39:31.849', '2025-12-07'),
    (3, 1, 1003, 'Delsey Tam', 'delsey@gmail.com', '6281234567892', 'linkedin.com/in/delsey', 'https://storage/cv_delsey.pdf', 'S1/D4', 4, 'CreativeAgency', 'UX Designer', 'Rp 13 juta', '2 weeks', 'qualified', 'second_interview', NULL, NULL, 82.50, 85.00, 80.00, 82.50, 'referral', NULL, '', '2025-12-07 04:40:27.120', '2025-12-07 04:40:27.120', '2025-12-07'),
    (4, 1, 1004, 'Alejandro Holland', 'alejandro@gmail.com', '6281234567893', '', 'https://storage/cv_alejandro.pdf', 'D3', 2, 'StartupXYZ', 'Design Intern', 'Rp 10 juta', 'Immediate', 'contract_signed', 'contract_signed', NULL, NULL, 70.00, 72.00, 68.00, 70.00, 'job_portal', NULL, '', '2025-12-07 04:40:27.120', '2025-12-07 04:40:27.120', '2025-12-07'),
    (5, 1, 1005, 'Rose Foster', 'rose@gmail.com', '6281234567894', '', 'https://storage/cv_rose.pdf', 'S1/D4', 1, 'FreshGraduate', 'Fresh Graduate', 'Rp 9 juta', 'Immediate', 'not_qualified', NULL, NULL, NULL, 65.00, 60.00, 62.00, 62.30, 'job_portal', NULL, '', '2025-12-07 04:40:27.120', '2025-12-07 04:40:27.120', '2025-12-07'),
    (101, 1, 1001, 'John Doe', 'john.doe@example.com', '628123456789', 'linkedin.com/in/johndoe', 'https://storage/cv_john.pdf', 'S1/D4', 5, 'TechCompany', 'Software Engineer', 'Rp 15 juta', '1 month', 'applied', NULL, NULL, NULL, 85.50, 90.00, 80.00, 85.17, 'linkedin', NULL, '', '2024-01-10 00:00:00', '2024-01-10 00:00:00', '2024-01-10'),
    (102, 1, 1002, 'Jane Smith', 'jane.smith@example.com', '628123456788', 'linkedin.com/in/janesmith', 'https://storage/cv_jane.pdf', 'S1/D4', 3, 'StartupXYZ', 'Backend Developer', 'Rp 12 juta', '2 weeks', 'qualified', 'first_interview', NULL, NULL, 92.30, 95.00, 85.00, 90.77, 'job_portal', NULL, '', '2024-01-11 00:00:00', '2024-01-11 00:00:00', '2024-01-11'),
    (103, 2, 1003, 'Bob Wilson', 'bob.wilson@example.com', '628123456787', 'linkedin.com/in/bobwilson', 'https://storage/cv_bob.pdf', 'S1/D4', 2, 'WebDev Co', 'Frontend Developer', 'Rp 10 juta', '1 month', 'applied', NULL, NULL, NULL, 78.90, 85.00, 70.00, 77.97, 'referral', NULL, '', '2024-01-12 00:00:00', '2024-01-12 00:00:00', '2024-01-12')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT CANDIDATE_SCORE ==========
    op.execute("""
    INSERT INTO candidate_score (id, application_id, job_id, candidate_name, fit_score, skill_score, experience_score, education_score, reasons, updated_at) VALUES
    (1, 101, 1, 'John Doe', 85.50, 90.00, 80.00, 75.00, '{"experience": "5+ years", "skill_match": "Excellent Python skills"}', '2025-12-02 00:57:14.717'),
    (2, 102, 1, 'Jane Smith', 92.30, 95.00, 85.00, 90.00, '{"experience": "7+ years", "skill_match": "Fullstack developer"}', '2025-12-02 00:57:14.717'),
    (3, 103, 1, 'Bob Wilson', 78.90, 85.00, 70.00, 80.00, '{"experience": "3+ years", "skill_match": "Good backend skills"}', '2025-12-02 00:57:14.717')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT APPLICATION_HISTORY ==========
    op.execute("""
    INSERT INTO application_history (id, application_id, changed_by, previous_status, new_status, previous_stage, new_stage, change_reason, change_date) VALUES
    (1, 2, 1, 'qualified', 'qualified', 'first_interview', 'first_interview', 'Shortlisted', '2025-12-11 07:39:31.953')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT CHAT_THREADS ==========
    op.execute("""
    INSERT INTO chat_threads (id, application_id, job_id, employer_id, candidate_id, candidate_name, job_title, last_message, last_message_at, unread_count_employer, unread_count_candidate, created_at, updated_at) VALUES
    ('550e8400-e29b-41d4-a716-446655440000', 101, 1, 1, 1001, 'John Doe', 'Software Engineer', 'hallo', '2025-12-11 16:26:30.264', 5, 1, '2025-12-05 01:53:52.172', '2025-12-11 16:26:30.619'),
    ('550e8400-e29b-41d4-a716-446655440001', 102, 1, 1, 1002, 'Jane Smith', 'Backend Developer', 'Thanks for applying!', '2024-01-14 14:20:00.000', 0, 1, '2025-12-05 01:53:52.172', '2025-12-05 01:53:52.172'),
    ('550e8400-e29b-41d4-a716-446655440002', 103, 2, 2, 1003, 'Bob Wilson', 'Frontend Developer', 'Please send your portfolio', '2024-01-13 09:15:00.000', 1, 1, '2025-12-05 01:53:52.172', '2025-12-05 01:53:52.172'),
    ('abe51f39-7c7d-448f-ab01-29aa057a0174', 1, 1, 8, 9, NULL, NULL, 'tes lagi', '2025-12-13 02:15:36.439', 24, 35, '2025-12-07 23:26:26.774', '2025-12-13 02:15:36.443')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT MESSAGES (Complete) ==========
    op.execute("""
    INSERT INTO messages (id, thread_id, sender_id, receiver_id, sender_name, receiver_name, message_text, status, is_ai_suggestion, ai_suggestions, created_at) VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '550e8400-e29b-41d4-a716-446655440000', 1001, 1, 'John Doe', 'HR Manager', 'Hello, I applied for the Software Engineer position', 'seen', 0, NULL, '2024-01-15 09:00:00.000'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', '550e8400-e29b-41d4-a716-446655440000', 1, 1001, 'HR Manager', 'John Doe', 'Thanks for applying! When are you available for interview?', 'seen', 0, NULL, '2024-01-15 09:30:00.000'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', '550e8400-e29b-41d4-a716-446655440000', 1001, 1, 'John Doe', 'HR Manager', 'I am available tomorrow after 2 PM', 'delivered', 0, NULL, '2024-01-15 10:30:00.000'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', '550e8400-e29b-41d4-a716-446655440000', 1, 1001, 'HR Manager', 'John Doe', 'Perfect! Let schedule at 3 PM tomorrow', 'sent', 0, NULL, '2024-01-15 10:35:00.000'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', '550e8400-e29b-41d4-a716-446655440001', 1, 1002, 'HR Manager', 'Jane Smith', 'Hi Jane, we received your application', 'seen', 0, NULL, '2024-01-14 14:00:00.000'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', '550e8400-e29b-41d4-a716-446655440001', 1002, 1, 'Jane Smith', 'HR Manager', 'Thank you! Looking forward to hearing back', 'delivered', 0, NULL, '2024-01-14 14:20:00.000'),
    ('bb4fbc56-5761-445f-9917-aac0f2c2bb41', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Test', 'sent', 0, NULL, '2025-12-07 23:35:21.273'),
    ('b4a56393-159f-427d-94e6-59ae7594967f', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'Iya halo?', 'sent', 0, NULL, '2025-12-07 23:38:17.917'),
    ('83d90e20-9712-4558-9504-5d70ea58ca28', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Gimana hari ini?', 'sent', 0, NULL, '2025-12-08 00:11:44.492'),
    ('0bb9da0a-6438-4e50-96b1-dbecc230c60f', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'Baik hari ini', 'sent', 0, NULL, '2025-12-08 00:12:07.042'),
    ('8ebcfa8a-3b1e-404d-b241-21bb202df6fe', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'test', 'sent', 0, NULL, '2025-12-08 01:18:19.165'),
    ('e6f336bb-0011-4f88-80a1-282069a9969f', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'tes di web', 'sent', 0, NULL, '2025-12-08 12:11:09.883'),
    ('b785a7e1-a26d-470d-b5cb-62da28b3b68d', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'tes di web 2', 'sent', 0, NULL, '2025-12-08 12:54:45.838'),
    ('321326cd-6c13-4f71-b2d2-ebfd195c512e', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'tes di web 3', 'sent', 0, NULL, '2025-12-08 13:12:03.515'),
    ('62b8e3b5-4509-48e3-ad71-44196638057b', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'halo', 'sent', 0, NULL, '2025-12-08 13:41:11.689'),
    ('406ec356-0890-432f-ab01-a16b04302a58', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Tes', 'sent', 0, NULL, '2025-12-08 14:57:39.549'),
    ('53e81d5a-fc38-4f89-b384-ecc1c74aca7e', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Bisa Anda jelaskan lebih detail?', 'sent', 0, NULL, '2025-12-08 15:15:40.142'),
    ('9a0822db-fe9f-4108-a0e5-82f66a0ae317', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'Apakah ada pertanyaan lain?', 'sent', 0, NULL, '2025-12-08 15:16:29.969'),
    ('f74fba33-4745-4b28-b98e-922c2499dd76', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Tes', 'sent', 0, NULL, '2025-12-08 15:18:40.894'),
    ('2d3446e1-64e4-4f30-b927-65cc13aa1460', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'Halo', 'sent', 0, NULL, '2025-12-09 03:20:06.169'),
    ('70d85be7-ff0f-4f44-8fc0-06afbb332d3d', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Ya?', 'sent', 0, NULL, '2025-12-09 03:20:16.595'),
    ('fb203644-9de2-4ab9-8641-ae883f5fea5c', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'Tes', 'sent', 0, NULL, '2025-12-09 03:46:54.912'),
    ('d29860f2-81ff-4f9a-beb4-5494e0384e76', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'tes', 'sent', 0, NULL, '2025-12-09 03:58:25.406'),
    ('359663ae-c504-461b-b17d-4d3cef2a8225', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'cek', 'sent', 0, NULL, '2025-12-09 04:09:14.477'),
    ('0de32f61-2b2b-48a8-9d22-213774a7a012', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'aaa', 'sent', 0, NULL, '2025-12-10 08:39:26.423'),
    ('7b1efcc3-2a57-492f-b5be-3d7b6369ac48', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'tes', 'sent', 0, NULL, '2025-12-10 08:46:46.512'),
    ('9a163f00-15d6-4660-b32c-462faada14f7', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available for interview tomorrow?', 'sent', 0, NULL, '2025-12-10 08:54:50.764'),
    ('18af644f-02ac-415c-87d9-286473364cd5', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available for right now ?', 'sent', 0, NULL, '2025-12-10 08:56:25.992'),
    ('b926cf22-92f6-4a44-8cde-bd44e566b353', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-10 09:26:36.780'),
    ('b0dd8c25-e468-4c1f-b573-b308b8b8223e', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-10 09:28:03.612'),
    ('fefb44ea-3a5e-4b4d-8630-2a2436ada116', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-10 14:57:57.047'),
    ('37465427-67d2-4ec0-af5c-0f148ffebfdc', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-10 14:59:43.195'),
    ('b8b5e9f1-fc8e-43a5-8802-dbda8f124a7a', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-11 04:17:07.578'),
    ('68e5be4e-e866-4761-867a-605747d803e4', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-11 04:18:59.672'),
    ('1fc43918-b636-451b-a0bd-1744b545dd42', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-11 07:06:53.276'),
    ('4cdd4f29-3504-40f1-b14c-d165092b9015', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-11 07:07:28.714'),
    ('a136fe25-a429-42e8-97fd-ce30ad6be546', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-11 07:39:43.415'),
    ('96cd24f5-f003-48d7-b6a5-55860c75ed82', '550e8400-e29b-41d4-a716-446655440000', 1, 1001, 'System Administrator', 'John Doe', 'Hi, can we schedule an interview?', 'sent', 0, NULL, '2025-12-11 07:40:10.615'),
    ('7fa13d23-3a49-40b5-9db8-96ca0529c5cb', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-11 07:59:33.349'),
    ('4d7bc256-4567-4e1c-b2ee-306524775ce5', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-11 09:08:53.363'),
    ('f0392831-e395-4040-a55d-276c130ba97a', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hi John, are you available currently ?', 'sent', 0, NULL, '2025-12-11 09:09:11.072'),
    ('623448a7-f81b-4472-866c-b4126979d61c', '550e8400-e29b-41d4-a716-446655440000', 1001, 1, 'John Doe', 'Software Engineer', 'gg', 'sent', 0, NULL, '2025-12-11 09:14:43.308'),
    ('2f4106b3-cdcf-422e-b0ea-7150628423bd', '550e8400-e29b-41d4-a716-446655440000', 1001, 1, 'John Doe', 'Software Engineer', 'gg', 'sent', 0, NULL, '2025-12-11 09:14:44.930'),
    ('47cdce4d-6fbb-4b3a-8e6e-49c64852d35e', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'Hello!', 'sent', 0, NULL, '2025-12-11 20:58:01.141'),
    ('0036e139-616e-4eb3-8f09-29249c95c152', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'When are you available?', 'sent', 0, NULL, '2025-12-11 20:58:07.301'),
    ('cd4a7e61-eeec-43e0-8356-fa4c671629f3', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'Hello!', 'sent', 0, NULL, '2025-12-11 20:58:40.321'),
    ('b3ee1cab-e591-42a2-8e23-4396248cbff7', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'Thanks for applying!', 'sent', 0, NULL, '2025-12-11 20:58:43.592'),
    ('8738915c-6607-4984-9d0e-5254fc404ce9', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'send', 'sent', 0, NULL, '2025-12-11 14:09:43.189'),
    ('966a3a9b-1dfb-437d-8b33-e1822a28722b', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'send 2', 'sent', 0, NULL, '2025-12-11 14:11:06.781'),
    ('71274f98-06e3-4ccd-ac74-c331c62e06e6', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', 'Employer 1', 'tes', 'sent', 0, NULL, '2025-12-11 14:14:07.717'),
    ('dee702a4-6546-4b53-add4-898408c75753', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'tes message to employer', 'sent', 0, NULL, '2025-12-11 14:19:12.740'),
    ('f80f63ac-4edf-4dd7-a611-e7d98718b767', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'halo test', 'sent', 0, NULL, '2025-12-11 14:23:55.728'),
    ('caf3f9f6-ab38-498a-810f-401487005525', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'Hello!', 'sent', 0, NULL, '2025-12-11 14:35:41.003'),
    ('243c2cb0-32e6-431e-a615-f4dfde31e44a', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'test hanya test', 'sent', 0, NULL, '2025-12-11 14:35:51.956'),
    ('2bdbf00e-738d-442b-bdab-db85c611725e', '550e8400-e29b-41d4-a716-446655440000', 1001, 1, 'John Doe', 'Software Engineer', 'hallo', 'sent', 0, NULL, '2025-12-11 16:26:30.619'),
    ('ec8ea03e-3f61-443b-87ed-8c0bff2355a4', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'testt', 'sent', 0, NULL, '2025-12-12 01:41:26.187'),
    ('805b30d7-6d76-4c9d-8ba2-829fff70659a', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', '', 'halo', 'sent', 0, NULL, '2025-12-12 01:41:51.941'),
    ('0789b157-682b-4a92-bb1e-cf1eb3dba0ae', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'haloo', 'sent', 0, NULL, '2025-12-12 01:47:42.761'),
    ('3348e5a6-ce76-41df-b304-d4ac06c200fb', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'Tes send message', 'sent', 0, NULL, '2025-12-12 07:28:05.836'),
    ('c55155b2-4f57-4d44-acbf-00e754e65cd5', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'asd', 'sent', 0, NULL, '2025-12-12 07:32:03.515'),
    ('9effdee1-b44c-4d8e-88d3-eadb9db9337f', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', '', 'cek', 'sent', 0, NULL, '2025-12-12 07:48:24.860'),
    ('c4ee7082-0bbb-4641-8239-4bebf9f938a3', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', '', 'cek 2', 'sent', 0, NULL, '2025-12-12 07:48:40.779'),
    ('7cbdd073-43d0-4d32-b230-a66d822cd1e9', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'cek 3', 'sent', 0, NULL, '2025-12-12 08:13:22.757'),
    ('8e1e8659-3f94-4d0e-a26b-859203a8e138', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', '', 'tes', 'sent', 0, NULL, '2025-12-12 08:14:03.710'),
    ('0eed892c-6f6d-46fe-bd83-00c522207bc2', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'tes\naaa', 'sent', 0, NULL, '2025-12-12 10:35:48.170'),
    ('ef390bd9-fccb-4092-92ba-d48a7b8b5f15', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 8, 9, 'Employer 1', '', 'test new line\nnew line', 'sent', 0, NULL, '2025-12-12 10:36:36.383'),
    ('113a9e20-0270-46dc-8d0c-2397aa7f7f4e', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'tes swagger', 'sent', 0, NULL, '2025-12-13 02:07:14.572'),
    ('4d684a70-e8bd-4bd5-a150-fa895f9bee26', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'tes kirim message', 'sent', 0, NULL, '2025-12-13 02:12:56.420'),
    ('05ed5e36-5181-451a-9dc4-cd7469fe2061', 'abe51f39-7c7d-448f-ab01-29aa057a0174', 9, 8, 'Candidate 1', 'Employer', 'tes lagi', 'sent', 0, NULL, '2025-12-13 02:15:36.439')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT ACTIVITY_LOGS (Complete) ==========
    op.execute("""
    INSERT INTO activity_logs (id, employer_id, type, title, subtitle, meta_data, job_id, applicant_id, message_id, timestamp, is_read) VALUES
    (1, 1, 'status_update', 'Update status pelamar', 'Status Lewis Redenson berubah: qualified -> qualified', '{"body": "Status Lewis Redenson berubah: qualified -> qualified", "description": "Status Lewis Redenson berubah: qualified -> qualified", "cta": "/jobs/1/applications/2", "role": "employer", "associated_data": {"job_id": "1", "applicant_id": 2, "from_status": "qualified", "to_status": "qualified", "source": "status_update", "ip_address": "192.168.1.50", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}}', 1, 2, NULL, '2025-12-11 14:39:32.218', FALSE),
    (2, 1, 'new_message', 'Pesan baru', 'System Administrator → John Doe: Hi, can we schedule an interview?', '{"body": "Hi, can we schedule an interview?", "description": "System Administrator → John Doe: Hi, can we schedule an interview?", "cta": "/chats/550e8400-e29b-41d4-a716-446655440000", "role": "admin", "associated_data": {"thread_id": "550e8400-e29b-41d4-a716-446655440000", "job_id": "1", "applicant_id": 1001, "sender": "System Administrator", "receiver": "John Doe", "source": "chat", "ip_address": "10.0.0.1", "user_agent": "SuperJob-Admin/1.0"}}', 1, 1001, '96cd24f5-f003-48d7-b6a5-55860c75ed82', '2025-12-11 14:40:10.802', FALSE),
    (3, 8, 'new_message', 'Pesan baru', 'Employer 1 → Candidate 1: Hello!', '{"body": "Hello!", "description": "Employer 1 → Candidate 1: Hello!", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "employer", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Employer 1", "receiver": "Candidate 1", "source": "chat", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}}', NULL, 9, '47cdce4d-6fbb-4b3a-8e6e-49c64852d35e', '2025-12-11 20:58:01.217', FALSE),
    (4, 8, 'new_message', 'Pesan baru', 'Employer 1 → Candidate 1: When are you available?', '{"body": "When are you available?", "description": "Employer 1 → Candidate 1: When are you available?", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "employer", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Employer 1", "receiver": "Candidate 1", "source": "chat", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}}', NULL, 9, '0036e139-616e-4eb3-8f09-29249c95c152', '2025-12-11 20:58:07.368', FALSE),
    (5, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: Hello!', '{"body": "Hello!", "description": "Candidate 1 → Employer 1: Hello!", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "203.189.142.55", "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile Safari/604.1"}}', NULL, 9, 'cd4a7e61-eeec-43e0-8356-fa4c671629f3', '2025-12-11 20:58:40.573', FALSE),
    (6, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: Thanks for applying!', '{"body": "Thanks for applying!", "description": "Candidate 1 → Employer 1: Thanks for applying!", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "203.189.142.55", "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Mobile Safari/604.1"}}', NULL, 9, 'b3ee1cab-e591-42a2-8e23-4396248cbff7', '2025-12-11 20:58:43.657', FALSE),
    (7, 8, 'new_message', 'Pesan baru', 'Employer 1 → Candidate 1: send', '{"body": "send", "description": "Employer 1 → Candidate 1: send", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "employer", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Employer 1", "receiver": "Candidate 1", "source": "chat", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}}', NULL, 9, '8738915c-6607-4984-9d0e-5254fc404ce9', '2025-12-11 21:09:43.197', FALSE),
    (8, 8, 'new_message', 'Pesan baru', 'Employer 1 → Candidate 1: send 2', '{"body": "send 2", "description": "Employer 1 → Candidate 1: send 2", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "employer", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Employer 1", "receiver": "Candidate 1", "source": "chat", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}}', NULL, 9, '966a3a9b-1dfb-437d-8b33-e1822a28722b', '2025-12-11 21:11:06.791', FALSE),
    (9, 8, 'new_message', 'Pesan baru', 'Employer 1 → Candidate 1: tes', '{"body": "tes", "description": "Employer 1 → Candidate 1: tes", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "employer", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Employer 1", "receiver": "Candidate 1", "source": "chat", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/120.0.0.0"}}', NULL, 9, '71274f98-06e3-4ccd-ac74-c331c62e06e6', '2025-12-11 21:14:07.724', FALSE),
    (10, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: tes message to employer', '{"body": "tes message to employer", "description": "Candidate 1 → Employer 1: tes message to employer", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "203.189.142.55", "user_agent": "Mozilla/5.0 (Android 13; Mobile) Chrome/119.0.0.0"}}', NULL, 9, 'dee702a4-6546-4b53-add4-898408c75753', '2025-12-11 21:19:12.752', FALSE),
    (11, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: halo test', '{"body": "halo test", "description": "Candidate 1 → Employer 1: halo test", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "203.189.142.55", "user_agent": "Mozilla/5.0 (Android 13; Mobile) Chrome/119.0.0.0"}}', NULL, 9, 'f80f63ac-4edf-4dd7-a611-e7d98718b767', '2025-12-11 21:23:55.735', FALSE),
    (12, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: Hello!', '{"body": "Hello!", "description": "Candidate 1 → Employer 1: Hello!", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "203.189.142.55", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605.1.15"}}', NULL, 9, 'caf3f9f6-ab38-498a-810f-401487005525', '2025-12-11 21:35:41.013', FALSE),
    (13, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: test hanya test', '{"body": "test hanya test", "description": "Candidate 1 → Employer 1: test hanya test", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "203.189.142.55", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605.1.15"}}', NULL, 9, '243c2cb0-32e6-431e-a615-f4dfde31e44a', '2025-12-11 21:35:51.972', FALSE),
    (14, 8, 'new_applicant', 'Pelamar baru', 'John Doe melamar untuk Senior Software Engineer', '{"body": "Pelamar baru: John Doe", "description": "John Doe melamar untuk Senior Software Engineer", "cta": "/jobs/11111111-1111-1111-1111-111111111111/applications", "role": "candidate", "associated_data": {"job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 1001, "source": "application", "ip_address": "182.1.100.50", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/121.0"}}', NULL, 1001, NULL, '2025-12-12 08:41:26.194', FALSE),
    (15, 8, 'status_update', 'Update status pelamar', 'Status Jane Smith berubah: applied -> in_review', '{"body": "Status Jane Smith berubah: applied -> in_review", "description": "Status Jane Smith berubah: applied -> in_review", "cta": "/jobs/11111111-1111-1111-1111-111111111111/applications/102", "role": "employer", "associated_data": {"job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 1002, "from_status": "applied", "to_status": "in_review", "source": "status_update", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}}', NULL, 1002, NULL, '2025-12-12 08:41:51.949', FALSE),
    (16, 8, 'job_performance_alert', 'Peringatan performa lowongan', 'Junior Frontend Developer memiliki apply rate rendah: 2.5%', '{"body": "Apply rate rendah untuk Junior Frontend Developer", "description": "Junior Frontend Developer memiliki apply rate rendah: 2.5%", "cta": "/jobs/11111111-1111-1111-1111-111111111112/analytics", "role": "system", "associated_data": {"job_id": "11111111-1111-1111-1111-111111111112", "views": 200, "applicants": 5, "apply_rate": 2.5, "source": "cron_job", "ip_address": "127.0.0.1", "user_agent": "CronJob/refresh_job_performance"}}', NULL, NULL, NULL, '2025-12-12 08:47:42.774', FALSE),
    (17, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: Tes send message', '{"body": "Tes send message", "description": "Candidate 1 → Employer 1: Tes send message", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "203.189.142.55", "user_agent": "Mozilla/5.0 (Linux; Android 13) Chrome/120.0.0.0"}}', NULL, 9, '3348e5a6-ce76-41df-b304-d4ac06c200fb', '2025-12-12 14:28:05.896', FALSE),
    (18, 8, 'system_event', 'Event sistem', 'Backup database berhasil dilakukan', '{"body": "Backup database berhasil", "description": "Backup database harian berhasil dilakukan pada 12 Dec 2025 15:00 WIB", "cta": "/admin/system-logs", "role": "system", "associated_data": {"event_type": "backup_completed", "backup_size": "1.2GB", "duration": "45s", "source": "system", "ip_address": "10.0.0.5", "user_agent": "BackupService/2.0"}}', NULL, NULL, NULL, '2025-12-12 14:32:03.524', TRUE),
    (19, 8, 'new_message', 'Pesan baru', 'Employer 1 → Candidate 1: Kapan bisa interview?', '{"body": "Kapan bisa interview?", "description": "Employer 1 → Candidate 1: Kapan bisa interview?", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "employer", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Employer 1", "receiver": "Candidate 1", "source": "chat", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0"}}', NULL, 9, '9effdee1-b44c-4d8e-88d3-eadb9db9337f', '2025-12-12 14:48:24.870', FALSE),
    (20, 8, 'new_message', 'Pesan baru', 'Employer 1 → Candidate 1: Mohon konfirmasi jadwal', '{"body": "Mohon konfirmasi jadwal", "description": "Employer 1 → Candidate 1: Mohon konfirmasi jadwal", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "employer", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Employer 1", "receiver": "Candidate 1", "source": "chat", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0"}}', NULL, 9, 'c4ee7082-0bbb-4641-8239-4bebf9f938a3', '2025-12-12 14:48:40.787', FALSE),
    (21, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: Siap, saya available', '{"body": "Siap, saya available", "description": "Candidate 1 → Employer 1: Siap, saya available", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "203.189.142.55", "user_agent": "SuperJob-Mobile/3.0 (Android 13)"}}', NULL, 9, '7cbdd073-43d0-4d32-b230-a66d822cd1e9', '2025-12-12 15:13:22.764', FALSE),
    (22, 8, 'new_message', 'Pesan baru', 'Employer 1 → Candidate 1: Interview besok jam 10', '{"body": "Interview besok jam 10", "description": "Employer 1 → Candidate 1: Interview besok jam 10", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "employer", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Employer 1", "receiver": "Candidate 1", "source": "chat", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}}', NULL, 9, '8e1e8659-3f94-4d0e-a26b-859203a8e138', '2025-12-12 15:14:03.718', FALSE),
    (23, 3, 'new_applicant', 'Pelamar baru', 'Alice Johnson melamar untuk UI/UX Designer', '{"body": "Pelamar baru: Alice Johnson", "description": "Alice Johnson melamar untuk UI/UX Designer", "cta": "/jobs/11111111-1111-1111-1111-111111111115/applications", "role": "candidate", "associated_data": {"job_id": "11111111-1111-1111-1111-111111111115", "applicant_id": 1004, "source": "application", "ip_address": "114.125.200.30", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) Safari/605.1.15"}}', NULL, 1004, NULL, '2025-12-12 17:35:48.300', FALSE),
    (24, 3, 'status_update', 'Update status pelamar', 'Status Alice Johnson berubah: applied -> qualified', '{"body": "Status Alice Johnson berubah: applied -> qualified", "description": "Status Alice Johnson berubah: applied -> qualified", "cta": "/jobs/11111111-1111-1111-1111-111111111115/applications", "role": "employer", "associated_data": {"job_id": "11111111-1111-1111-1111-111111111115", "applicant_id": 1004, "from_status": "applied", "to_status": "qualified", "source": "status_update", "ip_address": "202.150.80.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}}', NULL, 1004, NULL, '2025-12-12 17:36:36.395', FALSE),
    (25, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: tes swagger', '{"body": "tes swagger", "description": "Candidate 1 → Employer 1: tes swagger", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "127.0.0.1", "user_agent": "Swagger-UI/5.0"}}', NULL, 9, '113a9e20-0270-46dc-8d0c-2397aa7f7f4e', '2025-12-13 09:07:14.582', FALSE),
    (26, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: tes kirim message', '{"body": "tes kirim message", "description": "Candidate 1 → Employer 1: tes kirim message", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "127.0.0.1", "user_agent": "Swagger-UI/5.0"}}', NULL, 9, '4d684a70-e8bd-4bd5-a150-fa895f9bee26', '2025-12-13 09:12:56.426', FALSE),
    (27, 8, 'new_message', 'Pesan baru', 'Candidate 1 → Employer 1: tes lagi', '{"body": "tes lagi", "description": "Candidate 1 → Employer 1: tes lagi", "cta": "/chats/abe51f39-7c7d-448f-ab01-29aa057a0174", "role": "candidate", "associated_data": {"thread_id": "abe51f39-7c7d-448f-ab01-29aa057a0174", "job_id": "11111111-1111-1111-1111-111111111111", "applicant_id": 9, "sender": "Candidate 1", "receiver": "Employer 1", "source": "chat", "ip_address": "127.0.0.1", "user_agent": "Swagger-UI/5.0"}}', NULL, 9, '05ed5e36-5181-451a-9dc4-cd7469fe2061', '2025-12-13 09:15:36.447', FALSE)
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT JOB_POSTINGS (for Job Quality Score, Dashboard, Job Performance API) ==========
    # employer_id merujuk ke users.id: 8 = employer@superjob.com, 3 = tanaka@gmail.com
    op.execute("""
    INSERT INTO job_postings (id, employer_id, title, description, salary_min, salary_max, salary_currency, skills, location, employment_type, experience_level, education, benefits, contact_url, status, created_at, updated_at) VALUES
    ('11111111-1111-1111-1111-111111111111', 8, 'Senior Software Engineer', 'Kami mencari Senior Software Engineer berpengalaman untuk bergabung dengan tim kami. Kandidat ideal memiliki pengalaman minimal 5 tahun dalam pengembangan aplikasi web menggunakan Python, FastAPI, dan PostgreSQL. Anda akan bertanggung jawab untuk merancang arsitektur sistem, melakukan code review, dan mentoring junior developer.', 15000000, 25000000, 'IDR', '["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "Redis", "AWS"]', 'Jakarta, Indonesia', 'full_time', 'senior', 'S1 Teknik Informatika atau setara', 'BPJS, THR, Remote Working, Training Budget', 'https://superjob.com/careers/senior-engineer', 'published', '2025-12-10 10:00:00', '2025-12-10 10:00:00'),
    ('11111111-1111-1111-1111-111111111112', 8, 'Junior Frontend Developer', 'Posisi entry-level untuk Fresh Graduate yang ingin memulai karir sebagai Frontend Developer. Persyaratan: memahami HTML, CSS, JavaScript, dan React.js. Akan diberikan training dan mentoring.', 6000000, 9000000, 'IDR', '["JavaScript", "React", "HTML", "CSS", "Git"]', 'Bandung, Indonesia', 'full_time', 'junior', 'D3/S1 Teknik Informatika', 'BPJS, THR, WFH 2x seminggu', 'https://superjob.com/careers/junior-frontend', 'published', '2025-12-11 09:00:00', '2025-12-11 09:00:00'),
    ('11111111-1111-1111-1111-111111111113', 8, 'Product Manager', 'Mencari Product Manager dengan pengalaman minimal 3 tahun untuk memimpin pengembangan produk digital. Bertanggung jawab untuk roadmap produk, koordinasi dengan tim engineering dan design.', 20000000, 35000000, 'IDR', '["Product Strategy", "Agile", "Data Analysis", "User Research", "Jira"]', 'Jakarta, Indonesia', 'full_time', 'mid', 'S1 Semua Jurusan', 'BPJS, THR, Stock Options, Remote Working', 'https://superjob.com/careers/pm', 'published', '2025-12-12 08:00:00', '2025-12-12 08:00:00'),
    ('11111111-1111-1111-1111-111111111114', 8, 'DevOps Engineer', 'DevOps Engineer untuk mengelola infrastruktur cloud dan CI/CD pipeline.', 18000000, 28000000, 'IDR', '["AWS", "Docker", "Kubernetes", "Terraform", "GitHub Actions"]', 'Remote', 'full_time', 'mid', 'S1 Teknik Informatika', 'BPJS, THR, 100% Remote', NULL, 'draft', '2025-12-13 10:00:00', '2025-12-13 10:00:00'),
    ('11111111-1111-1111-1111-111111111115', 3, 'UI/UX Designer', 'UI/UX Designer kreatif untuk merancang pengalaman pengguna yang luar biasa. Portfolio wajib dilampirkan.', 12000000, 18000000, 'IDR', '["Figma", "Adobe XD", "User Research", "Prototyping", "Design System"]', 'Surabaya, Indonesia', 'full_time', 'mid', 'S1 DKV atau setara', 'BPJS, THR, Flexible Hours', 'https://designco.com/careers', 'published', '2025-12-14 09:00:00', '2025-12-14 09:00:00'),
    ('11111111-1111-1111-1111-111111111116', 3, 'Data Analyst', 'Data Analyst untuk menganalisis data bisnis dan memberikan insight untuk pengambilan keputusan.', 10000000, 16000000, 'IDR', '["SQL", "Python", "Tableau", "Excel", "Statistics"]', 'Jakarta, Indonesia', 'full_time', 'junior', 'S1 Statistika/Matematika/Informatika', 'BPJS, THR', NULL, 'published', '2025-12-14 10:00:00', '2025-12-14 10:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT REMINDER_TASKS (for Reminder API) ==========
    # employer_id merujuk ke users.id: 8 = employer@superjob.com, 3 = tanaka@gmail.com
    op.execute("""
    INSERT INTO reminder_tasks (id, employer_id, job_id, candidate_id, task_title, task_type, redirect_url, due_at, status, created_at, updated_at) VALUES
    ('aaaa1111-aaaa-1111-aaaa-111111111111', 8, '11111111-1111-1111-1111-111111111111', NULL, 'Review lamaran John Doe', 'candidate', '/jobs/11111111-1111-1111-1111-111111111111/applications', '2025-12-16 10:00:00+07', 'pending', '2025-12-14 09:00:00', '2025-12-14 09:00:00'),
    ('aaaa1111-aaaa-1111-aaaa-111111111112', 8, '11111111-1111-1111-1111-111111111112', NULL, 'Jadwalkan interview kandidat', 'interview', '/jobs/11111111-1111-1111-1111-111111111112/interviews', '2025-12-17 14:00:00+07', 'pending', '2025-12-14 09:30:00', '2025-12-14 09:30:00'),
    ('aaaa1111-aaaa-1111-aaaa-111111111113', 8, NULL, NULL, 'Balas pesan dari kandidat', 'message', '/messages', '2025-12-15 16:00:00+07', 'pending', '2025-12-14 10:00:00', '2025-12-14 10:00:00'),
    ('aaaa1111-aaaa-1111-aaaa-111111111114', 8, '11111111-1111-1111-1111-111111111114', NULL, 'Publish job posting DevOps', 'job_update', '/jobs/11111111-1111-1111-1111-111111111114/edit', '2025-12-16 09:00:00+07', 'pending', '2025-12-14 11:00:00', '2025-12-14 11:00:00'),
    ('aaaa1111-aaaa-1111-aaaa-111111111115', 3, '11111111-1111-1111-1111-111111111115', NULL, 'Review portfolio designer', 'candidate', '/jobs/11111111-1111-1111-1111-111111111115/applications', '2025-12-18 10:00:00+07', 'pending', '2025-12-14 12:00:00', '2025-12-14 12:00:00'),
    ('aaaa1111-aaaa-1111-aaaa-111111111116', 8, NULL, NULL, 'Task sudah selesai', 'other', '/dashboard', NULL, 'done', '2025-12-10 09:00:00', '2025-12-12 15:00:00'),
    ('aaaa1111-aaaa-1111-aaaa-111111111117', 8, NULL, NULL, 'Task diabaikan', 'other', '/dashboard', NULL, 'ignored', '2025-12-08 09:00:00', '2025-12-11 10:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT REJECTION_REASONS ==========
    # created_by adalah Integer (FK ke users.id), gunakan 1 = admin@superjob.com
    op.execute("""
    INSERT INTO rejection_reasons (id, reason_code, reason_text, is_custom, is_active, created_by, created_at, updated_at) VALUES
    (1, 'SKILL_MISMATCH', 'Keterampilan tidak sesuai dengan kebutuhan posisi', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (2, 'EXPERIENCE_LACK', 'Pengalaman kerja kurang dari persyaratan minimum', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (3, 'SALARY_MISMATCH', 'Ekspektasi gaji tidak sesuai dengan budget perusahaan', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (4, 'CULTURE_FIT', 'Tidak cocok dengan budaya perusahaan', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (5, 'COMMUNICATION', 'Kemampuan komunikasi kurang baik', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (6, 'POSITION_FILLED', 'Posisi sudah terisi oleh kandidat lain', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (7, 'NO_RESPONSE', 'Kandidat tidak merespons undangan interview', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (8, 'DOCUMENT_INCOMPLETE', 'Dokumen yang diperlukan tidak lengkap', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (9, 'OVERQUALIFIED', 'Kandidat terlalu berkualifikasi untuk posisi ini', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (10, 'LOCATION_ISSUE', 'Lokasi tempat tinggal tidak sesuai', FALSE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00'),
    (11, 'OTHER', 'Alasan lainnya', TRUE, TRUE, 1, '2025-12-14 00:00:00', '2025-12-14 00:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT COMPANIES ==========
    # id adalah String/UUID, bukan Integer
    op.execute("""
    INSERT INTO companies (id, name, description, industry, website, location, logo_url, founded_year, employee_size, linkedin_url, twitter_url, instagram_url, created_at, updated_at) VALUES
    ('comp1111-1111-1111-1111-111111111111', 'PT SuperJob Indonesia', 'Platform rekrutmen terkemuka di Indonesia yang menghubungkan talenta dengan perusahaan terbaik.', 'Technology', 'https://superjob.id', 'Jakarta, Indonesia', 'https://superjob.id/logo.png', 2020, '50-200', 'https://linkedin.com/company/superjob', 'https://twitter.com/superjob', 'https://instagram.com/superjob', '2025-12-01 00:00:00', '2025-12-01 00:00:00'),
    ('comp1111-1111-1111-1111-111111111112', 'TechCorp Solutions', 'Perusahaan teknologi yang fokus pada pengembangan software enterprise dan solusi digital.', 'Technology', 'https://techcorp.com', 'Jakarta, Indonesia', 'https://techcorp.com/logo.png', 2015, '200-500', 'https://linkedin.com/company/techcorp', 'https://twitter.com/techcorp', 'https://instagram.com/techcorp', '2025-12-01 00:00:00', '2025-12-01 00:00:00'),
    ('comp1111-1111-1111-1111-111111111113', 'Creative Studio', 'Agensi kreatif yang menyediakan layanan desain, branding, dan marketing digital.', 'Creative Design', 'https://creativestudio.id', 'Bandung, Indonesia', 'https://creativestudio.id/logo.png', 2018, '10-50', 'https://linkedin.com/company/creativestudio', 'https://twitter.com/creativestudio', 'https://instagram.com/creativestudio', '2025-12-01 00:00:00', '2025-12-01 00:00:00'),
    ('comp1111-1111-1111-1111-111111111114', 'DataInsight Analytics', 'Konsultan data dan analytics yang membantu perusahaan membuat keputusan berbasis data.', 'Data Analytics', 'https://datainsight.co.id', 'Surabaya, Indonesia', 'https://datainsight.co.id/logo.png', 2019, '10-50', 'https://linkedin.com/company/datainsight', 'https://twitter.com/datainsight', 'https://instagram.com/datainsight', '2025-12-01 00:00:00', '2025-12-01 00:00:00'),
    ('comp1111-1111-1111-1111-111111111115', 'FinTech Sejahtera', 'Startup fintech yang menyediakan layanan payment gateway dan pinjaman digital.', 'Financial Services', 'https://fintechsejahtera.id', 'Jakarta, Indonesia', 'https://fintechsejahtera.id/logo.png', 2017, '50-200', 'https://linkedin.com/company/fintechsejahtera', 'https://twitter.com/fintechsejahtera', 'https://instagram.com/fintechsejahtera', '2025-12-01 00:00:00', '2025-12-01 00:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT COMPANY_REVIEWS ==========
    # id dan company_id adalah String/UUID
    op.execute("""
    INSERT INTO company_reviews (id, company_id, user_id, rating, title, pros, cons, position, employment_status, employment_duration, created_at, updated_at) VALUES
    ('review11-1111-1111-1111-111111111111', 'comp1111-1111-1111-1111-111111111111', 9, 5, 'Tempat kerja yang luar biasa!', 'Kultur kerja positif, benefit bagus, work-life balance', 'Kadang deadline ketat', 'Software Engineer', 'Current Employee', '2 years', '2025-12-10 10:00:00', '2025-12-10 10:00:00'),
    ('review11-1111-1111-1111-111111111112', 'comp1111-1111-1111-1111-111111111111', 1002, 4, 'Bagus untuk fresh graduate', 'Banyak kesempatan belajar, mentoring yang baik', 'Gaji entry level masih standar', 'Junior Developer', 'Former Employee', '1 year', '2025-12-11 14:00:00', '2025-12-11 14:00:00'),
    ('review11-1111-1111-1111-111111111113', 'comp1111-1111-1111-1111-111111111112', 1001, 4, 'Perusahaan teknologi profesional', 'Tim solid, project menarik, teknologi up-to-date', 'Proses birokrasi kadang lambat', 'Backend Developer', 'Current Employee', '3 years', '2025-12-12 09:00:00', '2025-12-12 09:00:00'),
    ('review11-1111-1111-1111-111111111114', 'comp1111-1111-1111-1111-111111111113', 1003, 5, 'Kreativitas tanpa batas', 'Kebebasan berkreasi, tim supportive, client bagus', 'Work from office wajib', 'UI Designer', 'Current Employee', '1.5 years', '2025-12-13 11:00:00', '2025-12-13 11:00:00'),
    ('review11-1111-1111-1111-111111111115', 'comp1111-1111-1111-1111-111111111114', 1004, 4, 'Cocok untuk pecinta data', 'Project data menantang, team skilled', 'Jam kerja panjang saat deadline', 'Data Analyst', 'Former Employee', '6 months', '2025-12-14 15:00:00', '2025-12-14 15:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT CANDIDATE_APPLICATION ==========
    # Struktur tabel: id (Integer), name, email, applied_position, status, applied_at
    op.execute("""
    INSERT INTO candidate_application (id, name, email, applied_position, status, applied_at) VALUES
    (1, 'John Doe', 'john.doe@example.com', 'Senior Software Engineer', 'applied', '2025-12-10 09:00:00'),
    (2, 'Jane Smith', 'jane.smith@example.com', 'Senior Software Engineer', 'qualified', '2025-12-11 10:00:00'),
    (3, 'Bob Wilson', 'bob.wilson@example.com', 'Junior Frontend Developer', 'in_review', '2025-12-12 08:30:00'),
    (4, 'Alice Johnson', 'alice.johnson@example.com', 'Product Manager', 'approved', '2025-12-08 11:00:00'),
    (5, 'Charlie Brown', 'charlie.brown@example.com', 'Senior Software Engineer', 'rejected', '2025-12-09 14:00:00'),
    (6, 'Diana Ross', 'diana.ross@example.com', 'UI/UX Designer', 'pending', '2025-12-13 09:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT NOTIFICATIONS ==========
    # Struktur: id, user_id, title, message, notification_type, data, thread_id, is_read, created_at
    op.execute("""
    INSERT INTO notifications (id, user_id, title, message, notification_type, data, thread_id, is_read, created_at) VALUES
    ('notif111-1111-1111-1111-111111111111', 8, 'Pelamar baru!', 'John Doe melamar untuk posisi Senior Software Engineer', 'new_applicant', '{"job_id": "11111111-1111-1111-1111-111111111111", "applicant_name": "John Doe"}', NULL, FALSE, '2025-12-10 09:00:00'),
    ('notif111-1111-1111-1111-111111111112', 8, 'Pelamar baru!', 'Jane Smith melamar untuk posisi Senior Software Engineer', 'new_applicant', '{"job_id": "11111111-1111-1111-1111-111111111111", "applicant_name": "Jane Smith"}', NULL, TRUE, '2025-12-11 10:00:00'),
    ('notif111-1111-1111-1111-111111111113', 8, 'Interview dijadwalkan', 'Interview dengan Jane Smith dijadwalkan untuk 16 Dec 2025', 'interview', '{"job_id": "11111111-1111-1111-1111-111111111111", "candidate_name": "Jane Smith", "date": "2025-12-16"}', NULL, FALSE, '2025-12-12 14:30:00'),
    ('notif111-1111-1111-1111-111111111114', 8, 'Pesan baru', 'Anda menerima pesan baru dari Candidate 1', 'message', '{"sender": "Candidate 1"}', 'abe51f39-7c7d-448f-ab01-29aa057a0174', FALSE, '2025-12-13 15:00:00'),
    ('notif111-1111-1111-1111-111111111115', 9, 'Status lamaran diperbarui', 'Lamaran Anda untuk Senior Software Engineer sedang direview', 'status', '{"job_id": "11111111-1111-1111-1111-111111111111", "new_status": "in_review"}', NULL, FALSE, '2025-12-11 11:00:00'),
    ('notif111-1111-1111-1111-111111111116', 3, 'Pelamar baru!', 'John Doe melamar untuk posisi UI/UX Designer', 'new_applicant', '{"job_id": "11111111-1111-1111-1111-111111111115", "applicant_name": "John Doe"}', NULL, FALSE, '2025-12-13 09:00:00'),
    ('notif111-1111-1111-1111-111111111117', 8, 'Reminder', 'Jangan lupa review lamaran minggu ini', 'reminder', '{"type": "weekly_reminder"}', NULL, TRUE, '2025-12-14 08:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT JOB_VIEWS ==========
    # Struktur: id (BigInt), job_id (Integer - FK ke jobs.id), viewed_at
    # Menggunakan job IDs dari tabel jobs (Integer 1-8)
    op.execute("""
    INSERT INTO job_views (id, job_id, viewed_at) VALUES
    (1, 1, '2025-12-10 08:00:00'),
    (2, 1, '2025-12-10 09:30:00'),
    (3, 1, '2025-12-10 10:15:00'),
    (4, 1, '2025-12-10 11:00:00'),
    (5, 2, '2025-12-11 08:00:00'),
    (6, 2, '2025-12-11 09:00:00'),
    (7, 3, '2025-12-12 08:30:00'),
    (8, 3, '2025-12-13 08:00:00'),
    (9, 4, '2025-12-13 10:00:00'),
    (10, 1, '2025-12-14 09:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT USER_DEVICES ==========
    # Struktur: id, user_id, device_token, device_type, is_active, created_at, updated_at
    op.execute("""
    INSERT INTO user_devices (id, user_id, device_token, device_type, is_active, created_at, updated_at) VALUES
    ('device11-1111-1111-1111-111111111111', 8, 'fcm_token_employer_8_chrome_windows', 'web', TRUE, '2025-12-01 00:00:00', '2025-12-15 10:00:00'),
    ('device11-1111-1111-1111-111111111112', 8, 'fcm_token_employer_8_samsung_android', 'android', TRUE, '2025-12-05 00:00:00', '2025-12-14 18:00:00'),
    ('device11-1111-1111-1111-111111111113', 9, 'fcm_token_candidate_9_iphone_ios', 'ios', TRUE, '2025-12-07 00:00:00', '2025-12-15 09:30:00'),
    ('device11-1111-1111-1111-111111111114', 3, 'fcm_token_employer_3_firefox_macos', 'web', TRUE, '2025-12-02 00:00:00', '2025-12-13 14:00:00'),
    ('device11-1111-1111-1111-111111111115', 1001, 'fcm_token_candidate_1001_xiaomi', 'android', FALSE, '2025-12-08 00:00:00', '2025-12-10 08:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # ========== INSERT INTERVIEW_FEEDBACKS ==========
    # application_id dan created_by adalah Integer (FK ke applications.id dan users.id)
    # Menggunakan application IDs: 2, 3, 4 yang sudah ada di applications table
    # created_by menggunakan employer users: 8 = employer@superjob.com, 3 = tanaka@gmail.com
    op.execute("""
    INSERT INTO interview_feedbacks (id, application_id, rating, feedback, created_by, created_at, updated_at) VALUES
    (gen_random_uuid(), 2, 5, 'Kandidat Lewis Redenson memiliki skill teknis yang sangat baik. Pengalaman 5 tahun sebagai UI Designer sangat relevan. Komunikasi lancar dan attitude positif.', 8, '2025-12-11 10:00:00', '2025-12-11 10:00:00'),
    (gen_random_uuid(), 3, 4, 'Delsey Tam menunjukkan kemampuan UX yang solid. Portfolio impressive. Sedikit kurang di presentation skill tapi overall bagus.', 8, '2025-12-12 14:30:00', '2025-12-12 14:30:00'),
    (gen_random_uuid(), 4, 3, 'Alejandro Holland masih junior tapi menunjukkan potensi. Perlu training lebih lanjut untuk design system.', 8, '2025-12-13 09:00:00', '2025-12-14 11:00:00'),
    (gen_random_uuid(), 101, 5, 'John Doe excellent candidate! Strong technical background, great communication, very professional. Highly recommended for the position.', 1, '2025-12-15 10:00:00', '2025-12-15 10:00:00'),
    (gen_random_uuid(), 102, 4, 'Jane Smith shows great potential. Good problem-solving skills. Needs improvement in system design concepts.', 1, '2025-12-15 11:30:00', '2025-12-15 14:00:00')
    ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    # Hapus semua data dalam urutan terbalik
    op.execute("DELETE FROM user_devices")
    op.execute("DELETE FROM job_views")
    op.execute("DELETE FROM notifications")
    op.execute("DELETE FROM candidate_application")
    op.execute("DELETE FROM company_reviews")
    op.execute("DELETE FROM companies")
    op.execute("DELETE FROM rejection_reasons")
    op.execute("DELETE FROM reminder_tasks")
    op.execute("DELETE FROM job_postings")
    op.execute("DELETE FROM activity_logs")
    op.execute("DELETE FROM messages")
    op.execute("DELETE FROM chat_threads")
    op.execute("DELETE FROM application_history")
    op.execute("DELETE FROM candidate_score")
    op.execute("DELETE FROM applications")
    op.execute("DELETE FROM jobs")
    op.execute("DELETE FROM users WHERE id >= 1001")
    op.execute("DELETE FROM users WHERE id <= 10")
    op.execute("DELETE FROM interview_feedbacks")
