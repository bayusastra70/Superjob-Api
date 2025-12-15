# 📘 SuperJob API Testing Guide

Panduan lengkap untuk testing API SuperJob oleh tim Frontend.

---

## 🔐 Authentication

### Login Credentials

| Role           | Email                    | Password       | User ID |
| -------------- | ------------------------ | -------------- | ------- |
| **Admin**      | `admin@superjob.com`     | `admin123`     | 1       |
| **Employer**   | `employer@superjob.com`  | `employer123`  | 8       |
| **Candidate**  | `candidate@superjob.com` | `candidate123` | 9       |
| **Employer 2** | `tanaka@gmail.com`       | `password`     | 3       |

### Cara Login di Swagger

1. Buka `http://localhost:8000/docs`
2. Klik **POST /auth/token**
3. Klik **Try it out**
4. Isi form:
   - `username`: email (contoh: `employer@superjob.com`)
   - `password`: password (contoh: `employer123`)
5. Klik **Execute**
6. Copy `access_token` dari response
7. Klik tombol **Authorize** (🔒) di pojok kanan atas
8. Paste token dengan format: `Bearer <token>`

---

## 📊 Test Data Lengkap

### 👥 Users (15 users)

| ID        | Email                     | Role      | Description                           |
| --------- | ------------------------- | --------- | ------------------------------------- |
| 1         | admin@superjob.com        | admin     | System Administrator                  |
| 2         | fikri@gmail.com           | candidate | Test candidate                        |
| 3         | tanaka@gmail.com          | employer  | Employer 2 (Company: Creative Studio) |
| 8         | employer@superjob.com     | employer  | Main employer for testing             |
| 9         | candidate@superjob.com    | candidate | Main candidate for testing            |
| 1001-1005 | john.doe@example.com, etc | candidate | Sample candidates                     |

### 🏢 Companies (5 companies)

| ID  | Name                  | Industry           | Location |
| --- | --------------------- | ------------------ | -------- |
| 1   | PT SuperJob Indonesia | Technology         | Jakarta  |
| 2   | TechCorp Solutions    | Technology         | Jakarta  |
| 3   | Creative Studio       | Creative & Design  | Bandung  |
| 4   | DataInsight Analytics | Data & Analytics   | Surabaya |
| 5   | FinTech Sejahtera     | Financial Services | Jakarta  |

### 📋 Job Postings (6 jobs - UUID IDs)

| Job ID (UUID)                          | Title                     | Employer ID | Status    |
| -------------------------------------- | ------------------------- | ----------- | --------- |
| `11111111-1111-1111-1111-111111111111` | Senior Software Engineer  | 8           | published |
| `11111111-1111-1111-1111-111111111112` | Junior Frontend Developer | 8           | published |
| `11111111-1111-1111-1111-111111111113` | Product Manager           | 8           | published |
| `11111111-1111-1111-1111-111111111114` | DevOps Engineer           | 8           | draft     |
| `11111111-1111-1111-1111-111111111115` | UI/UX Designer            | 3           | published |
| `11111111-1111-1111-1111-111111111116` | Data Analyst              | 3           | published |

### 📝 Candidate Applications (6 applications - UUID IDs)

| Application ID (UUID)                  | Candidate     | Job                       | Status                            |
| -------------------------------------- | ------------- | ------------------------- | --------------------------------- |
| `ca111111-1111-1111-1111-111111111111` | John Doe      | Senior Software Engineer  | applied                           |
| `ca111111-1111-1111-1111-111111111112` | Jane Smith    | Senior Software Engineer  | qualified (first_interview)       |
| `ca111111-1111-1111-1111-111111111113` | Bob Wilson    | Junior Frontend Developer | in_review                         |
| `ca111111-1111-1111-1111-111111111114` | Alice Johnson | Product Manager           | contract_signed                   |
| `ca111111-1111-1111-1111-111111111115` | Charlie Brown | Senior Software Engineer  | rejected (reason: SKILL_MISMATCH) |
| `ca111111-1111-1111-1111-111111111116` | John Doe      | UI/UX Designer            | applied                           |

