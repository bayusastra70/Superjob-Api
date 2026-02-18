from loguru import logger
from typing import List, Dict, Any, Optional

from app.services.database import get_db_connection, release_connection
from app.services.ojt_agenda_service import ojt_agenda_service

class OjtDashboardService:
    def __init__(self):
        pass

    def get_talent_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Aggregate data for talent dashboard."""
        conn = None
        cursor = None
        data = {
            "active_program": None,
            "upcoming_agenda": None,
            "pending_tasks_count": 0,
            "attendance_summary": "0/0",
            "recent_tasks": []
        }
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. Get Active Program (Latest accepted application)
            program_query = """
                SELECT 
                    p.id, p.title, p.role, p.status,
                    u.full_name as trainer_name
                FROM ojt_applications app
                JOIN ojt_programs p ON app.program_id = p.id
                LEFT JOIN users u ON p.trainer_id = u.id
                WHERE app.talent_id = %s AND app.status = 'accepted'
                ORDER BY app.created_at DESC
                LIMIT 1
            """
            cursor.execute(program_query, (user_id,))
            program = cursor.fetchone()
            
            if not program:
                return data

            # Calculate Progress (Tasks completed / Total tasks)
            # This is a simple estimation
            task_stats_query = """
                SELECT 
                    COUNT(t.id) as total_tasks,
                    COUNT(s.id) as completed_tasks
                FROM ojt_tasks t
                LEFT JOIN ojt_task_submissions s ON t.id = s.task_id AND s.talent_id = %s
                WHERE t.program_id = %s
            """
            cursor.execute(task_stats_query, (user_id, program['id']))
            stats = cursor.fetchone()
            
            total_tasks = stats['total_tasks'] or 0
            completed_tasks = stats['completed_tasks'] or 0
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            data['active_program'] = {
                **dict(program),
                "progress_percentage": round(progress, 1)
            }
            data['pending_tasks_count'] = total_tasks - completed_tasks

            # 2. Get Upcoming Agenda (Nearest future session)
            agenda_query = """
                SELECT 
                    a.*,
                    u.full_name as trainer_name
                FROM ojt_agendas a
                LEFT JOIN users u ON a.trainer_id = u.id
                WHERE a.program_id = %s AND a.session_date >= NOW()
                ORDER BY a.session_date ASC
                LIMIT 1
            """
            cursor.execute(agenda_query, (program['id'],))
            agenda = cursor.fetchone()
            if agenda:
                data['upcoming_agenda'] = dict(agenda)

            # 3. Attendance Summary (Present / Total Sessions so far)
            attendance_query = """
                SELECT 
                    COUNT(a.id) as total_past_sessions,
                    COUNT(att.id) as total_attended
                FROM ojt_agendas a
                LEFT JOIN ojt_attendance att ON a.id = att.agenda_id AND att.talent_id = %s
                WHERE a.program_id = %s AND a.session_date < NOW()
            """
            cursor.execute(attendance_query, (user_id, program['id']))
            att_stats = cursor.fetchone()
            
            total_past = att_stats['total_past_sessions'] or 0
            total_attended = att_stats['total_attended'] or 0
            data['attendance_summary'] = f"{total_attended}/{total_past}"

            # 4. Recent Tasks (Limit 3)
            recent_tasks_query = """
                SELECT 
                    t.*,
                    sub.status as submission_status,
                    sub.score as my_score
                FROM ojt_tasks t
                LEFT JOIN ojt_task_submissions sub ON t.id = sub.task_id AND sub.talent_id = %s
                WHERE t.program_id = %s
                ORDER BY t.deadline ASC
                LIMIT 3
            """
            cursor.execute(recent_tasks_query, (user_id, program['id']))
            recent_tasks = cursor.fetchall()
            data['recent_tasks'] = [dict(row) for row in recent_tasks]

            return data

        except Exception as e:
            logger.error(f"Error getting dashboard data for user {user_id}: {e}")
            return data
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

ojt_dashboard_service = OjtDashboardService()
