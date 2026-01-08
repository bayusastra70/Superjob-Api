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

## Template untuk Update Selanjutnya

Gunakan template berikut saat menambahkan perubahan baru:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Detail Versi X.Y.Z

#### 📦 Kategori Perubahan (pilih yang sesuai)

- **Deskripsi:**
  - **Fitur/Fix Name:** Penjelasan detail tentang perubahan
  - **Impact:** Dampak perubahan terhadap sistem atau API consumers
  - **Technical Notes:** Catatan teknis jika diperlukan
  - **Migration Required:** Ya/Tidak (jika ada database migration)
```

### Kategori yang Tersedia:

- `✨ Fitur Baru` - Penambahan endpoint atau fitur baru
- `🐛 Bug Fix` - Perbaikan bug
- `🚀 Peningkatan Performa` - Optimasi performa API
- `🔒 Security Fix` - Perbaikan keamanan
- `📝 Documentation` - Update dokumentasi API
- `♻️ Refactor` - Refactoring code tanpa mengubah fungsionalitas
- `🗃️ Database` - Perubahan skema atau migrasi database
- `🔧 Configuration` - Perubahan konfigurasi
- `🧪 Testing` - Penambahan atau update test
- `🔨 Breaking Changes` - Perubahan yang break backward compatibility

---

## Contoh Entry Changelog

### Contoh 1: Penambahan Fitur Baru (MINOR Version)

```markdown
## [1.2.0] - 2025-01-15

### Detail Versi 1.2.0

#### ✨ Advanced Job Search & Filtering

- **Deskripsi:**
  - **New Endpoint:** `GET /api/v1/jobs/search`
  - **Query Parameters:**
    - `q`: Keyword search (job title, company name)
    - `location`: Filter by location/city
    - `job_type`: Filter by job type (full-time, part-time, contract, remote)
    - `salary_min` & `salary_max`: Salary range filter
    - `experience_level`: junior, mid, senior
    - `company_size`: startup, small, medium, large
    - `limit`: Results per page (default 20, max 100)
    - `offset`: Pagination offset
  - **Example Request:**
    ```bash
    GET /api/v1/jobs/search?q=software+engineer&location=jakarta&job_type=full-time&salary_min=10000000
    ```
  - **Response Time:** Average 120ms for 50K job listings
  - **Impact:** Memungkinkan job seekers menemukan lowongan yang sesuai dengan kriteria spesifik

#### 🚀 Peningkatan Performa

- **Deskripsi:**
  - **Database Indexing:** Menambahkan composite index pada `(location, job_type, created_at)` untuk faster filtering
  - **Full-Text Search:** Implementasi PostgreSQL full-text search untuk job title dan description
  - **Query Optimization:** Refactor query dengan eager loading untuk mengurangi N+1 queries
  - **Impact:** Response time search endpoint berkurang dari 800ms menjadi 120ms

#### 🗃️ Database Migration

- **Migration Required:** ✅ Yes
- **Migration Command:**
  ```bash
  alembic upgrade head
  ```
- **Changes:**
  - Added composite index on `jobs(location, job_type, created_at)`
  - Added GIN index on `jobs` for full-text search
  - Added `experience_level` ENUM column to `jobs` table
```

### Contoh 2: Bug Fix (PATCH Version)

```markdown
## [1.1.1] - 2025-01-10

### Detail Versi 1.1.1

#### 🐛 Bug Fix Job Application

- **Deskripsi:**
  - **Duplicate Application:** Fix issue dimana user bisa apply ke job yang sama multiple times
  - **Resume Upload Validation:** Perbaikan validasi file type (hanya accept PDF, DOC, DOCX)
  - **File Size Limit:** Enforce 5MB limit untuk resume upload
  - **Error Response:** Mengembalikan proper 400 Bad Request untuk invalid applications
  - **Impact:** Mencegah duplicate applications dan invalid file uploads

#### 🔒 Security Fix

- **Deskripsi:**
  - **SQL Injection:** Fix potential SQL injection di job search query
  - **File Upload Security:** Sanitize filename dan validate MIME type untuk resume upload
  - **Rate Limiting:** Implementasi rate limiting 10 applications per hour per user
  - **JWT Expiration:** Reduce token expiration dari 7 days ke 24 hours untuk security
  - **Impact:** Meningkatkan keamanan API dari common vulnerabilities

#### 📝 Documentation

- **Deskripsi:**
  - **Swagger Examples:** Menambahkan request/response examples untuk semua endpoints
  - **Error Codes:** Dokumentasi lengkap untuk semua HTTP status codes dan error messages
  - **Authentication Flow:** Step-by-step guide untuk register, login, dan apply job
