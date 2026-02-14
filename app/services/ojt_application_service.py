from loguru import logger
from typing import List, Dict, Any, Optional

from app.services.database import get_db_connection, release_connection


class OjtApplicationService:
    def __init__(self):
        pass

    def create_application(
        self,
        talent_id: int,
        program_id: int,
        motivation_letter: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Talent mendaftar ke program OJT.
        Validasi:
        1. Program harus ada dan berstatus 'published'
        2. Talent belum pernah apply ke program ini
        3. Peserta belum penuh
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            conn.autocommit = False  # Kita perlu transaction
            cursor = conn.cursor()

            # Validasi 1: Program ada dan published
            cursor.execute(
                """
                SELECT id, title, max_participants, status
                FROM ojt_programs
                WHERE id = %s
                """,
                (program_id,),
            )
            program = cursor.fetchone()

            if not program:
                return {"error": "Program OJT tidak ditemukan", "code": 404}

            if program["status"] != "published":
                return {
                    "error": "Program OJT belum dibuka untuk pendaftaran",
                    "code": 400,
                }

            # Validasi 2: Belum pernah apply
            cursor.execute(
                """
                SELECT id FROM ojt_applications
                WHERE talent_id = %s AND program_id = %s
                """,
                (talent_id, program_id),
            )
            existing = cursor.fetchone()

            if existing:
                return {
                    "error": "Anda sudah mendaftar ke program ini",
                    "code": 400,
                }

            # Validasi 3: Peserta belum penuh
            if program["max_participants"]:
                cursor.execute(
                    """
                    SELECT COUNT(*) as total FROM ojt_applications
                    WHERE program_id = %s AND status NOT IN ('rejected', 'withdrawn')
                    """,
                    (program_id,),
                )
                count = cursor.fetchone()
                if count and count["total"] >= program["max_participants"]:
                    return {
                        "error": "Program OJT sudah penuh",
                        "code": 400,
                    }

            # Semua validasi lolos → INSERT
            cursor.execute(
                """
                INSERT INTO ojt_applications (talent_id, program_id, motivation_letter)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (talent_id, program_id, motivation_letter),
            )
            new_application = cursor.fetchone()
            conn.commit()

            if new_application:
                result = dict(new_application)
                result["program_title"] = program["title"]
                return result

            return {"error": "Gagal membuat pendaftaran", "code": 500}

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating OJT application: {e}")
            return {"error": "Internal server error", "code": 500}
        finally:
            if conn:
                conn.autocommit = True
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_my_applications(
        self, talent_id: int
    ) -> List[Dict[str, Any]]:
        """Ambil semua pendaftaran OJT milik talent yang login"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    a.*,
                    p.title as program_title,
                    p.role as program_role,
                    p.location as program_location,
                    p.status as program_status
                FROM ojt_applications a
                JOIN ojt_programs p ON a.program_id = p.id
                WHERE a.talent_id = %s
                ORDER BY a.applied_at DESC
            """

            cursor.execute(query, (talent_id,))
            applications = cursor.fetchall()

            return [dict(row) for row in applications]

        except Exception as e:
            logger.error(f"Error getting OJT applications for user {talent_id}: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def register_application(
        self, application_id: int, talent_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Konfirmasi keikutsertaan OJT (setelah diterima).
        Status berubah dari 'accepted' → 'registered'.
        Validasi:
        1. Application ada dan milik talent ini
        2. Status harus 'accepted'
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Ambil application
            cursor.execute(
                """
                SELECT a.*, p.title as program_title
                FROM ojt_applications a
                JOIN ojt_programs p ON a.program_id = p.id
                WHERE a.id = %s
                """,
                (application_id,),
            )
            application = cursor.fetchone()

            if not application:
                return {"error": "Pendaftaran tidak ditemukan", "code": 404}

            if application["talent_id"] != talent_id:
                return {
                    "error": "Anda tidak memiliki akses ke pendaftaran ini",
                    "code": 403,
                }

            if application["status"] != "accepted":
                return {
                    "error": f"Status saat ini '{application['status']}', harus 'accepted' untuk bisa registrasi",
                    "code": 400,
                }

            # Update status → registered
            cursor.execute(
                """
                UPDATE ojt_applications
                SET status = 'registered', registered_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (application_id,),
            )
            updated = cursor.fetchone()
            conn.commit()

            if updated:
                result = dict(updated)
                result["program_title"] = application["program_title"]
                return result

            return {"error": "Gagal registrasi", "code": 500}

        except Exception as e:
            logger.error(f"Error registering OJT application {application_id}: {e}")
            return {"error": "Internal server error", "code": 500}
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)
