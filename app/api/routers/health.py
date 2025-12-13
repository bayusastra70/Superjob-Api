from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from app.services.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) as user_count FROM users")
        user_count = cursor.fetchone()['user_count']
        cursor.close()
        
        return {
            "status": "healthy", 
            "database": "connected",
            "users_count": user_count
        }
    except Exception as e:
        return {
            "status": "unhealthy", "database": "disconnected", "error": str(e)
            }