### 💬 Chat Threads (4 threads)

| Thread ID (UUID)                       | Participants             | Last Message                 |
| -------------------------------------- | ------------------------ | ---------------------------- |
| `550e8400-e29b-41d4-a716-446655440000` | John Doe ↔ Admin         | "hallo"                      |
| `550e8400-e29b-41d4-a716-446655440001` | Jane Smith ↔ Admin       | "Thanks for applying!"       |
| `550e8400-e29b-41d4-a716-446655440002` | Bob Wilson ↔ Employer 2  | "Please send your portfolio" |
| `abe51f39-7c7d-448f-ab01-29aa057a0174` | Candidate 1 ↔ Employer 1 | "tes lagi"                   |

### ⏰ Reminders (7 reminders - UUID IDs)

| Reminder ID (UUID)                     | Title                     | Type      | Status  |
| -------------------------------------- | ------------------------- | --------- | ------- |
| `aaaa1111-aaaa-1111-aaaa-111111111111` | Review lamaran John Doe   | candidate | pending |
| `aaaa1111-aaaa-1111-aaaa-111111111112` | Jadwalkan interview       | interview | pending |
| `aaaa1111-aaaa-1111-aaaa-111111111113` | Balas pesan dari kandidat | message   | pending |
| `aaaa1111-aaaa-1111-aaaa-111111111116` | Task sudah selesai        | other     | done    |
| `aaaa1111-aaaa-1111-aaaa-111111111117` | Task diabaikan            | other     | ignored |

### ❌ Rejection Reasons (11 reasons)

| ID  | Code                | Text                      |
| --- | ------------------- | ------------------------- |
| 1   | SKILL_MISMATCH      | Keterampilan tidak sesuai |
| 2   | EXPERIENCE_LACK     | Pengalaman kurang         |
| 3   | SALARY_MISMATCH     | Gaji tidak sesuai         |
| 4   | CULTURE_FIT         | Tidak cocok budaya        |
| 5   | COMMUNICATION       | Komunikasi kurang         |
| 6   | POSITION_FILLED     | Posisi sudah terisi       |
| 7   | NO_RESPONSE         | Tidak merespons           |
| 8   | DOCUMENT_INCOMPLETE | Dokumen tidak lengkap     |
| 9   | OVERQUALIFIED       | Terlalu berkualifikasi    |
| 10  | LOCATION_ISSUE      | Lokasi tidak sesuai       |
| 11  | OTHER               | Alasan lainnya            |

### 🔔 Notifications (7 notifications)

| ID (UUID)             | User        | Type                | is_read |
| --------------------- | ----------- | ------------------- | ------- |
| `notif111-...-111111` | Employer 8  | new_applicant       | false   |
| `notif111-...-111112` | Employer 8  | new_applicant       | true    |
| `notif111-...-111113` | Employer 8  | interview_scheduled | false   |
| `notif111-...-111114` | Employer 8  | new_message         | false   |
| `notif111-...-111115` | Candidate 9 | status_update       | false   |
| `notif111-...-111116` | Employer 3  | new_applicant       | false   |
| `notif111-...-111117` | Employer 8  | reminder            | true    |

---

## 🗂️ API Endpoint Categories

### 🔐 Auth (`/auth`)

| Method | Endpoint         | Description                  |
| ------ | ---------------- | ---------------------------- |
| POST   | `/auth/token`    | Login dan dapatkan JWT token |
| POST   | `/auth/register` | Register user baru           |
| GET    | `/auth/me`       | Get current user info        |

### 👤 Users & Candidates (`/api/v1`)

| Method | Endpoint                  | Description         |
| ------ | ------------------------- | ------------------- |
| GET    | `/api/v1/candidates`      | List semua kandidat |
| GET    | `/api/v1/candidates/{id}` | Detail kandidat     |

