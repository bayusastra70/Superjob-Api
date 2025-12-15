# SuperJob API - Testing Guide

## 🔐 Authentication

Semua endpoint (kecuali `/auth/token` dan `/health`) memerlukan Authorization token.

### Login Credentials untuk Testing:

| Email                    | Password      | Role      | ID  |
| ------------------------ | ------------- | --------- | --- |
| `admin@superjob.com`     | `password123` | admin     | 1   |
| `tanaka@gmail.com`       | `password123` | employer  | 3   |
| `employer@superjob.com`  | `password123` | employer  | 8   |
| `candidate@superjob.com` | `password123` | candidate | 9   |

### Cara Login:

1. Buka Swagger UI: `http://localhost:8000/docs`
2. Cari endpoint: **POST `/auth/token`**
3. Klik **Try it out**
4. Masukkan:

```json
{
  "email": "employer@superjob.com",
  "password": "password123"
}
```

5. Klik **Execute**
6. Copy `access_token` dari response
7. Klik tombol **Authorize** di kanan atas Swagger
8. Paste token dan klik **Authorize**

---

## 📋 Test Data yang Tersedia

### Employers (employer_id - Integer):

| ID  | Email                 | Jobs | Reminders | Activities |
| --- | --------------------- | ---- | --------- | ---------- |
| `8` | employer@superjob.com | 4    | 6         | Banyak     |
| `3` | tanaka@gmail.com      | 2    | 1         | Sedikit    |
| `1` | admin@superjob.com    | 0    | 0         | 2          |

### Job Postings (job_id - UUID format):

Untuk endpoint: `/employers/{id}/jobs`, `/jobs/{id}/quality-score`

| UUID                                   | Title                     | Employer | Status    |
| -------------------------------------- | ------------------------- | -------- | --------- |
| `11111111-1111-1111-1111-111111111111` | Senior Software Engineer  | 8        | published |
| `11111111-1111-1111-1111-111111111112` | Junior Frontend Developer | 8        | published |
| `11111111-1111-1111-1111-111111111113` | Product Manager           | 8        | published |
| `11111111-1111-1111-1111-111111111114` | DevOps Engineer           | 8        | draft     |
| `11111111-1111-1111-1111-111111111115` | UI/UX Designer            | 3        | published |
| `11111111-1111-1111-1111-111111111116` | Data Analyst              | 3        | published |

### Jobs (job_id - Integer):

Untuk endpoint: `/api/v1/jobs`, `/api/v1/jobs/{id}/applications`

| ID  | Title             |
| --- | ----------------- |
| `1` | Software Engineer |
| `2` | Data Analyst      |
| `3` | Product Manager   |

### Applications (application_id - Integer):

| ID  | Job ID | Status          |
| --- | ------ | --------------- |
| `1` | 1      | applied         |
| `2` | 1      | qualified       |
| `3` | 1      | in_review       |
| `4` | 2      | applied         |
| `5` | 2      | contract_signed |

### Chat Threads (thread_id - UUID format):

| UUID                                   | Participants |
| -------------------------------------- | ------------ |
| `abe51f39-7c7d-448f-ab01-29aa057a0174` | employer 8   |
| `550e8400-e29b-41d4-a716-446655440000` | employer 1   |

---

## 📂 Endpoint Categories

### 🔑 Authentication

- `POST /auth/token` - Login & get JWT token
- `POST /auth/register` - Register new user
- `GET /auth/me` - Get current user info

### 👔 Jobs (Integer ID)

- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{job_id}` - Get job detail
- `POST /api/v1/jobs` - Create job
- `PUT /api/v1/jobs/{job_id}` - Update job
- `DELETE /api/v1/jobs/{job_id}` - Delete job
- `GET /api/v1/jobs/{job_id}/applications` - Get job applications

### 📝 Job Postings (UUID)

- `GET /employers/{employer_id}/jobs` - List job postings
- `POST /employers/{employer_id}/jobs` - Create job posting
- `GET /employers/{employer_id}/jobs/{job_id}` - Get job posting detail

### 📊 Job Quality & Performance

- `GET /jobs/{job_id}/quality-score` - Get job quality score (UUID)
- `PATCH /jobs/{job_id}` - Update job fields (UUID)
- `GET /employers/{employer_id}/job-performance` - Job performance metrics

### 📋 Applications

- `GET /api/v1/applications` - List applications
- `GET /api/v1/applications/{id}` - Get application detail
- `POST /api/v1/applications` - Create application
- `PUT /api/v1/applications/{id}/status` - **Update status (triggers activity log)**

### 💬 Chat & Messaging

- `GET /api/v1/chat/list` - Get chat threads
- `GET /api/v1/chat/{thread_id}` - Get chat history
- `POST /api/v1/chat/{thread_id}/messages` - Send message
- `PATCH /api/v1/chat/{thread_id}/read` - Mark as read

### 📢 Activities / Notifications

- `GET /employer/{employer_id}/activities` - List activities
- `PATCH /activities/{activity_id}/read` - Mark activity as read

### 📌 Reminders

- `GET /employers/{employer_id}/reminders` - List reminders
- `POST /employers/{employer_id}/reminders` - Create reminder
- `PATCH /employers/{employer_id}/reminders/{id}` - Update reminder

### 📈 Dashboard

- `GET /employers/{employer_id}/dashboard/quick-actions` - Dashboard metrics

---

## ⚠️ ID Format Quick Reference

| Entity                | Format  | Example                                |
| --------------------- | ------- | -------------------------------------- |
| employer_id           | Integer | `8`                                    |
| job_id (job_postings) | UUID    | `11111111-1111-1111-1111-111111111111` |
| job_id (jobs table)   | Integer | `1`                                    |
| application_id        | Integer | `2`                                    |
| reminder_id           | UUID    | `aaaa1111-aaaa-1111-aaaa-111111111111` |
| activity_id           | Integer | `5`                                    |
| thread_id             | UUID    | `abe51f39-7c7d-448f-ab01-29aa057a0174` |
| user_id               | Integer | `8`                                    |

---

## 🧪 Quick Test Scenarios

### 1. Login as Employer

```
POST /auth/token
Body: {"email": "employer@superjob.com", "password": "password123"}
```

### 2. Get Job Quality Score

```
GET /jobs/11111111-1111-1111-1111-111111111111/quality-score
(Requires Auth Token)
```

### 3. List Activities

```
GET /employer/8/activities
(Requires Auth Token)
```

### 4. Update Application Status (Creates Activity Log)

```
PUT /api/v1/applications/2/status
Body: {
  "new_status": "qualified",
  "new_stage": "first_interview",
  "reason": "Kandidat lolos screening"
}
```

### 5. Get Chat List

```
GET /api/v1/chat/list
(Requires Auth Token)
```

---

## 🔄 Cron Jobs (Manual Testing)

```bash
cd c:\MyProject\superjob-api

# Refresh job performance (creates activity logs)
py -m app.cron.refresh_job_performance

# Check reminders
py -m app.cron.check_reminders

# Cleanup old activity logs (>14 days)
py -m app.cron.cleanup_activity_logs
```
