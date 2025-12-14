# Superjob Corporate API - ERD (ringkas)

Fokus penambahan: tabel `activity_logs` untuk feed notifikasi/aktivitas.

## activity_logs
- `id` (bigint, PK, auto)
- `employer_id` (uuid, wajib) — pemilik log.
- `type` (enum `activity_type`) — `new_applicant` | `status_update` | `new_message` | `job_performance_alert` | `system_event`.
- `title` (varchar) — judul singkat.
- `subtitle` (text, opsional) — detail ringkas.
- `meta_data` (jsonb, default `{}`) — payload fleksibel per tipe event.
- `job_id` (uuid, nullable) — referensi ke lowongan (mis. `job_postings.id` atau sumber lain).
- `applicant_id` (int, nullable) — referensi ke `candidate_application.id`.
- `message_id` (varchar(36), nullable) — referensi ke pesan/percakapan.
- `timestamp` (timestamptz, default `now()`).
- `is_read` (bool, default `false`).

## Relasi/Referensi
- `activity_logs.job_id` → lowongan (UUID) bila event terkait pekerjaan.
- `activity_logs.applicant_id` → `candidate_application.id` bila event terkait pelamar.
- `activity_logs.message_id` → pesan/chat (varchar(36)) bila event berupa pesan baru.

> Catatan: relasi bersifat opsional dan disimpan longgar untuk mengakomodasi variasi sumber event.
