# Changelog - Superjob API

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-01-19

### Detail Versi 0.4.0

#### ✨ Fitur Baru: Public Jobs & Advanced Management

- **Deskripsi:**
  - **Public Jobs API:** Added `GET /api/v1/jobs/public` for landing page with flattened company info.
  - **User Management:** Added support for updating and deleting company users.
  - **Regional Data:** Added new list of provinces and regencies.
  - **Impact:** Enables landing page integration and full company team management.

#### 🔒 Security & Validation

- **Deskripsi:**
  - **SQL Injection Hardening:** Refactored `get_public_jobs` to use strict parameterized queries.
  - **Parameter Validation:** Added `Literal` validation for `employment_type` and `working_type`.
  - **Admin Protection:** Prevented assigning the system Admin role (ID 1) in company user management.
  - **Impact:** Eliminates security warnings and ensures data integrity for the public API.

#### 📝 Documentation

- **Deskripsi:**
  - **Swagger Update:** Enriched documentation for public jobs and company user endpoints with explicit parameter options.
  - **Impact:** Improved developer experience for frontend integration.

---

## [0.3.0] - 2026-01-19

### Detail Versi 0.3.0

#### ✨ Fitur Baru: Talent Auth & Profile Enchancemet

- **Deskripsi:**
  - **Talent Registration:** Implemented dedicated talent registration and auth flow.
  - **Google OAuth Talent:** Enhanced talent authentication with proper error handling and structure.
  - **User Profile:** Added `company_id` to the `/auth/me` response.
  - **Impact:** Fully enables talent/candidate side of the platform.

#### 🗃️ Database & Storage

- **Deskripsi:**
  - **Candidate Info:** Added migration for `candidate_info` table to support user CV storage.
  - **Technical Note:** Centralized password hashing and updated JWT decoding mechanism.
  - **Migration Required:** ✅ Yes (`0023_create_candidate_info_table`)
  - **Impact:** Supports rich candidate profiles and persistent storage for CVs.

#### 🚀 Peningkatan Performa & Monitoring

- **Deskripsi:**
  - **Activity Log:** Enhanced activity logs with date range filtering support.
  - **Impact:** Better audit capability and monitoring.

---

## [0.2.3] - 2026-01-13

### Detail Versi 0.2.3

#### 🐛 Bug Fix: Render Database Connectivity

- **Deskripsi:**
  - **Render SSL & Parameter Compatibility:** Migrated company user endpoints to synchronous `psycopg2` to resolve `sslmode` and `channel_binding` errors on Render.
  - **Impact:** Fixed production database connectivity issues for company management features.
  - **Technical Notes:** Aligns with working authentication patterns and bypasses `asyncpg` parameter limitations.
  - **Migration Required:** ❌ No

---

## [0.2.2] - 2026-01-13

### Detail Versi 0.2.2

#### ✨ Fitur Baru: Company User Management

- **Deskripsi:**
  - **New Endpoints:** Added `GET /companies/{company_id}/users` (listing) and `POST /companies/{company_id}/users` (creation).
  - **Capabilities:** Supports pagination, searching, filtering by role, and sorting for company members.
  - **Automation:** `POST` endpoint automatically links new users to the target company.
  - **Impact:** Allows Company Admins to manage their team members within a isolated company scope.

#### 🔒 Security Fix: RBAC Permission Mapping

- **Deskripsi:**
  - **Fix:** Corrected the permission check in `create_company_user` to use the existing `user.create` code instead of a non-existent one.
  - **Strict Access:** Explicitly enforced that only users with the Admin role (or Superusers) can create company members.
  - **Impact:** Resolves the authorization "trust issue" and ensures proper access control.

#### 🐛 Bug Fix: Schema Validation

- **Deskripsi:**
  - **Fix:** Resolved an `AttributeError` in the `CorporateRegisterRequest` schema's `nib_document_url` validator.
  - **Technical Note:** Switched from string-prefix checking to native Pydantic `HttpUrl.scheme` validation.
  - **Impact:** Prevents registration crashes when processing Vercel Blob URLs.

