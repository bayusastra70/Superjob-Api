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
        training_type: Optional[str] = None,
        duration_min: Optional[int] = None,
        duration_max: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        user_id: Optional[str] = None,
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

            # Base query columns
            columns = [
                "p.*",
                "u.full_name as trainer_name",
                "c.id as company_db_id",
                "c.name as company_name",
                "c.description as company_description",
                "c.logo_url as company_logo_url",
                "c.banner_url as company_banner_url",
                "c.industry as company_industry",
                "c.location as company_location",
                "c.website as company_website",
                """(
                    SELECT COUNT(*) FROM ojt_applications a
                    WHERE a.program_id = p.id 
                    AND a.status NOT IN ('rejected', 'withdrawn')
                ) as current_participants"""
            ]

            # Add is_registered check if user_id provided
            if user_id:
                columns.append(f"""(
                    SELECT EXISTS(
                        SELECT 1 FROM ojt_applications a
                        WHERE a.program_id = p.id 
                        AND a.talent_id = '{user_id}'
                        AND a.status != 'withdrawn'
                    )
                ) as is_registered""")
            else:
                columns.append("false as is_registered")

            query = f"""
                SELECT {', '.join(columns)}
                FROM ojt_programs p
                LEFT JOIN users u ON p.trainer_id = u.id
                LEFT JOIN companies c ON p.company_id = c.id
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

            # Filter by training_type (onsite/remote/hybrid)
            if training_type:
                query += " AND p.training_type = %s"
                params.append(training_type)

            # Filter by duration range (hari)
            if duration_min:
                query += " AND p.duration_days >= %s"
                params.append(duration_min)
            if duration_max:
                query += " AND p.duration_days <= %s"
                params.append(duration_max)

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

            return [self._build_program_dict(row) for row in programs]

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
        training_type: Optional[str] = None,
        duration_min: Optional[int] = None,
        duration_max: Optional[int] = None,
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

            if training_type:
                query += " AND p.training_type = %s"
                params.append(training_type)

            if duration_min:
                query += " AND p.duration_days >= %s"
                params.append(duration_min)
            if duration_max:
                query += " AND p.duration_days <= %s"
                params.append(duration_max)

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

    def get_program_by_id(self, program_id: int, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Ambil detail 1 program OJT berdasarkan ID"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Base columns
            columns = [
                "p.*",
                "u.full_name as trainer_name",
                "c.id as company_db_id",
                "c.name as company_name",
                "c.description as company_description",
                "c.logo_url as company_logo_url",
                "c.banner_url as company_banner_url",
                "c.industry as company_industry",
                "c.location as company_location",
                "c.website as company_website",
                """(
                    SELECT COUNT(*) FROM ojt_applications a
                    WHERE a.program_id = p.id 
                    AND a.status NOT IN ('rejected', 'withdrawn')
                ) as current_participants"""
            ]

            # Add is_registered check if user_id provided
            if user_id:
                columns.append(f"""(
                    SELECT EXISTS(
                        SELECT 1 FROM ojt_applications a
                        WHERE a.program_id = p.id 
                        AND a.talent_id = '{user_id}'
                        AND a.status != 'withdrawn'
                    )
                ) as is_registered""")
            else:
                columns.append("false as is_registered")

            query = f"""
                SELECT {', '.join(columns)}
                FROM ojt_programs p
                LEFT JOIN users u ON p.trainer_id = u.id
                LEFT JOIN companies c ON p.company_id = c.id
                WHERE p.id = %s
            """

            cursor.execute(query, (program_id,))
            program = cursor.fetchone()

            # Fetch agendas
            agenda_query = """
                SELECT * FROM ojt_agendas 
                WHERE program_id = %s
                ORDER BY session_date ASC, order_number ASC
            """
            cursor.execute(agenda_query, (program_id,))
            agendas = cursor.fetchall()
            
            # Format agendas
            agenda_list = []
            for ag in agendas:
                ad = dict(ag)
                agenda_list.append(ad)

            program_dict = self._build_program_dict(program) if program else None
            if program_dict:
                program_dict["agendas"] = agenda_list

            return program_dict

        except Exception as e:
            logger.error(f"Error getting OJT program {program_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def _build_program_dict(self, row) -> Dict[str, Any]:
        """Konversi row database ke dictionary dengan nested company object.
        
        Mengambil field company_* dari hasil JOIN dan menyusunnya
        menjadi object 'company' yang nested, sama seperti di Jobs API.
        """
        d = dict(row)

        # Bangun nested company object dari field-field hasil JOIN
        if d.get("company_id"):
            d["company"] = {
                "id": d.get("company_db_id") or d.get("company_id"),
                "name": d.get("company_name"),
                "description": d.get("company_description"),
                "logo_url": d.get("company_logo_url"),
                "banner_url": d.get("company_banner_url"),
                "industry": d.get("company_industry"),
                "location": d.get("company_location"),
                "website": d.get("company_website"),
            }
        else:
            d["company"] = None

        # Bersihkan field company_* yang sudah dipindah ke nested object
        for key in ["company_db_id", "company_name", "company_description",
                    "company_logo_url", "company_banner_url", "company_industry",
                    "company_location", "company_website"]:
            d.pop(key, None)

        return d
