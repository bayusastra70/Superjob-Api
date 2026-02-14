from loguru import logger
from typing import List, Dict, Any, Optional

from app.services.database import get_db_connection, release_connection


class OjtProgramService:
    def __init__(self):
        pass

    def get_programs(
        self,
        role: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Ambil daftar program OJT dengan filter opsional.
        Default hanya tampilkan status='published' untuk talent.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    p.*,
                    u.full_name as trainer_name,
                    (
                        SELECT COUNT(*) FROM ojt_applications a
                        WHERE a.program_id = p.id 
                        AND a.status NOT IN ('rejected', 'withdrawn')
                    ) as current_participants
                FROM ojt_programs p
                LEFT JOIN users u ON p.trainer_id = u.id
                WHERE 1=1
            """
            params = []

            # Filter by status (default: published)
            if status:
                query += " AND p.status = %s"
                params.append(status)

            # Filter by role
            if role:
                query += " AND p.role ILIKE %s"
                params.append(f"%{role}%")

            # Filter by location
            if location:
                query += " AND p.location ILIKE %s"
                params.append(f"%{location}%")

            # Search by title or description
            if search:
                search_term = f"%{search}%"
                query += """
                    AND (
                        p.title ILIKE %s 
                        OR p.description ILIKE %s
                        OR p.role ILIKE %s
                    )
                """
                params.extend([search_term, search_term, search_term])

            # Order dan pagination
            query += " ORDER BY p.created_at DESC"
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            programs = cursor.fetchall()

            return [dict(row) for row in programs]

        except Exception as e:
            logger.error(f"Error getting OJT programs: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_programs_count(
        self,
        role: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        """Hitung total program OJT (untuk pagination)"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT COUNT(*) as total
                FROM ojt_programs p
                WHERE 1=1
            """
            params = []

            if status:
                query += " AND p.status = %s"
                params.append(status)

            if role:
                query += " AND p.role ILIKE %s"
                params.append(f"%{role}%")

            if location:
                query += " AND p.location ILIKE %s"
                params.append(f"%{location}%")

            if search:
                search_term = f"%{search}%"
                query += """
                    AND (
                        p.title ILIKE %s 
                        OR p.description ILIKE %s
                        OR p.role ILIKE %s
                    )
                """
                params.extend([search_term, search_term, search_term])

            cursor.execute(query, params)
            result = cursor.fetchone()

            return result["total"] if result else 0

        except Exception as e:
            logger.error(f"Error counting OJT programs: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_program_by_id(self, program_id: int) -> Optional[Dict[str, Any]]:
        """Ambil detail 1 program OJT berdasarkan ID"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    p.*,
                    u.full_name as trainer_name,
                    (
                        SELECT COUNT(*) FROM ojt_applications a
                        WHERE a.program_id = p.id 
                        AND a.status NOT IN ('rejected', 'withdrawn')
                    ) as current_participants
                FROM ojt_programs p
                LEFT JOIN users u ON p.trainer_id = u.id
                WHERE p.id = %s
            """

            cursor.execute(query, (program_id,))
            program = cursor.fetchone()

            return dict(program) if program else None

        except Exception as e:
            logger.error(f"Error getting OJT program {program_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)