### 🏢 Companies (`/api/v1/companies`)

| Method | Endpoint                         | Description           |
| ------ | -------------------------------- | --------------------- |
| GET    | `/api/v1/companies`              | List semua perusahaan |
| GET    | `/api/v1/companies/{id}`         | Detail perusahaan     |
| GET    | `/api/v1/companies/{id}/reviews` | Reviews perusahaan    |

### 📋 Jobs - Integer ID (`/api/v1/jobs`)

| Method | Endpoint                | Description                               |
| ------ | ----------------------- | ----------------------------------------- |
| GET    | `/api/v1/jobs`          | List jobs (tabel `jobs`, ID: Integer 1-8) |
| GET    | `/api/v1/jobs/{job_id}` | Detail job                                |
| POST   | `/api/v1/jobs`          | Create job baru                           |
| PUT    | `/api/v1/jobs/{job_id}` | Update job                                |
| DELETE | `/api/v1/jobs/{job_id}` | Delete job                                |

### 📋 Job Postings - UUID (`/employers/{employer_id}/jobs`)

| Method | Endpoint                                 | Description        |
| ------ | ---------------------------------------- | ------------------ |
| GET    | `/employers/{employer_id}/jobs`          | List job postings  |
| POST   | `/employers/{employer_id}/jobs`          | Create job posting |
| GET    | `/employers/{employer_id}/jobs/{job_id}` | Detail job posting |

### 📝 Applications (`/api/v1/applications`)

| Method | Endpoint                           | Description            |
| ------ | ---------------------------------- | ---------------------- |
| GET    | `/api/v1/applications`             | List applications      |
| PUT    | `/api/v1/applications/{id}/status` | Update status aplikasi |

### 📄 Candidate Applications (`/api/v1/candidate-applications`)

| Method | Endpoint                                     | Description                 | Application ID |
| ------ | -------------------------------------------- | --------------------------- | -------------- |
| GET    | `/api/v1/candidate-applications`             | List candidate applications | UUID           |
| GET    | `/api/v1/candidate-applications/{id}`        | Detail application          | UUID           |
| PATCH  | `/api/v1/candidate-applications/{id}/status` | Update status               | UUID           |
| PATCH  | `/api/v1/candidate-applications/{id}/reject` | Reject candidate            | UUID           |

### ❌ Rejection Reasons (`/api/v1/rejection-reasons`)

| Method | Endpoint                                    | Description            |
| ------ | ------------------------------------------- | ---------------------- |
| GET    | `/api/v1/rejection-reasons`                 | List rejection reasons |
| POST   | `/api/v1/rejection-reasons`                 | Create new reason      |
| GET    | `/api/v1/rejection-reasons/{id}`            | Get by ID              |
| PATCH  | `/api/v1/rejection-reasons/{id}`            | Update reason          |
| PATCH  | `/api/v1/rejection-reasons/{id}/deactivate` | Deactivate             |

### 💬 Chat (`/api/v1/chat`)

| Method | Endpoint                            | Description       |
| ------ | ----------------------------------- | ----------------- |
| GET    | `/api/v1/chat/list`                 | List chat threads |
| GET    | `/api/v1/chat/{thread_id}`          | Get chat history  |
| POST   | `/api/v1/chat/{thread_id}/messages` | Send message      |
| POST   | `/api/v1/chat/threads/create`       | Create new thread |
| PATCH  | `/api/v1/chat/{thread_id}/read`     | Mark as read      |

### 🔔 Notifications (`/api/v1/notifications`)

| Method | Endpoint                              | Description        |
| ------ | ------------------------------------- | ------------------ |
| GET    | `/api/v1/notifications`               | List notifications |
| PATCH  | `/api/v1/notifications/{id}/read`     | Mark as read       |
| POST   | `/api/v1/notifications/mark-all-read` | Mark all as read   |

### 📊 Activities (`/api/v1/employer/{employer_id}/activities`)