#### 🐛 Bug Fix: SQLAlchemy Mapper Ambiguity

- **Deskripsi:**
  - **Fix:** Resolved a "multiple foreign key paths" error in the `User.roles` and `Role.users` relationships.
  - **Technical Note:** Implemented explicit `primaryjoin` and `secondaryjoin` conditions to handle the dual foreign keys (`user_id` and `assigned_by`) in the `user_roles` table.
  - **Impact:** Prevents runtime errors when accessing user-role relationships.

#### 📝 Documentation: API Specification

- **Deskripsi:**
  - **Update:** Standardized Swagger/OpenAPI descriptions for all company-related endpoints.
  - **Authorization Docs:** Added explicit notes about Admin role requirements and company membership checks.
  - **Impact:** Improved developer experience and API clarity.

---

## [0.2.1] - 2026-01-12

### Detail Versi 0.2.1

#### ☁️ Cloud Storage & V2 Registration

- **Deskripsi:**
  - **Vercel Blob Integration:** Replaced multipart file upload with `nib_document_url` URL handling.
  - **Feature:** Frontend now uploads directly to Vercel Blob, backend stores the URL.
  - **Cleanup Logic:** Implemented automated deletion of orphaned NIB files if company registration fails.
  - **Impact:** Reduced server load and improved upload reliability.

#### ♻️ Code Refactor & Consolidation

- **Deskripsi:**
  - **Consolidation:** Merged corporate registration logic into `auth.py`, replacing the experimental `auth_v2.py`.
  - **Endpoint Update:** Renamed and standardized endpoint to `/auth/register/company`.
  - **Payload:** Switched to flat JSON structure (`CorporateRegisterRequest`) for simpler frontend integration.
  - **Impact:** Simplified codebase and easier API maintenance.

#### 🗃️ Database

- **Deskripsi:**
  - **Migration Required:** ✅ Yes (`0022_add_nib_document_url_to_companies`)
  - **Changes:** Added `nib_document_url` (Text, Nullable) to `companies` table.
  - **Impact:** Supports storing long URLs for Vercel Blob assets.

#### ⚠️ Known Issues

- **Vercel Blob Dependency Conflict:**
  - **Issue:** Unable to install `vercel_blob` SDK directly due to dependency conflicts.
  - **Workaround:** Implemented fallback logic using `httpx` for deleting NIB documents from Vercel Blob.
  - **Status:** Temporary workaround; requires resolution of package dependencies for full SDK support.

---

## [0.2.0] - 2026-01-12

### Detail Versi 0.2.0

#### ✨ Unified Company & Admin Registration

- **Deskripsi:**
  - **New Endpoint:** `/auth/register/company`
  - **Feature:** Added capability to create both company and admin user in a single atomic transaction.
  - **Schema Validation:** Improved registration request schema with nested `company` and `user` entities.
  - **Impact:** Cleaner registration flow for companies and improved data integrity.

#### 🐛 Bug Fix Auth Registration

- **Deskripsi:**
  - **Fix Name:** `/auth/register` endpoint validation
  - **Fix:** Fixed broken registration endpoint and integrated proper `role_id` validation.
  - **Changes:** Added `role_id` to `UserCreate` request body and `UserResponse`.
  - **Impact:** Prevents registration with non-existent roles and supports Role-Based Access Control (RBAC).

#### 🚀 Peningkatan Performa

- **Deskripsi:**
  - **Optimization:** Refactored registration logic to use Common Table Expressions (CTE).
  - **Efficiency:** Reduced database round-trips from 3 to 1 for multiple inserts.
  - **Impact:** Significantly faster registration process and reduced database load.

#### 🗃️ Database

- **Deskripsi:**
  - **Migration Required:** ✅ Yes
  - **Changes:**
    - Implemented `users_companies` association table for many-to-many relationship.
    - Added `default_role_id` column support in registration.
  - **Impact:** Allows linking multiple users to a company and better role management.

#### 📝 Documentation

- **Deskripsi:**
  - **Swagger Update:** Added detailed descriptions and example payloads for registration endpoints.
  - **Impact:** Improved API discoverability and ease of use for developers.

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
