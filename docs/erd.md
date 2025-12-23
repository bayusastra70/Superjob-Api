# Superjob Corporate API - ERD (ringkas)

Fokus penambahan: tabel `activity_logs` untuk feed notifikasi/aktivitas.

> **⚠️ UPDATE (2025-12-22):** Table `job_postings` telah dikonsolidasikan ke table `jobs`.
> Semua referensi ke job sekarang menggunakan **Integer ID** (FK ke `jobs.id`).

## activity_logs

- `id` (bigint, PK, auto)
- `employer_id` (int, wajib) — pemilik log, FK ke `users.id`.
- `type` (enum `activity_type`) — `new_applicant` | `status_update` | `new_message` | `job_performance_alert` | `system_event`.
- `title` (varchar) — judul singkat.
- `subtitle` (text, opsional) — detail ringkas.
- `meta_data` (jsonb, default `{}`) — payload fleksibel per tipe event.
- `job_id` (int, nullable) — **referensi ke `jobs.id`** (Integer, bukan UUID).
- `applicant_id` (int, nullable) — referensi ke `applications.id` atau `candidate_application.id`.
- `message_id` (varchar(36), nullable) — referensi ke pesan/percakapan.
- `timestamp` (timestamptz, default `now()`).
- `is_read` (bool, default `false`).

## Relasi/Referensi

- `activity_logs.job_id` → **`jobs.id`** (Integer) bila event terkait pekerjaan.
- `activity_logs.applicant_id` → `applications.id` atau `candidate_application.id` bila event terkait pelamar.
- `activity_logs.message_id` → pesan/chat (varchar(36)) bila event berupa pesan baru.

## jobs (Consolidated Table)

> **Catatan:** Table `job_postings` telah di-merge ke `jobs` pada migrasi `0014`.

- `id` (int, PK, auto)
- `employer_id` (int, FK → users.id) — pemilik job posting
- `job_code` (varchar(50), nullable, unique) — kode job internal
- `title` (varchar(255)) — judul posisi
- `description` (text) — deskripsi pekerjaan
- `salary_min`, `salary_max` (numeric) — range gaji
- `salary_currency` (varchar(8), default 'IDR')
- `salary_interval` (enum) — hourly | daily | weekly | monthly | yearly
- `skills` (jsonb) — array of skills
- `location` (varchar)
- `employment_type` (varchar)
- `experience_level` (varchar)
- `education` (varchar(100))
- `working_type` (enum) — onsite | remote | hybrid
- `gender_requirement` (enum) — any | male | female
- `min_age`, `max_age` (int)
- `qualifications`, `responsibilities`, `benefits` (text)
- `ai_interview_enabled` (bool)
- `ai_interview_questions_count`, `ai_interview_duration_seconds`, `ai_interview_deadline_days` (int)
- `ai_interview_questions` (text)
- `status` (varchar/enum) — draft | published | archived
- `company_id` (bigint, nullable)
- `created_by` (int, FK → users.id)
- `created_at`, `updated_at` (timestamptz)

> Catatan: relasi bersifat opsional dan disimpan longgar untuk mengakomodasi variasi sumber event.