| Method | Endpoint                                    | Description        |
| ------ | ------------------------------------------- | ------------------ |
| GET    | `/api/v1/employer/{employer_id}/activities` | List activity logs |
| POST   | `/api/v1/employer/{employer_id}/activities` | Create activity    |

### ⏰ Reminders (`/employers/{employer_id}/reminders`)

| Method | Endpoint                             | Description     |
| ------ | ------------------------------------ | --------------- |
| GET    | `/employers/{employer_id}/reminders` | List reminders  |
| POST   | `/employers/{employer_id}/reminders` | Create reminder |

### 📈 Job Quality & Performance

| Method | Endpoint                                         | Description             |
| ------ | ------------------------------------------------ | ----------------------- |
| GET    | `/employers/{employer_id}/jobs/{job_id}/quality` | Job quality score       |
| GET    | `/employers/{employer_id}/job-performance`       | Job performance metrics |

### 📊 Dashboard

| Method | Endpoint                                           | Description       |
| ------ | -------------------------------------------------- | ----------------- |
| GET    | `/employers/{employer_id}/dashboard/quick-actions` | Dashboard metrics |

---

## 🔑 ID Format Quick Reference

| Entity                            | ID Type | Example                                |
| --------------------------------- | ------- | -------------------------------------- |
| Users                             | Integer | `8`, `9`, `1001`                       |
| Jobs (tabel jobs)                 | Integer | `1`, `2`, `3`                          |
| Job Postings                      | UUID    | `11111111-1111-1111-1111-111111111111` |
| Applications (tabel applications) | Integer | `1`, `2`, `101`                        |
| Candidate Applications            | UUID    | `ca111111-1111-1111-1111-111111111111` |
| Chat Threads                      | UUID    | `550e8400-e29b-41d4-a716-446655440000` |
| Messages                          | UUID    | `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` |
| Reminders                         | UUID    | `aaaa1111-aaaa-1111-aaaa-111111111111` |
| Rejection Reasons                 | Integer | `1`, `2`, `11`                         |
| Companies                         | Integer | `1`, `2`, `5`                          |
| Notifications                     | UUID    | `notif111-1111-1111-1111-111111111111` |

---

## 🚀 Quick Test Scenarios

### 1. Login sebagai Employer

```bash
POST /auth/token
username: employer@superjob.com
password: employer123
```

### 2. Get Job Postings

```bash
GET /employers/8/jobs
```

### 3. Get Active Rejections Reasons

```bash
GET /api/v1/rejection-reasons/?active_only=true
```

### 4. Get Candidate Applications

```bash
GET /api/v1/candidate-applications?employer_id=8
```

### 5. Update Application Status

```bash
PATCH /api/v1/candidate-applications/ca111111-1111-1111-1111-111111111112/status
{
  "status": "qualified",
  "interview_stage": "second_interview"
}
```

### 6. Reject Candidate

```bash
PATCH /api/v1/candidate-applications/ca111111-1111-1111-1111-111111111111/reject
{
  "rejection_reason_id": 1,
  "notes": "Skill tidak sesuai requirement"
}
```

### 7. Get Notifications

```bash
GET /api/v1/notifications?user_id=8
```

### 8. Get Company Reviews

```bash
GET /api/v1/companies/1/reviews
```

---

## 🔄 Cron Job Commands

```bash
# Job Performance Alert
py -m app.cron.refresh_job_performance
```

---

## 📝 Notes untuk Frontend

1. **Authentication**: Semua endpoint (kecuali `/auth/token` dan `/auth/register`) membutuhkan Bearer token
2. **UUID vs Integer**: Perhatikan format ID setiap entity
3. **Pagination**: Banyak endpoint mendukung `skip` dan `limit` parameter
4. **Filtering**: Cek dokumentasi Swagger untuk filter yang tersedia
5. **WebSocket**: Chat realtime tersedia di `/ws/chat/{thread_id}`

---

_Last updated: 2025-12-15_
