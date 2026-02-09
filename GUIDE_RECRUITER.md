# 🏢 SuperJob API - Panduan untuk Recruiter (Employer)

> **Dokumentasi lengkap API untuk recruiter/employer/perusahaan**

**Base URL:** `http://147.139.132.60:18001` (Production) atau `http://localhost:8000` (Local)

---

## 📑 Daftar Isi

1. [Struktur Folder Project](#1--struktur-folder-project)
2. [Overview](#2--overview)
3. [Getting Started](#3--getting-started)
4. [Authentication](#4--authentication)
5. [Company Profile](#5--company-profile)
6. [Team Management](#6--team-management)
7. [Job Posting](#7--job-posting)
8. [Job Performance](#8--job-performance)
9. [Application Management](#9--application-management)
10. [Interview Feedback](#10--interview-feedback)
11. [Rejection Reasons](#11--rejection-reasons)
12. [Chat & Messaging](#12--chat--messaging)
13. [Notifications](#13--notifications)
14. [Dashboard & Activities](#14--dashboard--activities)
15. [Reminders](#15--reminders)
16. [RBAC - Role Management](#16--rbac---role-management)
17. [AI Features](#17--ai-features)
18. [Best Practices](#18--best-practices)
19. [Error Handling](#19--error-handling)
20. [Use Cases](#20--use-cases)

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
├── 📄 GUIDE_TALENT.md         # Dokumentasi untuk talent
├── 📄 GUIDE_RECRUITER.md      # 📍 Dokumentasi ini
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
│   │   ├── 📄 auth.py         # Authentication (login, register)
│   │   ├── 📄 companies.py    # 🏢 Company profile & users
│   │   ├── 📄 team_member.py  # 👥 Team management
│   │   ├── 📄 job.py          # 📋 Job posting & management
│   │   ├── 📄 application.py  # 📝 Application review & status
│   │   ├── 📄 candidate.py    # Candidate scoring & ranking
│   │   ├── 📄 interview_feedback.py  # Interview feedback
│   │   ├── 📄 rejection_reason.py    # Rejection reasons
│   │   ├── 📄 chat.py         # 💬 Chat messaging
│   │   ├── 📄 notification.py # 🔔 Notifications
│   │   ├── 📄 activities.py   # Activity log & dashboard
│   │   ├── 📄 reminders.py    # ⏰ Task reminders
│   │   ├── 📄 role_base_access_control.py  # 🔐 RBAC
│   │   ├── 📄 dashboard.py    # Dashboard endpoints
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
│   ├── 📄 company.py          # Company model
│   ├── 📄 job.py              # Job posting model
│   ├── 📄 team_member.py      # Team member relationships
│   ├── 📄 interview_feedback.py # Feedback model
│   ├── 📄 rejection_reason.py # Rejection reason model
│   ├── 📄 reminder.py         # Reminder model
│   ├── 📄 role_base_access_control.py  # RBAC models
│   └── 📄 ...                 # (20 model files total)
│
├── 📁 schemas/                # Pydantic Schemas (Request/Response)
│   ├── 📄 auth.py             # Auth schemas
│   ├── 📄 company_schema.py   # Company schemas
│   ├── 📄 team_member.py      # Team member schemas
│   ├── 📄 job.py              # Job schemas
│   ├── 📄 application.py      # Application schemas
│   ├── 📄 interview_feedback_schema.py  # Feedback schemas
│   └── 📄 ...                 # (35 schema files total)
│
├── 📁 services/               # 🔥 Business Logic Layer
│   ├── 📄 auth.py             # Authentication logic (57KB)
│   ├── 📄 company_service.py  # 🏢 Company CRUD (58KB - largest)
│   ├── 📄 user_service.py     # User management (52KB)
│   ├── 📄 job_service.py      # 📋 Job CRUD & filters (48KB)
│   ├── 📄 application_service.py  # 📝 Application management (61KB)
│   ├── 📄 job_scoring_service.py  # 📊 Job quality scoring (27KB)
│   ├── 📄 interview_feedback_service.py  # Feedback logic
│   ├── 📄 activity_log_service.py     # Activity tracking (26KB)
│   ├── 📄 reminder_service.py         # Reminder system
│   ├── 📄 role_base_access_control_service.py  # 🔐 RBAC (20KB)
│   ├── 📄 chat_service.py     # Chat messaging logic
│   ├── 📄 notification_service.py     # Notification sending
│   ├── 📄 email_service.py    # Email sending
│   ├── 📄 ai_generator_service.py     # 🤖 AI job description
│   ├── 📄 candidate_service.py        # Candidate scoring
│   └── 📄 ...                 # (41 service files total)
│
├── 📁 db/                     # Database Layer
│   ├── 📄 session.py          # Database connection
│   └── 📁 migrations/         # Alembic migrations
│
├── 📁 utils/                  # Utility Functions
├── 📁 exceptions/             # Custom Exceptions
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

### File Penting untuk Recruiter API

| File | Path | Deskripsi |
|------|------|-----------|
| 🔐 **Auth Service** | `app/services/auth.py` | Login, register corporate |
| 🏢 **Company Service** | `app/services/company_service.py` | Company profile, team, verification |
| 📋 **Job Service** | `app/services/job_service.py` | Job CRUD, AI generation |
| 📊 **Job Scoring** | `app/services/job_scoring_service.py` | Job quality analysis |
| 📝 **Application Service** | `app/services/application_service.py` | Application review, status |
| 👥 **Candidate Service** | `app/services/candidate_service.py` | Scoring, ranking |
| 📊 **Activity Log** | `app/services/activity_log_service.py` | Activity dashboard |
| 🔐 **RBAC Service** | `app/services/role_base_access_control_service.py` | Role permissions |
| 💬 **Chat Service** | `app/services/chat_service.py` | Messaging candidates |
| 🤖 **AI Generator** | `app/services/ai_generator_service.py` | AI job description |

---

## 2. 📌 Overview

### Apa yang Bisa Dilakukan Recruiter?

SuperJob API memungkinkan recruiter/employer untuk:

| Fitur | Deskripsi |
|-------|-----------|
| 🔐 **Register & Login** | Daftar perusahaan dengan dokumen NIB |
| 🏢 **Company Profile** | Kelola profil perusahaan |
| 👥 **Team Management** | Tambah/kelola tim recruiter |
| 📋 **Job Posting** | Buat, edit, hapus lowongan kerja |
| 📊 **Analytics** | Pantau performa lowongan |
| 📝 **Applications** | Review & kelola lamaran kandidat |
| 💬 **Chat** | Komunikasi dengan kandidat |
| 🔔 **Notifications** | Terima notifikasi real-time |
| 🤖 **AI Tools** | Generate job description, interview questions |

### Flow Umum Recruiter

```
Register Company → Verify → Complete Profile → Post Jobs → Review Candidates → Interview → Hire
       ↓              ↓            ↓               ↓              ↓              ↓          ↓
     POST          POST         PUT            POST           GET/PUT        Feedback    Status
   /auth/        /auth/      /companies/      /jobs/       /applications/              Update
  corporate/    verify-email  {id}
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

```http
Authorization: Bearer <access_token>
```

### Token System

| Token | Expiry | Fungsi |
|-------|--------|--------|
| **Access Token** | 30 menit | Akses API |
| **Refresh Token** | 7 hari | Dapatkan access token baru |

### ID Format Reference

| Entity | ID Type | Example |
|--------|---------|---------|
| Users | Integer | `8`, `1001` |
| Jobs | Integer | `1`, `10` |
| Companies | Integer | `1`, `5` |
| Applications | Integer | `1`, `101` |
| Chat Threads | UUID | `550e8400-e29b-41d4-a716-446655440000` |
| Notifications | UUID | `notif111-1111-1111-1111-111111111111` |
| Reminders | UUID | `aaaa1111-aaaa-1111-aaaa-111111111111` |

---

## 3. 🔐 Authentication

### 3.1 Register Company

**`POST /auth/register/company`** atau **`POST /auth/corporate/register`**

> Registrasi perusahaan baru dengan admin user.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contact_name` | string | ✅ | Nama contact person |
| `company_name` | string | ✅ | Nama perusahaan |
| `email` | string | ✅ | Email bisnis |
| `phone_number` | string | ✅ | No. telepon (+62...) |
| `password` | string | ✅ | Password (min 8 karakter) |
| `nib_document` | file | ❌ | NIB Document (PDF, max 5MB) |

**Request:**
```bash
curl -X POST "{base_url}/auth/corporate/register" \
  -F "contact_name=HR Manager" \
  -F "company_name=PT Teknologi Maju" \
  -F "email=hr@teknologimaju.com" \
  -F "phone_number=+6281234567890" \
  -F "password=SecurePass123" \
  -F "nib_document=@/path/to/nib.pdf"
```

**Response (201):**
```json
{
  "message": "Registrasi berhasil. Silakan tunggu verifikasi akun.",
  "user_id": 100,
  "email": "hr@teknologimaju.com",
  "company_name": "PT Teknologi Maju",
  "role": "employer",
  "is_verified": false
}
```

> ⚠️ **Note:** Akun memerlukan verifikasi admin sebelum dapat digunakan.

---

### 3.2 Corporate Login

**`POST /auth/corporate/login`**

> Login untuk employer/admin.

**Request Body:**
```json
{
  "email": "employer@superjob.com",
  "password": "employer123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_expires_in": 604800,
  "user": {
    "id": 8,
    "email": "employer@superjob.com",
    "full_name": "Employer 1",
    "role": "employer",
    "is_superuser": false
  }
}
```

**Test Credentials:**

| Email | Password | Role |
|-------|----------|------|
| `admin@superjob.com` | `admin123` | admin |
| `employer@superjob.com` | `employer123` | employer |
| `tanaka@gmail.com` | `password123` | employer |

---

### 3.3 Get Current User

**`GET /auth/me`** 🔒

---

### 3.4 Verify Email & Password Reset

Sama dengan Talent API:
- `POST /auth/verify-email`
- `POST /auth/resend-otp`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `POST /auth/refresh`

---

## 4. 🏢 Company Profile

### 4.1 Get Company Profile

**`GET /api/v1/companies/{company_id}`** 🔒

**Response (200):**
```json
{
  "id": 1,
  "name": "PT SuperJob Indonesia",
  "industry": "Technology",
  "description": "Leading job matching platform...",
  "website": "https://superjob.com",
  "location": "Jakarta",
  "founded_year": 2020,
  "employee_size": "51-200",
  "logo_url": "https://storage.superjob.com/logos/...",
  "banner_url": "https://storage.superjob.com/banners/...",
  "social_media": {
    "linkedin": "https://linkedin.com/company/superjob",
    "instagram": "@superjob.id"
  },
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 4.2 Update Company Profile

**`PUT /api/v1/companies/{company_id}`** 🔒

**Content-Type:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Nama perusahaan |
| `industry` | string | Industri |
| `description` | string | Deskripsi perusahaan |
| `website` | string | URL website |
| `location` | string | Lokasi |
| `founded_year` | int | Tahun berdiri |
| `employee_size` | string | 1-10, 11-50, 51-200, 201-500, 500+ |
| `linkedin_url` | string | URL LinkedIn |
| `instagram_url` | string | URL Instagram |
| `logo` | file | Logo (PNG/JPG, max 2MB) |
| `banner` | file | Banner (PNG/JPG, max 5MB) |
| `nib_document` | file | NIB (PDF) |
| `npwp_document` | file | NPWP (PDF) |
| `proposal_document` | file | Proposal (PDF) |
| `portfolio_document` | file | Portfolio (PDF) |

**Request:**
```bash
curl -X PUT "{base_url}/api/v1/companies/1" \
  -H "Authorization: Bearer <token>" \
  -F "name=PT SuperJob Indonesia" \
  -F "industry=Technology" \
  -F "description=Leading job platform..." \
  -F "logo=@/path/to/logo.png"
```

---

### 4.3 Verify Company (Superadmin Only)

**`POST /api/v1/companies/{company_id}/verify`** 🔒

> Verifikasi perusahaan (hanya superadmin).

---

## 5. 👥 Team Management

### 5.1 List Company Users

**`GET /api/v1/companies/{company_id}/users`** 🔒

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `limit` | int | 10 | Items per page |
| `search` | string | - | Search by name/email |
| `role` | string | - | Filter by role |
| `is_active` | bool | - | Filter by status |
| `sort_by` | string | created_at | Sort field |
| `sort_order` | string | desc | asc/desc |

**Response (200):**
```json
{
  "users": [
    {
      "id": 10,
      "email": "recruiter@company.com",
      "full_name": "Recruiter 1",
      "role": "recruiter",
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 10
}
```

---

### 5.2 Add Company User

**`POST /api/v1/companies/{company_id}/users`** 🔒

> Tambah user baru ke perusahaan.

**Request Body:**
```json
{
  "email": "newrecruiter@company.com",
  "full_name": "New Recruiter",
  "password": "SecurePass123",
  "role": "recruiter"
}
```

> ⚠️ **Note:** Tidak boleh assign role admin (role_id = 1).

---

### 5.3 Update Company User

**`PUT /api/v1/companies/{company_id}/users/{user_id}`** 🔒

**Request Body:**
```json
{
  "full_name": "Updated Name",
  "role": "hr_manager",
  "is_active": true
}
```

> **Permissions:**
> - Admin: Bisa edit semua (email, password, role)
> - Employer: Hanya bisa edit profil sendiri

---

### 5.4 Remove Company User

**`DELETE /api/v1/companies/{company_id}/users/{user_id}`** 🔒

---

### Team Members Endpoint (Alternative)

#### List Team Members

**`GET /api/v1/employers/{employer_id}/team-members`** 🔒

#### Add Team Member

**`POST /api/v1/employers/{employer_id}/team-members`** 🔒

**Request Body:**
```json
{
  "user_id": 10,
  "role": "recruiter"
}
```

ATAU buat user baru:

```json
{
  "email": "new@company.com",
  "full_name": "New Member",
  "password": "Pass123",
  "role": "recruiter"
}
```

**Available Roles:** `admin`, `hr_manager`, `recruiter`, `hiring_manager`, `trainer`

#### Update Team Member

**`PUT /api/v1/employers/{employer_id}/team-members/{member_id}`** 🔒

#### Remove Team Member

**`DELETE /api/v1/employers/{employer_id}/team-members/{member_id}`** 🔒

---

## 6. 📋 Job Posting

### 6.1 Create Job

**`POST /api/v1/jobs/`** 🔒

**Request Body:**
```json
{
  "title": "Senior Software Engineer",
  "department": "Engineering",
  "description": "We are looking for an experienced...",
  "requirements": [
    "5+ years experience in software development",
    "Proficiency in Python and JavaScript"
  ],
  "responsibilities": [
    "Design and implement scalable systems",
    "Lead technical discussions"
  ],
  "employment_type": "full_time",
  "working_type": "hybrid",
  "location": "Jakarta",
  "salary_min": 15000000,
  "salary_max": 25000000,
  "salary_currency": "IDR",
  "education": "S1",
  "experience_level": "senior",
  "status": "draft",
  "ai_interview_enabled": true,
  "ai_interview_questions": 5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ | Judul posisi |
| `department` | string | ❌ | Departemen |
| `description` | string | ✅ | Deskripsi lengkap |
| `requirements` | array | ❌ | List requirements |
| `responsibilities` | array | ❌ | List responsibilities |
| `employment_type` | string | ✅ | full_time, part_time, contract, internship |
| `working_type` | string | ✅ | onsite, remote, hybrid |
| `location` | string | ✅ | Lokasi kerja |
| `salary_min` | int | ❌ | Gaji minimum |
| `salary_max` | int | ❌ | Gaji maksimum |
| `education` | string | ❌ | SMA, D3, S1, S2, S3 |
| `experience_level` | string | ❌ | entry, junior, mid, senior, lead |
| `status` | string | ✅ | draft, published, closed, archived |

**Response (201):**
```json
{
  "id": 15,
  "title": "Senior Software Engineer",
  "status": "draft",
  "created_at": "2024-01-20T10:00:00Z"
}
```

---

### 6.2 List Jobs

**`GET /api/v1/jobs/`** 🔒

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: draft, published, closed, archived |
| `department` | string | Filter by department |
| `search` | string | Search by title |
| `page` | int | Page number |
| `limit` | int | Items per page |

---

### 6.3 Get Job Detail

**`GET /api/v1/jobs/{job_id}`** 🔒

---

### 6.4 Update Job

**`PUT /api/v1/jobs/{job_id}`** 🔒

---

### 6.5 Delete Job

**`DELETE /api/v1/jobs/{job_id}`** 🔒

> Soft delete - job tidak dihapus permanen.

---

### 6.6 AI Generate Job Description

**`POST /api/v1/jobs/criteria/ai`** 🔒

> Generate job description menggunakan AI.

**Request Body:**
```json
{
  "title": "Senior Software Engineer",
  "department": "Engineering",
  "location": "Jakarta"
}
```

**Response (200):**
```json
{
  "description": "We are seeking a talented Senior Software Engineer...",
  "requirements": [
    "5+ years of experience in software development",
    "Strong proficiency in Python, JavaScript, or Go"
  ],
  "responsibilities": [
    "Lead the design and development of complex systems",
    "Mentor junior developers"
  ]
}
```

---

### 6.7 AI Generate Interview Questions

**`POST /api/v1/jobs/interview/ai`** 🔒

> Generate pertanyaan interview dengan AI.

**Request Body:**
```json
{
  "title": "Senior Software Engineer",
  "department": "Engineering",
  "experience_level": "senior",
  "num_questions": 5,
  "question_type": "technical"
}
```

**Response (200):**
```json
{
  "questions": [
    "Explain the SOLID principles and give examples of how you've applied them.",
    "Describe a challenging technical problem you solved recently.",
    "How would you design a scalable microservices architecture?",
    "What's your approach to code review?",
    "How do you handle technical debt?"
  ]
}
```

---

## 7. 📊 Job Performance

### 7.1 Get Job Scoring

**`GET /api/v1/jobs/{job_id}/scoring`** 🔒

> Skor kualitas job posting (0-120).

**Response (200):**
```json
{
  "job_id": 1,
  "total_score": 95,
  "grade": "Excellent",
  "category_scores": {
    "title": 20,
    "description": 25,
    "requirements": 20,
    "salary": 15,
    "benefits": 15
  },
  "recommendations": [
    "Add more specific technical requirements",
    "Include company culture description"
  ]
}
```

**Grading:**
| Score | Grade |
|-------|-------|
| 0-40 | Poor |
| 41-70 | Fair |
| 71-100 | Good |
| 101-120 | Excellent |

---

### 7.2 Employer Scoring Overview

**`GET /api/v1/jobs/employers/{employer_id}/scoring/overview`** 🔒

> Overview skor semua job posting.

---

### 7.3 Job Performance Metrics

**`GET /api/v1/jobs/employers/{employer_id}/job-performance`** 🔒

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | active, draft, closed |
| `sort_by` | string | views, applicants, apply_rate |
| `sort_order` | string | asc, desc |
| `page` | int | Page number |
| `limit` | int | Items per page |

**Response (200):**
```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Senior Software Engineer",
      "status": "published",
      "views_count": 500,
      "applicants_count": 25,
      "apply_rate": 5.0,
      "quality_score": 95
    }
  ],
  "total": 10,
  "summary": {
    "total_views": 2000,
    "total_applicants": 150,
    "average_apply_rate": 7.5
  }
}
```

---

### 7.4 Job Statistics

**`GET /api/v1/jobs/{job_id}/statistics`** 🔒

---

### 7.5 Overall Statistics

**`GET /api/v1/jobs/statistics/overall`** 🔒

---

## 8. 📝 Application Management

### 8.1 List Applications

**`GET /api/v1/applications/`** 🔒

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | int | Filter by job |
| `statuses` | string | Comma-separated: applied,in_review,qualified |
| `search` | string | Search by name |
| `page` | int | Page number |
| `limit` | int | Items per page |
| `sort_by` | string | created_at, score |
| `sort_order` | string | asc, desc |

---

### 8.2 Get Job Applications

**`GET /api/v1/jobs/{job_id}/applications`** 🔒

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter status |
| `stage` | string | Interview stage |
| `search` | string | Search candidate |
| `page` | int | Page number |
| `limit` | int | Items per page |

**Response (200):**
```json
{
  "applications": [
    {
      "id": 123,
      "candidate": {
        "id": 1001,
        "name": "John Doe",
        "email": "john@example.com",
        "cv_url": "https://..."
      },
      "status": "qualified",
      "stage": "first_interview",
      "scores": {
        "fit_score": 85,
        "skill_score": 90,
        "experience_score": 80
      },
      "applied_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 25
}
```

---

### 8.3 Application Detail

**`GET /api/v1/applications/{application_id}`** 🔒

**Response (200):**
```json
{
  "id": 123,
  "candidate": {
    "id": 1001,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+6281234567890",
    "linkedin_url": "https://linkedin.com/in/johndoe"
  },
  "job": {
    "id": 1,
    "title": "Senior Software Engineer"
  },
  "status": "qualified",
  "stage": "first_interview",
  "cv_url": "https://...",
  "cv_extracted_data": {
    "experience": [...],
    "education": [...],
    "skills": [...]
  },
  "coverletter": "I am excited to apply...",
  "portfolio_url": "https://...",
  "applied_at": "2024-01-15T10:30:00Z"
}
```

---

### 8.4 Update Application Status

**`PUT /api/v1/applications/{application_id}/status`** 🔒

**Request Body:**
```json
{
  "new_status": "qualified",
  "new_stage": "first_interview",
  "reason": "Kandidat memenuhi semua requirement"
}
```

**Available Statuses:**
| Status | Description |
|--------|-------------|
| `applied` | Baru melamar |
| `in_review` | Sedang direview |
| `qualified` | Lolos kualifikasi |
| `not_qualified` | Tidak lolos |
| `contract_signed` | Kontrak ditandatangani |

**Interview Stages:**
| Stage | Description |
|-------|-------------|
| `first_interview` | Interview pertama |
| `second_interview` | Interview kedua |
| `final_interview` | Interview final |
| `hr_interview` | Interview HR |
| `technical_test` | Tes teknis |

---

### 8.5 Bulk Update Status

**`PUT /api/v1/applications/status/bulk`** 🔒

> Update multiple applications sekaligus.

**Request Body:**
```json
{
  "applications": [
    {
      "application_id": 123,
      "new_status": "qualified",
      "new_stage": "first_interview",
      "note": "Kandidat bagus"
    },
    {
      "application_id": 124,
      "new_status": "not_qualified",
      "note": "Skill tidak match"
    }
  ]
}
```

---

### 8.6 Update Application Scores

**`PUT /api/v1/applications/{application_id}/scores`** 🔒

**Request Body:**
```json
{
  "fit_score": 85,
  "skill_score": 90,
  "experience_score": 80
}
```

> Semua score dalam range 0-100.

---

### 8.7 Application History

**`GET /api/v1/applications/{application_id}/history`** 🔒

---

### 8.8 Dashboard Statistics

**`GET /api/v1/applications/statistics/dashboard`** 🔒

**Response (200):**
```json
{
  "total_applications": 150,
  "by_status": {
    "applied": 50,
    "in_review": 30,
    "qualified": 40,
    "not_qualified": 20,
    "contract_signed": 10
  },
  "this_week": 25,
  "this_month": 80
}
```

---

### 8.9 Application Files

#### Upload File

**`POST /api/v1/applications/{application_id}/files`** 🔒

**Content-Type:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | File to upload |
| `file_type` | string | resume, portfolio, certificate, cover_letter, other |

#### List Files

**`GET /api/v1/applications/{application_id}/files`** 🔒

#### Get File

**`GET /api/v1/applications/{application_id}/files/{file_id}`** 🔒

#### Delete File

**`DELETE /api/v1/applications/{application_id}/files/{file_id}`** 🔒

---

## 9. 📋 Interview Feedback

### 9.1 Submit Feedback

**`POST /api/v1/interview-feedbacks/`** 🔒

**Request Body:**
```json
{
  "application_id": 123,
  "rating": 4,
  "feedback": "Kandidat menunjukkan pemahaman yang baik tentang teknologi..."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `application_id` | int | ✅ | ID application |
| `rating` | int | ✅ | 1-5 |
| `feedback` | string | ❌ | Min 10 karakter |

---

### 9.2 Get Feedback by Application

**`GET /api/v1/interview-feedbacks/application/{application_id}`** 🔒

**Response (200):**
```json
{
  "exists": true,
  "feedback": {
    "id": 1,
    "rating": 4,
    "feedback": "Kandidat menunjukkan...",
    "created_by": {
      "id": 8,
      "name": "Recruiter 1"
    },
    "created_at": "2024-01-20T14:00:00Z"
  }
}
```

---

### 9.3 Update Feedback

**`PUT /api/v1/interview-feedbacks/application/{application_id}`** 🔒

atau

**`PUT /api/v1/interview-feedbacks/{feedback_id}`** 🔒

---

## 10. ❌ Rejection Reasons

### 10.1 List Rejection Reasons

**`GET /api/v1/rejection-reasons/`** 🔒

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_only` | bool | false | Only active reasons |

**Response (200):**
```json
{
  "reasons": [
    {"id": 1, "code": "SKILL_MISMATCH", "text": "Keterampilan tidak sesuai"},
    {"id": 2, "code": "EXPERIENCE_LACK", "text": "Pengalaman kurang"},
    {"id": 3, "code": "SALARY_MISMATCH", "text": "Gaji tidak sesuai"},
    {"id": 4, "code": "CULTURE_FIT", "text": "Tidak cocok budaya"},
    {"id": 5, "code": "COMMUNICATION", "text": "Komunikasi kurang"},
    {"id": 6, "code": "POSITION_FILLED", "text": "Posisi sudah terisi"},
    {"id": 7, "code": "NO_RESPONSE", "text": "Tidak merespons"},
    {"id": 8, "code": "DOCUMENT_INCOMPLETE", "text": "Dokumen tidak lengkap"},
    {"id": 9, "code": "OVERQUALIFIED", "text": "Terlalu berkualifikasi"},
    {"id": 10, "code": "LOCATION_ISSUE", "text": "Lokasi tidak sesuai"},
    {"id": 11, "code": "OTHER", "text": "Alasan lainnya"}
  ]
}
```

---

### 10.2 Create Custom Reason

**`POST /api/v1/rejection-reasons/`** 🔒

**Request Body:**
```json
{
  "code": "CUSTOM_REASON",
  "text": "Alasan khusus perusahaan"
}
```

---

### 10.3 Deactivate Reason

**`PATCH /api/v1/rejection-reasons/{reason_id}/deactivate`** 🔒

---

## 11. 💬 Chat & Messaging

### 11.1 Create Chat Thread

**`POST /api/v1/chat/threads/create`** 🔒

**Request Body:**
```json
{
  "employer_id": 8,
  "candidate_id": 1001,
  "job_id": 1,
  "subject": "Regarding your application"
}
```

---

### 11.2 List Chat Threads

**`GET /api/v1/chat/list`** 🔒

---

### 11.3 Get Chat History

**`GET /api/v1/chat/{thread_id}`** 🔒

---

### 11.4 Send Message

**`POST /api/v1/chat/{thread_id}/messages`** 🔒

**Request Body:**
```json
{
  "content": "Hello, we would like to schedule an interview..."
}
```

---

### 11.5 Mark as Read

**`PATCH /api/v1/chat/{thread_id}/read`** 🔒

---

### 11.6 AI Reply Suggestions

**`POST /api/v1/chat/{thread_id}/ai-suggestions`** 🔒

> Dapatkan saran balasan dari AI.

---

### 11.7 WebSocket Real-time

**URL:** `ws://{host}/ws/chat/{thread_id}?token={jwt_token}`

---

## 12. 🔔 Notifications

### 12.1 Get Notifications

**`GET /api/v1/notifications/`** 🔒

**Response (200):**
```json
{
  "notifications": [
    {
      "id": "notif-123",
      "type": "new_applicant",
      "title": "Pelamar Baru",
      "message": "John Doe melamar posisi Software Engineer",
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

**Notification Types:**
| Type | Description |
|------|-------------|
| `new_applicant` | Kandidat baru melamar |
| `new_message` | Pesan baru dari kandidat |
| `interview_scheduled` | Interview dijadwalkan |
| `reminder` | Reminder task |

---

### 12.2 Mark as Read

**`POST /api/v1/notifications/{notification_id}/read`** 🔒

---

### 12.3 Mark All as Read

**`POST /api/v1/notifications/read-all`** 🔒

---

## 13. 📊 Dashboard & Activities

### 13.1 Get Dashboard

**`GET /api/v1/dashboard/`** 🔒

**Response (200):**
```json
{
  "profile": {...},
  "team_members": [...],
  "company_profile": {...},
  "jobs_summary": {
    "total": 10,
    "published": 6,
    "draft": 3,
    "closed": 1
  },
  "applications_summary": {
    "total": 150,
    "pending": 50,
    "in_progress": 80,
    "hired": 20
  }
}
```

---

### 13.2 Activity Dashboard

**`GET /api/v1/employer/{employer_id}/activities/dashboard`** 🔒

**Response (200):**
```json
{
  "stats_24h": {
    "job_published": 2,
    "new_applicant": 15,
    "status_changed": 8,
    "team_updated": 1
  },
  "recent_activities": [
    {
      "id": "act-123",
      "type": "new_applicant",
      "description": "John Doe applied for Software Engineer",
      "timestamp": "2024-01-20T14:00:00Z"
    }
  ]
}
```

---

### 13.3 Activity Timeline

**`GET /api/v1/employer/{employer_id}/activities/timeline`** 🔒

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | date | Filter start |
| `end_date` | date | Filter end |
| `page` | int | Page number |
| `limit` | int | Items per page |

---

### 13.4 Activity Detail

**`GET /api/v1/employer/{employer_id}/activities/{activity_id}`** 🔒

---

### 13.5 Mark Activity as Read

**`PATCH /api/v1/activities/{activity_id}/read`** 🔒

---

## 14. ⏰ Reminders

### 14.1 List Reminders

**`GET /api/v1/employers/{employer_id}/reminders`** 🔒

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | pending, done, ignored |

---

### 14.2 Create Reminder

**`POST /api/v1/employers/{employer_id}/reminders`** 🔒

**Request Body:**
```json
{
  "task_title": "Interview John Doe",
  "task_type": "interview",
  "redirect_url": "/applications/123",
  "due_at": "2024-01-25T10:00:00Z"
}
```

**Task Types:** `message`, `candidate`, `job_update`, `interview`, `other`

---

### 14.3 Update Reminder

**`PATCH /api/v1/employers/{employer_id}/reminders/{reminder_id}`** 🔒

**Request Body:**
```json
{
  "status": "done"
}
```

> Update status ke `done` atau `ignored` untuk auto-hide.

---

## 15. 🔐 RBAC - Role Management

### 15.1 List Permissions

**`GET /api/v1/rbac/permissions`** 🔒

---

### 15.2 Create Permission

**`POST /api/v1/rbac/permissions`** 🔒

---

### 15.3 List Roles

**`GET /api/v1/rbac/roles`** 🔒

---

### 15.4 Create Role

**`POST /api/v1/rbac/roles`** 🔒

---

### 15.5 Get Role Detail

**`GET /api/v1/rbac/roles/{role_id}`** 🔒

---

### 15.6 Update Role

**`PUT /api/v1/rbac/roles/{role_id}`** 🔒

---

### 15.7 User Roles

**`GET /api/v1/rbac/users/{user_id}/roles`** 🔒

**`POST /api/v1/rbac/users/{user_id}/roles/{role_id}`** 🔒

**`DELETE /api/v1/rbac/users/{user_id}/roles/{role_id}`** 🔒

---

### 15.8 My Roles

**`GET /api/v1/rbac/me/roles`** 🔒

---

## 16. 🤖 AI Features

### AI-Powered Capabilities

| Feature | Endpoint | Description |
|---------|----------|-------------|
| **Job Description Generator** | `POST /api/v1/jobs/criteria/ai` | Generate deskripsi job |
| **Interview Question Generator** | `POST /api/v1/jobs/interview/ai` | Generate pertanyaan interview |
| **Job Scoring** | `GET /api/v1/jobs/{id}/scoring` | Evaluasi kualitas job posting |
| **Chat Suggestions** | `POST /api/v1/chat/{id}/ai-suggestions` | Saran balasan chat |
| **Candidate Matching** | Automatic | Match score kandidat |

---

## 17. 💡 Best Practices

### Company Profile

| Tip | Impact |
|-----|--------|
| ✅ Lengkapi semua info perusahaan | Kredibilitas tinggi |
| ✅ Upload logo & banner berkualitas | Profesional image |
| ✅ Tambahkan social media | Engagement tinggi |
| ✅ Verify dokumen NIB | Trust badge |

### Job Posting

| Tip | Impact |
|-----|--------|
| ✅ Gunakan AI generate description | Job score tinggi |
| ✅ Tulis requirements spesifik | Kandidat lebih match |
| ✅ Cantumkan range gaji | Apply rate tinggi |
| ✅ Update status tepat waktu | Candidate experience |

### Application Review

| Tip | Impact |
|-----|--------|
| ✅ Review dalam 48 jam | Kandidat tidak menunggu |
| ✅ Berikan feedback setiap interview | Professional |
| ✅ Gunakan bulk update | Efisiensi waktu |
| ✅ Set reminders | Tidak lupa follow-up |

### Communication

| Tip | Impact |
|-----|--------|
| ✅ Respond chat cepat | Good impression |
| ✅ Gunakan AI suggestions | Konsisten tone |
| ✅ Personalisasi pesan | Engagement tinggi |

---

## 18. ❗ Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (success, no body) |
| 400 | Bad Request |
| 401 | Unauthorized (token invalid/expired) |
| 403 | Forbidden (no permission) |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Token expired` | Access token expired | Refresh token |
| `Company not verified` | Perusahaan belum diverifikasi | Tunggu verifikasi admin |
| `Permission denied` | Role tidak memiliki akses | Check role permissions |
| `User not in company` | User bukan anggota perusahaan | Add to team first |

---

## 19. 📋 Use Cases

### Use Case 1: Register → Post Job

```bash
# 1. Register Company
POST /auth/corporate/register

# 2. Verify Email
POST /auth/verify-email

# 3. Login
POST /auth/corporate/login

# 4. Complete Company Profile
PUT /api/v1/companies/{company_id}

# 5. Generate Job Description (AI)
POST /api/v1/jobs/criteria/ai

# 6. Create Job
POST /api/v1/jobs/

# 7. Publish (update status)
PUT /api/v1/jobs/{job_id}
```

### Use Case 2: Review Applications

```bash
# 1. Get Applications
GET /api/v1/jobs/{job_id}/applications

# 2. View Details
GET /api/v1/applications/{application_id}

# 3. Update Status
PUT /api/v1/applications/{application_id}/status

# 4. Submit Feedback
POST /api/v1/interview-feedbacks/

# 5. Send Message
POST /api/v1/chat/{thread_id}/messages
```

### Use Case 3: Team Management

```bash
# 1. List Team
GET /api/v1/employers/{employer_id}/team-members

# 2. Add Member
POST /api/v1/employers/{employer_id}/team-members

# 3. Assign Role
POST /api/v1/rbac/users/{user_id}/roles/{role_id}

# 4. Monitor Activities
GET /api/v1/employer/{employer_id}/activities/dashboard
```

### Use Case 4: Performance Tracking

```bash
# 1. Check Job Performance
GET /api/v1/jobs/employers/{employer_id}/job-performance

# 2. Get Scoring Details
GET /api/v1/jobs/{job_id}/scoring

# 3. Application Statistics
GET /api/v1/applications/statistics/dashboard

# 4. Activity Timeline
GET /api/v1/employer/{employer_id}/activities/timeline
```

---

> 📝 **Last Updated:** Februari 2026
