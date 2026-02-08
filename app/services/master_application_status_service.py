from typing import Optional, List, Dict, Any
from loguru import logger

from app.schemas.master_application_status import (
    ApplicationStatusCreate, 
    ApplicationStatusUpdate, 
    ApplicationStatusResponse
)
from app.services.database import get_db_connection, release_connection


class MasterApplicationStatusService:
    """Service for managing master application statuses."""
    
    async def get_all_application_statuses(self) -> List[ApplicationStatusResponse]:
        """
        Get all application statuses sorted by display_order.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    id,
                    name,
                    code,
                    description,
                    display_order,
                    created_at,
                    updated_at
                FROM master_application_status 
                ORDER BY display_order, id
            """
            
            cursor.execute(query)
            statuses_data = cursor.fetchall()
            
            statuses = []
            for data in statuses_data:
                status_dict = dict(data)
                statuses.append(
                    ApplicationStatusResponse(
                        id=status_dict['id'],
                        name=status_dict['name'],
                        code=status_dict['code'],
                        description=status_dict['description'],
                        display_order=status_dict['display_order'] or 0,
                        created_at=status_dict['created_at'],
                        updated_at=status_dict['updated_at']
                    )
                )
            
            return statuses

        except Exception as e:
            logger.error(f"Error getting application statuses: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def get_application_status_by_id(self, status_id: int) -> Optional[ApplicationStatusResponse]:
        """
        Get application status by ID.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    id,
                    name,
                    code,
                    description,
                    display_order,
                    created_at,
                    updated_at
                FROM master_application_status 
                WHERE id = %s
            """
            
            cursor.execute(query, (status_id,))
            data = cursor.fetchone()
            
            if not data:
                return None
            
            status_dict = dict(data)
            return ApplicationStatusResponse(
                id=status_dict['id'],
                name=status_dict['name'],
                code=status_dict['code'],
                description=status_dict['description'],
                display_order=status_dict['display_order'] or 0,
                created_at=status_dict['created_at'],
                updated_at=status_dict['updated_at']
            )

        except Exception as e:
            logger.error(f"Error getting application status {status_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def get_application_status_by_code(self, code: str) -> Optional[ApplicationStatusResponse]:
        """
        Get application status by code.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    id,
                    name,
                    code,
                    description,
                    display_order,
                    created_at,
                    updated_at
                FROM master_application_status 
                WHERE code = %s
            """
            
            cursor.execute(query, (code,))
            data = cursor.fetchone()
            
            if not data:
                return None
            
            status_dict = dict(data)
            return ApplicationStatusResponse(
                id=status_dict['id'],
                name=status_dict['name'],
                code=status_dict['code'],
                description=status_dict['description'],
                display_order=status_dict['display_order'] or 0,
                created_at=status_dict['created_at'],
                updated_at=status_dict['updated_at']
            )

        except Exception as e:
            logger.error(f"Error getting application status by code {code}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def create_application_status(
        self, 
        status_data: ApplicationStatusCreate
    ) -> Optional[ApplicationStatusResponse]:
        """
        Create a new application status.
        """
        try:
            # First check if code already exists
            existing = await self.get_application_status_by_code(status_data.code)
            if existing:
                raise ValueError(f"Application status with code '{status_data.code}' already exists")
            
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO master_application_status 
                (name, code, description, display_order)
                VALUES (%s, %s, %s, %s)
                RETURNING 
                    id,
                    name,
                    code,
                    description,
                    display_order,
                    created_at,
                    updated_at
            """
            
            cursor.execute(
                query, 
                (
                    status_data.name,
                    status_data.code,
                    status_data.description,
                    status_data.display_order or 0
                )
            )
            
            data = cursor.fetchone()
            conn.commit()
            
            if not data:
                return None
            
            status_dict = dict(data)
            return ApplicationStatusResponse(
                id=status_dict['id'],
                name=status_dict['name'],
                code=status_dict['code'],
                description=status_dict['description'],
                display_order=status_dict['display_order'] or 0,
                created_at=status_dict['created_at'],
                updated_at=status_dict['updated_at']
            )

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Error creating application status: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def update_application_status(
        self, 
        status_id: int, 
        status_data: ApplicationStatusUpdate
    ) -> Optional[ApplicationStatusResponse]:
        """
        Update an existing application status.
        """
        try:
            # First check if status exists
            existing = await self.get_application_status_by_id(status_id)
            if not existing:
                return None
            
            # Check if code is being changed and conflicts with another
            if status_data.code and status_data.code != existing.code:
                code_exists = await self.get_application_status_by_code(status_data.code)
                if code_exists:
                    raise ValueError(f"Application status with code '{status_data.code}' already exists")
            
            conn = get_db_connection()
            cursor = conn.cursor()

            # Build dynamic update query
            update_fields = []
            params = []
            
            if status_data.name is not None:
                update_fields.append("name = %s")
                params.append(status_data.name)
            
            if status_data.code is not None:
                update_fields.append("code = %s")
                params.append(status_data.code)
            
            if status_data.description is not None:
                update_fields.append("description = %s")
                params.append(status_data.description)
            
            if status_data.display_order is not None:
                update_fields.append("display_order = %s")
                params.append(status_data.display_order)
            
            # Always update updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            # Add WHERE clause
            params.append(status_id)
            
            query = f"""
                UPDATE master_application_status 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING 
                    id,
                    name,
                    code,
                    description,
                    display_order,
                    created_at,
                    updated_at
            """
            
            cursor.execute(query, params)
            data = cursor.fetchone()
            conn.commit()
            
            if not data:
                return None
            
            status_dict = dict(data)
            return ApplicationStatusResponse(
                id=status_dict['id'],
                name=status_dict['name'],
                code=status_dict['code'],
                description=status_dict['description'],
                display_order=status_dict['display_order'] or 0,
                created_at=status_dict['created_at'],
                updated_at=status_dict['updated_at']
            )

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Error updating application status {status_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def delete_application_status(self, status_id: int) -> bool:
        """
        Delete an application status.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                DELETE FROM master_application_status 
                WHERE id = %s
            """
            
            cursor.execute(query, (status_id,))
            conn.commit()
            
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error deleting application status {status_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def get_active_application_statuses(self) -> List[ApplicationStatusResponse]:
        """
        Get all application statuses sorted by display_order.
        """
        return await self.get_all_application_statuses()


# Service instance
master_application_status_service = MasterApplicationStatusService()