```

### Contoh 3: Breaking Changes (MAJOR Version)

```markdown
## [2.0.0] - 2025-02-01

### Detail Versi 2.0.0

#### 🔨 Breaking Changes

- **Deskripsi:**
  - **API Versioning:**
    - **BREAKING:** Base path berubah dari `/api/jobs` ke `/api/v2/jobs`
    - Old endpoints tetap available di `/api/v1/` sampai Q2 2025
  
  - **Response Structure:**
    - **BREAKING:** Unified response format untuk consistency
    - Old:
      ```json
      {
        "id": 1,
        "title": "Software Engineer",
        "company": "Tech Corp"
      }
      ```
    - New:
      ```json
      {
        "success": true,
        "data": {
          "id": 1,
          "title": "Software Engineer",
          "company": {
            "id": 10,
            "name": "Tech Corp",
            "logo": "https://..."
          }
        },
        "meta": {
          "timestamp": "2025-02-01T10:00:00Z"
        }
      }
      ```
  
  - **Job Model:**
    - **BREAKING:** Field `salary` split menjadi `salary_min` dan `salary_max`
    - Field `location` sekarang object: `{city, province, country, is_remote}`
    - Field `required_skills` ditambahkan (array of strings)
    - Field `benefits` ditambahkan (array of strings)

#### ✨ Fitur Baru

- **Deskripsi:**
  - **Saved Jobs:** User dapat save jobs untuk apply nanti
    - `POST /api/v2/users/saved-jobs/{job_id}` - Save job
    - `GET /api/v2/users/saved-jobs` - List saved jobs
    - `DELETE /api/v2/users/saved-jobs/{job_id}` - Remove saved job
  
  - **Job Recommendations:** AI-powered job recommendations based on user profile
    - `GET /api/v2/jobs/recommendations` - Get personalized job recommendations
  
  - **Application Status Tracking:** Detailed application status workflow
    - Status: applied → reviewed → interview_scheduled → offered → accepted/rejected
    - Notifications untuk setiap status change

#### 🗃️ Database Migration

- **Migration Required:** ✅ Yes
- **Migration Command:**
  ```bash
  # Backup database first!
  pg_dump superjob > backup_$(date +%Y%m%d).sql
  
  # Run migration
  alembic upgrade head
  ```

- **Changes:**
  ```sql
  -- Split salary field
  ALTER TABLE jobs ADD COLUMN salary_min INTEGER;
  ALTER TABLE jobs ADD COLUMN salary_max INTEGER;
  UPDATE jobs SET salary_min = salary, salary_max = salary WHERE salary IS NOT NULL;
  ALTER TABLE jobs DROP COLUMN salary;
  
  -- Update location to JSONB
  ALTER TABLE jobs ADD COLUMN location_new JSONB;
  UPDATE jobs SET location_new = jsonb_build_object(
    'city', location,
    'province', NULL,
    'country', 'Indonesia',
    'is_remote', false
  );
  ALTER TABLE jobs DROP COLUMN location;
  ALTER TABLE jobs RENAME COLUMN location_new TO location;
  
  -- Add new fields
  ALTER TABLE jobs ADD COLUMN required_skills TEXT[] DEFAULT '{}';
  ALTER TABLE jobs ADD COLUMN benefits TEXT[] DEFAULT '{}';
  
  -- Create saved_jobs table
  CREATE TABLE saved_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    saved_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, job_id)
  );
  
  -- Update application status enum
  ALTER TYPE application_status ADD VALUE 'interview_scheduled';
  ALTER TYPE application_status ADD VALUE 'offered';
  ```

#### 📝 Migration Guide

**For Frontend Developers:**

1. Update base URL:
   ```typescript
   // Old
   const BASE_URL = "https://superjob-api.onrender.com/api/jobs"
   
   // New
   const BASE_URL = "https://superjob-api.onrender.com/api/v2/jobs"
   ```

2. Update response parsing:
   ```typescript
   // Old
   const response = await fetch(`${BASE_URL}/1`)
   const job = await response.json()
   console.log(job.title)
   
   // New
   const response = await fetch(`${BASE_URL}/1`)
   const result = await response.json()
   const job = result.data
   console.log(job.title)
   ```

3. Update job model:
   ```typescript
   // Old
   interface Job {
     salary: number
     location: string
   }
   
   // New
   interface Job {
     salary_min: number
     salary_max: number
     location: {
       city: string
       province: string
       country: string
       is_remote: boolean
     }
     required_skills: string[]
     benefits: string[]
   }
   ```

