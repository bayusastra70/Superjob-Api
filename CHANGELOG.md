# Changelog - Superjob API

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup placeholder

---

## [0.1.0] - 2025-01-08

### Detail Versi 0.1.0

#### 🚀 Initial Setup & Configuration

- **Deskripsi:**
  - **FastAPI Project Setup:** Inisialisasi project FastAPI dengan struktur folder modular
  - **Database Configuration:** Setup PostgreSQL dengan SQLAlchemy ORM
  - **API Documentation:** Auto-generated OpenAPI (Swagger) documentation di `/docs`
  - **Environment Configuration:** Setup `.env` untuk database credentials dan configuration
  - **CORS Configuration:** Setup CORS middleware untuk frontend integration
  - **Authentication Base:** Setup JWT token authentication system untuk job seekers dan employers

#### 🛠️ Technical Setup

- **Deskripsi:**
  - **Alembic Migration:** Setup database migration tool untuk version control
  - **Pydantic Models:** Setup request/response validation schemas
  - **Router Structure:** Modular router setup untuk maintainability
  - **Error Handling:** Global exception handler dan custom error responses
  - **Logging:** Setup structured logging dengan Loguru
  - **File Upload:** Setup untuk CV/Resume upload ke cloud storage

#### 📊 Database Schema

- **Deskripsi:**
  - **Jobs Table:** Schema untuk job listings
    - Fields: id, title, description, company_id, location, salary_range, job_type, created_at, updated_at
  - **Companies Table:** Schema untuk employer profiles
    - Fields: id, name, description, website, logo_url, created_at
  - **Users Table:** Schema untuk job seekers
    - Fields: id, email, hashed_password, full_name, phone, resume_url, created_at
  - **Applications Table:** Schema untuk job applications
    - Fields: id, job_id, user_id, status, cover_letter, applied_at

---
