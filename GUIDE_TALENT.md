# 📱 SuperJob API - Panduan untuk Talent (Job Seeker)

> **Dokumentasi lengkap API untuk kandidat/pencari kerja**

**Base URL:** `http://147.139.132.60:18001` (Production) atau `http://localhost:8000` (Local)

---

## 📑 Daftar Isi

1. [Struktur Folder Project](#1--struktur-folder-project)
2. [Overview](#2--overview)
3. [Getting Started](#3--getting-started)
4. [Authentication](#4--authentication)
5. [Profile Management](#5--profile-management)
6. [Job Discovery](#6--job-discovery)
7. [Job Bookmarks](#7--job-bookmarks)
8. [Job Application](#8--job-application)
9. [AI Interview](#9--ai-interview)
10. [Chat & Messaging](#10--chat--messaging)
11. [Notifications](#11--notifications)
12. [Company & Reviews](#12--company--reviews)
13. [Location Data](#13--location-data)
14. [Master Data](#14--master-data)
15. [Best Practices](#15--best-practices)
16. [Error Handling](#16--error-handling)
17. [Use Cases](#17--use-cases)

---

## 1. 📁 Struktur Folder Project

### Root Directory

```
superjob-api/
├── 📄 .env                    # Environment variables (credentials, API keys)
├── 📄 .env.example            # Template environment variables
├── 📄 requirements.txt        # Python dependencies
├── 📄 alembic.ini             # Database migration config
├── 📄 docker-compose.yml      # Docker orchestration
├── 📄 README.md               # Project documentation
├── 📄 CHANGELOG.md            # Version history
├── 📄 GUIDE_TALENT.md         # 📍 Dokumentasi ini
├── 📄 GUIDE_RECRUITER.md      # Dokumentasi untuk recruiter
├── 📁 app/                    # 🔥 Source code utama
├── 📁 docs/                   # Dokumentasi teknis tambahan
├── 📁 templates/              # Email templates
└── 📁 tests/                  # Unit & integration tests
```

### Folder `app/` - Source Code Utama

```
app/
├── 📄 main.py                 # Entry point FastAPI application
├── 📄 __init__.py
│
├── 📁 api/                    # API Layer (Routes & Endpoints)
│   ├── 📄 deps.py             # Dependency injection
│   ├── 📁 routers/            # 🔥 Semua API endpoints
│   │   ├── 📄 auth.py         # Authentication endpoints (login, register, OTP)
│   │   ├── 📄 user.py         # User profile endpoints
│   │   ├── 📄 job.py          # Job listing & search endpoints
│   │   ├── 📄 application.py  # Job application endpoints
│   │   ├── 📄 chat.py         # Chat messaging endpoints
│   │   ├── 📄 notification.py # Notification endpoints
│   │   ├── 📄 interview.py    # AI Interview session endpoints
│   │   ├── 📄 companies.py    # Company profile endpoints
│   │   ├── 📄 candidate.py    # Candidate scoring & ranking
│   │   ├── 📄 locations.py    # Province & regency data
│   │   └── 📄 ...             # (30 route files total)
│   └── 📁 ws/                 # WebSocket handlers
│       ├── 📄 chat_ws.py      # Real-time chat
│       └── 📄 activity_ws.py  # Real-time activity updates
│
├── 📁 core/                   # Core Configuration
│   ├── 📄 config.py           # App settings & environment
│   ├── 📄 security.py         # JWT, password hashing, auth guards
│   ├── 📄 limiter.py          # Rate limiting
│   └── 📄 ...
│
├── 📁 models/                 # SQLAlchemy ORM Models
│   ├── 📄 user.py             # User table model
│   ├── 📄 job.py              # Job posting model
│   ├── 📄 company.py          # Company model
│   ├── 📄 interview.py        # AI Interview session model
│   ├── 📄 candidate_info.py   # Candidate profile data
│   └── 📄 ...                 # (20 model files total)
│
├── 📁 schemas/                # Pydantic Schemas (Request/Response)
│   ├── 📄 user.py             # User request/response schemas
│   ├── 📄 auth.py             # Auth schemas (login, register, token)
│   ├── 📄 job.py              # Job schemas
│   ├── 📄 application.py      # Application schemas
│   └── 📄 ...                 # (35 schema files total)
│
├── 📁 services/               # 🔥 Business Logic Layer
│   ├── 📄 auth.py             # Authentication logic (57KB - largest)
│   ├── 📄 user_service.py     # User CRUD operations
│   ├── 📄 job_service.py      # Job search, filter, recommendations
│   ├── 📄 application_service.py  # Application submit & tracking
│   ├── 📄 chat_service.py     # Chat messaging logic
│   ├── 📄 interview_service.py    # AI Interview logic
│   ├── 📄 cv_extraction_service.py # CV parsing with AI
│   ├── 📄 notification_service.py # Push notifications
│   ├── 📄 email_service.py    # Email sending (OTP, notifications)
│   ├── 📄 openrouter_service.py   # AI/LLM integration
│   ├── 📄 stt_service.py      # Speech-to-Text (Deepgram)
│   ├── 📄 tts_service.py      # Text-to-Speech (Deepgram)
│   └── 📄 ...                 # (41 service files total)
│
├── 📁 db/                     # Database Layer
│   ├── 📄 session.py          # Database connection
│   ├── 📁 migrations/         # Alembic migrations
│   └── 📄 ...
│
├── 📁 utils/                  # Utility Functions
│   ├── 📄 helpers.py          # General helpers
│   └── 📄 ...
│
├── 📁 exceptions/             # Custom Exceptions
│   └── 📄 ...
│
└── 📁 cron/                   # Scheduled Jobs
    └── 📄 refresh_job_performance.py
```

### Folder `docs/` - Dokumentasi Teknis

```
docs/
├── 📄 authentication_api.md    # Detail endpoint auth
├── 📄 ai_interview_api.md      # AI Interview WebSocket docs
├── 📄 dashboard_metrics_api.md # Dashboard API docs
├── 📄 job_performance_api.md   # Job analytics docs
├── 📄 erd.md                   # Entity Relationship Diagram
└── 📄 *.puml                   # PlantUML sequence diagrams
```

### Penjelasan Layer Architecture

| Layer | Folder | Fungsi |
|-------|--------|--------|
| **API Layer** | `app/api/routers/` | Menerima HTTP request, validasi input, return response |
| **Service Layer** | `app/services/` | Business logic, data processing, external API calls |
| **Model Layer** | `app/models/` | Database table definitions (SQLAlchemy ORM) |
| **Schema Layer** | `app/schemas/` | Request/Response validation (Pydantic) |
| **Core Layer** | `app/core/` | Configuration, security, middleware |

### File Penting untuk Talent API

| File | Path | Deskripsi |
|------|------|-----------|
| 🔐 **Auth Service** | `app/services/auth.py` | Login, register, OTP, password reset |
| 👤 **User Service** | `app/services/user_service.py` | Profile CRUD, CV upload |
| 📋 **Job Service** | `app/services/job_service.py` | Job search, filter, recommendations |
| 📝 **Application Service** | `app/services/application_service.py` | Submit & track applications |
| 🤖 **Interview Service** | `app/services/interview_service.py` | AI Interview sessions |
| 💬 **Chat Service** | `app/services/chat_service.py` | Messaging with recruiters |
| 📄 **CV Extraction** | `app/services/cv_extraction_service.py` | AI-powered CV parsing |

---

## 2. 📌 Overview

### Apa yang Bisa Dilakukan Talent?

SuperJob API memungkinkan kandidat/pencari kerja untuk:

| Fitur | Deskripsi |
|-------|-----------|
| 🔐 **Register & Login** | Buat akun dengan email/password atau Google OAuth |
| 👤 **Profile Management** | Update profil, upload CV, atur preferensi kerja |
| 🔍 **Job Discovery** | Browse & filter lowongan, dapatkan rekomendasi AI |
| 📌 **Bookmarks** | Simpan lowongan favorit untuk nantinya |
| 📝 **Apply Jobs** | Submit lamaran dengan CV, cover letter, portfolio |
| 🤖 **AI Interview** | Latihan interview dengan AI interviewer |
| 💬 **Chat** | Komunikasi langsung dengan recruiter |
| 🔔 **Notifications** | Terima update status lamaran |

### Flow Umum Talent

```
Register → Verify Email → Complete Profile → Browse Jobs → Apply → Interview → Hired
    ↓           ↓              ↓               ↓           ↓         ↓
POST       POST            PUT            GET         POST     WebSocket
/auth/     /auth/          /users/        /jobs/      /applications  /ws/
talent/    verify-email    {user_id}                  /submit       interview
register
```

---

## 2. 🚀 Getting Started

### Base URL

| Environment | URL |
|-------------|-----|
| **Production** | `http://147.139.132.60:18001` |
| **Local Development** | `http://localhost:8000` |
| **Swagger Docs** | `{base_url}/docs` |

### Authentication Header

Semua endpoint (kecuali public) membutuhkan header:

```http
Authorization: Bearer <access_token>
```

### Token System

| Token | Expiry | Fungsi |
|-------|--------|--------|
| **Access Token** | 30 menit | Akses API |
| **Refresh Token** | 7 hari | Dapatkan access token baru |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

atau untuk validation error:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "type": "value_error"
    }
  ]
}
```

---

## 3. 🔐 Authentication

### 3.1 Register Talent

**`POST /auth/talent/register`**

> Registrasi akun talent baru dengan opsi upload CV.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Nama lengkap |
| `email` | string | ✅ | Email valid |
| `password` | string | ✅ | Password minimal 8 karakter |
| `cv_file` | file | ❌ | CV (PDF, max 10MB) |

**Request:**
```bash
curl -X POST "{base_url}/auth/talent/register" \
  -F "name=John Doe" \
  -F "email=john.doe@example.com" \
  -F "password=SecurePass123" \
  -F "cv_file=@/path/to/cv.pdf"
```

**Response (201):**
```json
{
  "message": "Registrasi berhasil. Selamat datang di SuperJob!",
  "user_id": 101,
  "email": "john.doe@example.com",
  "name": "John Doe",
  "role": "candidate"
}
```

---

### 3.2 Login Talent

**`POST /auth/talent/login`**

> Login dengan email dan password.

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 101,
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "role": "candidate"
  }
}
```

---

### 3.3 Google OAuth Login

**`POST /auth/talent/google`**

> Login/Register dengan Google OAuth.

**Request Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 101,
    "email": "john.doe@gmail.com",
    "name": "John Doe",
    "role": "candidate"
  },
  "is_new_user": true
}
```

---

### 3.4 Legacy Login (OAuth2)

**`POST /auth/token`**

> Endpoint legacy untuk backward compatibility.

**Content-Type:** `application/x-www-form-urlencoded`

| Field | Type | Description |
|-------|------|-------------|
| `username` | string | Email |
| `password` | string | Password |

**Response:** Sama dengan `/auth/talent/login`

---

### 3.5 Verify Email (OTP)

**`POST /auth/verify-email`**

> Verifikasi email dengan kode OTP.

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "otp_code": "123456"
}
```

**Response (200):**
```json
{
  "email": "john.doe@example.com",
  "otp_type": "Verification Email",
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

### 3.6 Resend OTP

**`POST /auth/resend-otp`**

> Kirim ulang kode OTP ke email.

**Request Body:**
```json
{
  "email": "john.doe@example.com"
}
```

**Response (200):**
```json
{
  "message": "OTP berhasil dikirim ke email Anda"
}
```

---

### 3.7 Forgot Password

**`POST /auth/forgot-password`**

> Request link reset password.

**Request Body:**
```json
{
  "email": "john.doe@example.com"
}
```

**Response (200):**
```json
{
  "message": "Jika email terdaftar, link reset password telah dikirim."
}
```

> ⚠️ **Security Note:** Response selalu sama untuk mencegah email enumeration.

---

### 3.8 Reset Password

**`POST /auth/reset-password`**

> Set password baru dengan token.

**Request Body:**
```json
{
  "token": "abc123...",
  "new_password": "NewSecurePass123"
}
```

---

### 3.9 Get Current User

**`GET /auth/me`** 🔒

> Dapatkan info user yang sedang login.

**Response (200):**
```json
{
  "id": 101,
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "role": "candidate",
  "is_verified": true,
  "is_active": true
}
```

---

### 3.10 Refresh Token

**`POST /auth/refresh`**

> Dapatkan access token baru.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 4. 👤 Profile Management

### 4.1 Get My Profile

**`GET /api/v1/users/profile/me`** 🔒

> Dapatkan profil lengkap user.

**Response (200):**
```json
{
  "id": 101,
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "phone": "+6281234567890",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "cv_url": "https://storage.superjob.com/cv/john_doe.pdf",
  "job_preferences": {
    "expected_salary": 15000000,
    "work_type": "hybrid",
    "locations": ["Jakarta", "Bandung"]
  },
  "experience": [...],
  "education": [...],
  "skills": ["Python", "React", "PostgreSQL"],
  "certifications": [...]
}
```

---

### 4.2 Update Profile

**`PUT /api/v1/users/{user_id}`** 🔒

> Update profil user (multipart/form-data untuk file upload).

**Content-Type:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `full_name` | string | Nama lengkap |
| `phone` | string | No. telepon (+62...) |
| `linkedin_url` | string | URL LinkedIn |
| `cv_file` | file | CV baru (PDF, max 10MB) |
| `job_preferences` | JSON | Preferensi kerja |
| `experience` | JSON | Pengalaman kerja |
| `education` | JSON | Pendidikan |
| `skills` | JSON | Array skills |
| `certifications` | JSON | Sertifikasi |

**Request Example:**
```bash
curl -X PUT "{base_url}/api/v1/users/101" \
  -H "Authorization: Bearer <token>" \
  -F "full_name=John Doe Updated" \
  -F "phone=+6281234567890" \
  -F 'job_preferences={"expected_salary":15000000,"work_type":"hybrid"}'
```

---

### 4.3 Update Password

**`PUT /api/v1/users/{user_id}/password`** 🔒

> Ubah password user.

**Request Body:**
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword456"
}
```

---

### 4.4 CV Scan & Extract

**`POST /api/v1/candidates/cv/scan`** 🔒

> Upload CV dan extract data dengan AI.

**Content-Type:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `cv_file` | file | CV (PDF, max 10MB) |

**Response (200):**
```json
{
  "extracted_data": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+6281234567890",
    "experience": [
      {
        "company": "Tech Corp",
        "position": "Software Engineer",
        "duration": "2020-2023"
      }
    ],
    "education": [...],
    "skills": ["Python", "JavaScript", "AWS"]
  }
}
```

---

## 5. 🔍 Job Discovery

### 5.1 Browse Jobs (Public)

**`GET /api/v1/jobs/public`**

> List lowongan untuk landing page (tanpa auth).

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `employment_type` | string | Filter: full_time, part_time, contract, internship |
| `working_type` | string | Filter: onsite, remote, hybrid |
| `title` | string | Search by job title |

**Response (200):**
```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Senior Software Engineer",
      "company_name": "PT SuperJob Indonesia",
      "location": "Jakarta",
      "employment_type": "full_time",
      "working_type": "hybrid",
      "salary_min": 15000000,
      "salary_max": 25000000
    }
  ],
  "total": 100
}
```

---

### 5.2 List Jobs (Authenticated)

**`GET /api/v1/jobs/`** 🔒

> List semua jobs dengan filter lengkap.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: published, closed |
| `department` | string | Filter by department |
| `employment_type` | string | full_time, part_time, contract, internship |
| `location` | string | Filter by location |
| `working_type` | string | onsite, remote, hybrid |
| `search` | string | Search by title |
| `salary_min` | int | Minimum salary |
| `salary_max` | int | Maximum salary |
| `company_id` | int | Filter by company |
| `is_bookmark` | bool | Only bookmarked jobs |
| `page` | int | Page number (default: 1) |
| `limit` | int | Items per page (default: 20, max: 100) |

**Response (200):**
```json
{
  "jobs": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "total_pages": 8
}
```

---

### 5.3 Job Detail

**`GET /api/v1/jobs/{job_id}`** 🔒

> Detail lengkap lowongan.

**Response (200):**
```json
{
  "id": 1,
  "title": "Senior Software Engineer",
  "description": "We are looking for...",
  "requirements": ["5+ years experience", "Python proficiency"],
  "responsibilities": ["Design systems", "Lead team"],
  "company": {
    "id": 1,
    "name": "PT SuperJob Indonesia",
    "logo_url": "https://...",
    "industry": "Technology"
  },
  "employment_type": "full_time",
  "working_type": "hybrid",
  "location": "Jakarta",
  "salary_min": 15000000,
  "salary_max": 25000000,
  "is_bookmarked": false,
  "has_applied": false,
  "similar_jobs": [...]
}
```

---

### 5.4 Get Available Filters

**`GET /api/v1/jobs/search/filters`** 🔒

> Dapatkan opsi filter yang tersedia.

**Response (200):**
```json
{
  "employment_types": ["full_time", "part_time", "contract", "internship"],
  "working_types": ["onsite", "remote", "hybrid"],
  "locations": ["Jakarta", "Bandung", "Surabaya"],
  "departments": ["Engineering", "Marketing", "HR"],
  "salary_ranges": [
    {"min": 0, "max": 5000000},
    {"min": 5000000, "max": 10000000}
  ]
}
```

---

### 5.5 Job Recommendations (AI)

**`GET /api/v1/jobs/recommendation/list`** 🔒

> Dapatkan rekomendasi job berdasarkan profil (AI-powered).

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10 | Items per page (1-50) |
| `page` | int | 1 | Page number |

**Response (200):**
```json
{
  "recommendations": [
    {
      "job": {
        "id": 1,
        "title": "Senior Software Engineer",
        ...
      },
      "match_score": 85,
      "match_reasons": [
        "Skills match: Python, React",
        "Experience level match",
        "Location preference match"
      ]
    }
  ],
  "total": 25,
  "page": 1
}
```

---

## 6. 📌 Job Bookmarks

### 6.1 Bookmark Job

**`POST /api/v1/jobs/{job_id}/bookmarks`** 🔒

> Simpan job ke bookmark.

**Response (200):**
```json
{
  "message": "Job berhasil di-bookmark",
  "job_id": 1
}
```

---

### 6.2 Remove Bookmark

**`DELETE /api/v1/jobs/{job_id}/bookmarks`** 🔒

> Hapus job dari bookmark.

**Response (200):**
```json
{
  "message": "Bookmark berhasil dihapus",
  "job_id": 1
}
```

---

### 6.3 List Bookmarked Jobs

Gunakan **`GET /api/v1/jobs/?is_bookmark=true`** 🔒

---

## 7. 📝 Job Application

### 7.1 Submit Application

**`POST /api/v1/applications/submit`** 🔒

> Submit lamaran kerja.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_id` | int | ✅ | ID job yang dilamar |
| `full_name` | string | ✅ | Nama lengkap |
| `whatsapp_number` | string | ✅ | No. WhatsApp (+62...) |
| `coverletter` | string | ❌ | Cover letter text |
| `location` | string | ❌ | Lokasi kandidat |
| `cv` | file | ❌ | CV (PDF) |
| `cv_link` | string | ❌ | Link CV (alternative) |
| `portfolio_file` | file | ❌ | Portfolio (PDF) |

**Request:**
```bash
curl -X POST "{base_url}/api/v1/applications/submit" \
  -H "Authorization: Bearer <token>" \
  -F "job_id=1" \
  -F "full_name=John Doe" \
  -F "whatsapp_number=+6281234567890" \
  -F "coverletter=I am excited to apply..." \
  -F "cv=@/path/to/cv.pdf"
```

**Response (201):**
```json
{
  "message": "Lamaran berhasil dikirim",
  "application_id": 123,
  "job_id": 1,
  "status": "applied"
}
```

---

### 7.2 Get Active Applications

**`GET /api/v1/applications/active`** 🔒

> Lamaran yang sedang dalam proses.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by job title atau company |
| `limit` | int | Items per page (default: 10) |
| `page` | int | Page number (default: 1) |

**Status Active:** `applied`, `viewed`, `qualified`, `interview`, `contract_proposal`

**Response (200):**
```json
{
  "applications": [
    {
      "id": 123,
      "job": {
        "id": 1,
        "title": "Senior Software Engineer",
        "company_name": "PT SuperJob Indonesia"
      },
      "status": "interview",
      "stage": "first_interview",
      "applied_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T14:00:00Z"
    }
  ],
  "total": 5,
  "page": 1
}
```

---

### 7.3 Get Application History

**`GET /api/v1/applications/history`** 🔒

> Riwayat lamaran yang sudah selesai.

**Status History:** `not_qualified`, `contract_signed`

---

### 7.4 Application Detail

**`GET /api/v1/applications/{application_id}`** 🔒

> Detail lamaran tertentu.

**Response (200):**
```json
{
  "id": 123,
  "job": {...},
  "status": "interview",
  "stage": "first_interview",
  "cv_url": "https://...",
  "coverletter": "I am excited...",
  "portfolio_url": "https://...",
  "applied_at": "2024-01-15T10:30:00Z",
  "history": [
    {
      "status": "applied",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "status": "interview",
      "timestamp": "2024-01-20T14:00:00Z",
      "note": "Scheduled for first interview"
    }
  ]
}
```

---

## 8. 🤖 AI Interview

### 8.1 Create Interview Session

**`POST /api/v1/interview/sessions`** 🔒

> Mulai sesi interview AI baru.

**Request Body:**
```json
{
  "position": "Software Engineer",
  "level": "Senior",
  "totalQuestions": 5,
  "type": "technical"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `position` | string | Posisi yang diinterview |
| `level` | string | Junior, Mid, Senior |
| `totalQuestions` | int | Jumlah pertanyaan |
| `type` | string | technical, behavioral |

**Response (200):**
```json
{
  "sessionId": 123,
  "status": "active"
}
```

---

### 8.2 List Interview Sessions

**`GET /api/v1/interview/sessions`** 🔒

> List semua sesi interview user.

**Response (200):**
```json
[
  {
    "id": 123,
    "status": "ended",
    "startedAt": "2024-01-15T10:30:00Z",
    "endedAt": "2024-01-15T11:00:00Z",
    "config": {
      "position": "Software Engineer",
      "level": "Senior",
      "totalQuestions": 5,
      "type": "technical"
    },
    "evaluation": {
      "score": 85,
      "feedback": "Excellent performance...",
      "status": "completed"
    }
  }
]
```

---

### 8.3 WebSocket Interview

**URL:** `ws://{host}/api/v1/ws/interview/{session_id}?token={jwt_token}`

#### Client → Server Events:

```json
// Send text answer
{"type": "USER_TEXT_ANSWER", "payload": {"message": "My answer is..."}}

// Send audio chunk (base64)
{"type": "USER_AUDIO_CHUNK", "payload": {"chunk": "<base64>", "isFirst": true}}

// End audio
{"type": "USER_AUDIO_END", "payload": {}}

// End interview early
{"type": "HANGUP", "payload": {}}
```

#### Server → Client Events:

```json
// Introduction
{"type": "INTRO", "payload": {"message": "Welcome to your interview..."}}

// Question
{"type": "QUESTION", "payload": {"message": "Can you explain...", "questionNumber": 1}}

// Feedback
{"type": "FEEDBACK", "payload": {"message": "Great answer..."}}

// End
{"type": "END_INTERVIEW", "payload": {"message": "Thank you...", "sessionId": 123}}
```

---

### 8.4 End Session

**`POST /api/v1/interview/sessions/{session_id}/end`** 🔒

> Akhiri sesi interview secara manual.

---

### 8.5 Get Interview History

**`GET /api/v1/interview/history/{session_id}`** 🔒

> Review lengkap sesi interview.

---

## 9. 💬 Chat & Messaging

### 9.1 Get WebSocket Info

**`GET /api/v1/chat/websocket-info`** 🔒

> Dapatkan info koneksi WebSocket.

---

### 9.2 List Chat Threads

**`GET /api/v1/chat/list`** 🔒

> List semua percakapan.

**Response (200):**
```json
{
  "threads": [
    {
      "id": "thread-123",
      "participant": {
        "id": 8,
        "name": "HR Manager",
        "company": "PT SuperJob Indonesia"
      },
      "job": {
        "id": 1,
        "title": "Senior Software Engineer"
      },
      "last_message": {
        "content": "Please send your portfolio",
        "sent_at": "2024-01-20T14:00:00Z"
      },
      "unread_count": 2
    }
  ]
}
```

---

### 9.3 Get Chat History

**`GET /api/v1/chat/{thread_id}`** 🔒

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 100 | Max messages |
| `order` | string | asc | asc atau desc |

---

### 9.4 Send Message

**`POST /api/v1/chat/{thread_id}/messages`** 🔒

**Request Body:**
```json
{
  "content": "Thank you for the opportunity..."
}
```

---

### 9.5 Mark as Read

**`PATCH /api/v1/chat/{thread_id}/read`** 🔒

---

### 9.6 AI Reply Suggestions

**`POST /api/v1/chat/{thread_id}/ai-suggestions`** 🔒

> Dapatkan saran balasan dari AI.

**Response (200):**
```json
{
  "suggestions": [
    "Thank you for the update. I am available for the interview.",
    "I appreciate the opportunity. Could you please share more details?",
    "Thank you. I will prepare the requested documents."
  ]
}
```

---

## 10. 🔔 Notifications

### 10.1 Get Notifications

**`GET /api/v1/notifications/`** 🔒

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Max notifications |
| `offset` | int | 0 | Offset pagination |

**Response (200):**
```json
{
  "notifications": [
    {
      "id": "notif-123",
      "type": "status_update",
      "title": "Status Lamaran Diperbarui",
      "message": "Lamaran Anda untuk posisi Software Engineer telah dikualifikasi",
      "is_read": false,
      "created_at": "2024-01-20T14:00:00Z",
      "data": {
        "application_id": 123,
        "job_id": 1
      }
    }
  ],
  "total_unread": 5
}
```

---

### 10.2 Mark as Read

**`POST /api/v1/notifications/{notification_id}/read`** 🔒

---

### 10.3 Mark All as Read

**`POST /api/v1/notifications/read-all`** 🔒

---

## 11. 🏢 Company & Reviews

### 11.1 Get Company Profile

**`GET /api/v1/companies/{company_id}`** 🔒

**Response (200):**
```json
{
  "id": 1,
  "name": "PT SuperJob Indonesia",
  "industry": "Technology",
  "description": "Leading job platform...",
  "website": "https://superjob.com",
  "location": "Jakarta",
  "founded_year": 2020,
  "employee_size": "51-200",
  "logo_url": "https://...",
  "banner_url": "https://...",
  "social_media": {
    "linkedin": "https://linkedin.com/company/superjob",
    "instagram": "@superjob.id"
  }
}
```

---

### 11.2 Get Company Reviews

**`GET /api/v1/companies/{company_id}/reviews`**

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `sort` | string | newest, oldest, highest, lowest |
| `department` | string | Filter by department |
| `employment_duration` | string | less_than_1_year, 1_to_2_years, more_than_2_years |
| `employment_status` | string | current, former |
| `page` | int | Page number |
| `limit` | int | Items per page |

---

### 11.3 Get Rating Summary

**`GET /api/v1/companies/{company_id}/rating-summary`**

**Response (200):**
```json
{
  "average_rating": 4.2,
  "total_reviews": 150,
  "rating_breakdown": {
    "5": 80,
    "4": 40,
    "3": 20,
    "2": 7,
    "1": 3
  },
  "category_ratings": {
    "work_life_balance": 4.0,
    "career_growth": 4.3,
    "compensation": 3.8,
    "culture": 4.5
  }
}
```

---

## 12. 📍 Location Data

### 12.1 Get Provinces

**`GET /api/v1/locations/provinces`**

---

### 12.2 Get Regencies

**`GET /api/v1/locations/provinces/{province_id}/regencies`**

---

## 13. 📊 Master Data

### 13.1 Work Types

**`GET /api/v1/master/work-types/`**

---

### 13.2 Employment Types

**`GET /api/v1/master/employment-types/`**

---

### 13.3 Employment Types (Select Options)

**`GET /api/v1/master/employment-types/select-options`**

---

### 13.4 Application Statuses

**`GET /api/v1/master/application-statuses/`**

---

## 14. 💡 Best Practices

### Profile Optimization

| Tip | Impact |
|-----|--------|
| ✅ Lengkapi semua field profil | Higher match score |
| ✅ Upload CV berkualitas (PDF) | Better AI extraction |
| ✅ Tambahkan skills relevan | More recommendations |
| ✅ Update pengalaman kerja | Accurate matching |
| ✅ Set job preferences | Targeted recommendations |

### Job Application

| Tip | Impact |
|-----|--------|
| ✅ Tulis cover letter khusus | Stand out |
| ✅ Attach portfolio | Show work |
| ✅ Apply di jam kerja | Faster response |
| ✅ Respond cepat ke chat | Good impression |

### AI Interview

| Tip | Impact |
|-----|--------|
| ✅ Latihan dengan berbagai level | Better preparation |
| ✅ Review feedback AI | Improve answers |
| ✅ Coba mode technical & behavioral | Comprehensive prep |

---

## 15. ❗ Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized (token invalid/expired) |
| 403 | Forbidden (wrong role) |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Token expired` | Access token expired | Refresh token or re-login |
| `User not found` | Invalid user ID | Check user ID |
| `Permission denied` | Wrong role | Use correct login endpoint |
| `Already applied` | Duplicate application | Check existing applications |

---

## 16. 📋 Use Cases

### Use Case 1: Register → Apply

```bash
# 1. Register
POST /auth/talent/register

# 2. Verify Email
POST /auth/verify-email

# 3. Login
POST /auth/talent/login

# 4. Update Profile
PUT /api/v1/users/{user_id}

# 5. Browse Jobs
GET /api/v1/jobs/

# 6. Apply
POST /api/v1/applications/submit

# 7. Track Status
GET /api/v1/applications/active
```

### Use Case 2: AI Interview Practice

```bash
# 1. Create Session
POST /api/v1/interview/sessions

# 2. Connect WebSocket
ws://host/api/v1/ws/interview/{session_id}

# 3. Answer Questions (via WebSocket)
# 4. Review Results
GET /api/v1/interview/history/{session_id}
```

### Use Case 3: Chat with Recruiter

```bash
# 1. Check New Messages
GET /api/v1/chat/list

# 2. Read Thread
GET /api/v1/chat/{thread_id}

# 3. Get AI Suggestions
POST /api/v1/chat/{thread_id}/ai-suggestions

# 4. Send Reply
POST /api/v1/chat/{thread_id}/messages

# 5. Mark as Read
PATCH /api/v1/chat/{thread_id}/read
```

---

> 📝 **Last Updated:** Februari 2026