**For Database Admins:**

1. Schedule maintenance window (estimated 45 minutes for 500K jobs)
2. Create backup before migration
3. Run migration script
4. Verify data integrity:
   ```sql
   SELECT COUNT(*) FROM jobs WHERE salary_min IS NULL;
   SELECT COUNT(*) FROM jobs WHERE location IS NULL;
   SELECT COUNT(*) FROM saved_jobs;
   ```

#### ⚠️ Deprecation Notice

- `/api/v1/*` endpoints will be deprecated on **June 1, 2025**
- Start migrating to `/api/v2/*` as soon as possible
- V1 will return deprecation warning header: `X-API-Deprecated: true`
- Notification email akan dikirim ke semua API consumers 2 bulan sebelum deprecation
```

---

## Versioning Guidelines

### Kapan Increment Version?

**MAJOR (X.0.0):**
- Breaking changes di API contract (endpoint path, response structure)
- Database schema changes yang tidak backward-compatible
- Removal of deprecated endpoints
- Changes requiring migration atau action dari API consumers
- Perubahan authentication/authorization mechanism

**MINOR (0.X.0):**
- Penambahan endpoint baru (backward-compatible)
- Penambahan optional fields di request/response
- New features yang tidak break existing functionality
- Database schema additions (new tables, optional columns)
- Performance improvements yang significant

**PATCH (0.0.X):**
- Bug fixes
- Security patches
- Performance improvements tanpa API changes
- Documentation updates
- Internal refactoring tanpa API changes
- Logging dan monitoring improvements

---

## Database Migration Checklist

Untuk setiap perubahan yang memerlukan migration:

- [ ] Alembic migration script sudah dibuat
- [ ] Migration tested di development environment
- [ ] Rollback script sudah ditest
- [ ] Backup strategy sudah documented
- [ ] Estimated downtime sudah dihitung
- [ ] Migration guide untuk API consumers sudah dibuat
- [ ] Team sudah di-notify minimal 1 minggu sebelumnya

---

## Changelog Maintenance

### Best Practices

1. **Update setiap deploy ke production** - Document semua changes
2. **Include database changes** - Selalu dokumentasikan schema changes
3. **Provide migration guides** - Untuk breaking changes, sertakan step-by-step
4. **Version API endpoints** - Gunakan versioning untuk backward compatibility
5. **Deprecation warnings** - Kasih minimum 3 bulan notice sebelum remove endpoints
6. **Document breaking changes clearly** - Gunakan badge 🔨 dan BREAKING prefix
7. **Include performance impacts** - Dokumentasikan perubahan response time

### Bad Examples ❌

```markdown
## [1.2.0] - 2025-01-15
- Added search
- Fixed bugs
- Updated database
```

### Good Examples ✅

```markdown
## [1.2.0] - 2025-01-15

### Detail Versi 1.2.0

#### ✨ Advanced Job Search

- **Deskripsi:**
  - **New Endpoint:** `GET /api/v1/jobs/search`
  - **Query Parameters:**
    - `q`: Keyword (job title, company, skills)
    - `location`: City or province
    - `job_type`: full-time, part-time, contract, remote
    - `salary_min`: Minimum salary expectation
    - `limit`: Results per page (default 20, max 100)
  - **Response Time:** Average 120ms for 50K jobs
  - **Impact:** Meningkatkan job discovery rate sebesar 60% berdasarkan beta testing
  - **Example Request:**
    ```bash
    GET /api/v1/jobs/search?q=backend+developer&location=jakarta&job_type=remote
    ```

#### 🗃️ Database Migration

- **Migration Required:** ✅ Yes
- **Command:** `alembic upgrade head`
- **Changes:** Added GIN index on jobs for full-text search
- **Downtime:** ~10 minutes for index creation on production
```

---

## Version History Reference

| Version | Date | Type | Description |
|---------|------|------|-------------|
| 0.1.0 | 2025-01-08 | Initial | Project setup, basic CRUD, authentication, job listing |

---

## API Deprecation Policy

When deprecating endpoints:

1. **Announce** deprecation in changelog with target removal date (minimum 3 months)
2. **Add header** `X-API-Deprecated: true` to deprecated endpoints
3. **Update docs** with deprecation notice and migration path
4. **Notify stakeholders** via email dan Slack minimum 2 bulan sebelumnya
5. **Monitor usage** of deprecated endpoints
6. **Remove** only after grace period and usage drops to near-zero

---

**Note:** Changelog ini akan terus diupdate seiring development. Untuk breaking changes, selalu provide migration guide dan minimum 3 bulan deprecation period.