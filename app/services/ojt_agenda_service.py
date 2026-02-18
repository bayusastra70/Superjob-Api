from loguru import logger
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.database import get_db_connection, release_connection
from app.schemas.ojt_agenda import OjtAgendaCreate

class OjtAgendaService:
    def __init__(self):
        pass

    def get_agendas_by_program(self, program_id: int, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of agendas for a program."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    a.*,
                    u.full_name as trainer_name,
                    att.status as user_attendance
                FROM ojt_agendas a
                LEFT JOIN users u ON a.trainer_id = u.id
                LEFT JOIN ojt_attendance att ON a.id = att.agenda_id AND att.talent_id = %s
                WHERE a.program_id = %s
                ORDER BY a.session_date ASC, a.order_number ASC
            """
            cursor.execute(query, (user_id, program_id))
            agendas = cursor.fetchall()

            return [dict(row) for row in agendas]

        except Exception as e:
            logger.error(f"Error getting agendas for program {program_id}: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_agenda_by_id(self, agenda_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get detail of an agenda."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    a.*,
                    u.full_name as trainer_name,
                    att.status as user_attendance,
                    att.checked_in_at
                FROM ojt_agendas a
                LEFT JOIN users u ON a.trainer_id = u.id
                LEFT JOIN ojt_attendance att ON a.id = att.agenda_id AND att.talent_id = %s
                WHERE a.id = %s
            """
            cursor.execute(query, (user_id, agenda_id))
            agenda = cursor.fetchone()

            return dict(agenda) if agenda else None

        except Exception as e:
            logger.error(f"Error getting agenda {agenda_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def record_attendance(self, agenda_id: int, talent_id: int) -> Dict[str, Any]:
        """Record attendance for a talent."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if already attended
            check_query = "SELECT id FROM ojt_attendance WHERE agenda_id = %s AND talent_id = %s"
            cursor.execute(check_query, (agenda_id, talent_id))
            existing = cursor.fetchone()

            if existing:
                return {"success": False, "message": "Attendance already recorded"}
            
            # Record attendance
            insert_query = """
                INSERT INTO ojt_attendance (agenda_id, talent_id, status, checked_in_at)
                VALUES (%s, %s, 'present', NOW())
                RETURNING id, checked_in_at
            """
            cursor.execute(insert_query, (agenda_id, talent_id))
            conn.commit()
            
            result = cursor.fetchone()
            return {
                "success": True, 
                "message": "Attendance recorded successfully", 
                "checked_in_at": result["checked_in_at"]
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"Error recording attendance: {e}")
            return {"success": False, "message": str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

ojt_agenda_service = OjtAgendaService()
