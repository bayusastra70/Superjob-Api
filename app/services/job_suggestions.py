from typing import List, Sequence

from app.models.job import Job


def _skills_count(skills: Sequence[str] | None) -> int:
    return len([s for s in (skills or []) if s])


def get_job_suggestions(job: Job) -> List[str]:
    """
    Produce improvement suggestions based on missing/incomplete fields.
    Extendable for future scoring versions.
    """
    suggestions: List[str] = []

    if not job.title:
        suggestions.append("Isi judul lowongan")

    if not job.description:
        suggestions.append("Tambahkan deskripsi pekerjaan (>=150 karakter)")
    else:
        desc_len = len(job.description.strip())
        if desc_len < 150:
            suggestions.append("Perpanjang deskripsi pekerjaan (target >=150 karakter)")

    if job.salary_min is None and job.salary_max is None:
        suggestions.append("Tambahkan rentang gaji")

    skills_len = _skills_count(job.skills)
    if skills_len == 0:
        suggestions.append("Tambahkan skill yang diminta (minimal 3)")
    elif skills_len < 3:
        suggestions.append("Lengkapi skill set (minimal 3)")

    if not job.location:
        suggestions.append("Isi lokasi pekerjaan")

    if not job.employment_type:
        suggestions.append("Isi jenis pekerjaan (full-time/part-time/contract)")

    if not job.experience_level:
        suggestions.append("Isi level atau tahun pengalaman yang dibutuhkan")

    if not job.contact_url:
        suggestions.append("Tambahkan URL kontak/aplikasi")

    if not job.benefits:
        suggestions.append("Tambahkan benefit atau info perusahaan")

    return suggestions
