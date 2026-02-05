from typing import Optional, List, Dict, Any
from loguru import logger

from app.schemas.master_work_types import WorkTypeCreate, WorkTypeUpdate, WorkTypeResponse
from app.services.database import get_db_connection, release_connection


class MasterWorkTypesService:
    """Service for managing master work types."""
    
    async def get_all_work_types(self) -> List[WorkTypeResponse]:
        """
        Get all work types.
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
                    created_at,
                    updated_at
                FROM master_work_types 
                ORDER BY id
            """
            
            cursor.execute(query)
            work_types_data = cursor.fetchall()
            
            work_types = []
            for data in work_types_data:
                work_type_dict = dict(data)
                work_types.append(
                    WorkTypeResponse(
                        id=work_type_dict['id'],
                        name=work_type_dict['name'],
                        code=work_type_dict['code'],
                        description=work_type_dict['description'],
                        created_at=work_type_dict['created_at'],
                        updated_at=work_type_dict['updated_at']
                    )
                )
            
            return work_types

        except Exception as e:
            logger.error(f"Error getting work types: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def get_work_type_by_id(self, work_type_id: int) -> Optional[WorkTypeResponse]:
        """
        Get work type by ID.
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
                    created_at,
                    updated_at
                FROM master_work_types 
                WHERE id = %s
            """
            
            cursor.execute(query, (work_type_id,))
            data = cursor.fetchone()
            
            if not data:
                return None
            
            work_type_dict = dict(data)
            return WorkTypeResponse(
                id=work_type_dict['id'],
                name=work_type_dict['name'],
                code=work_type_dict['code'],
                description=work_type_dict['description'],
                created_at=work_type_dict['created_at'],
                updated_at=work_type_dict['updated_at']
            )

        except Exception as e:
            logger.error(f"Error getting work type {work_type_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def get_work_type_by_code(self, code: str) -> Optional[WorkTypeResponse]:
        """
        Get work type by code.
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
                    created_at,
                    updated_at
                FROM master_work_types 
                WHERE code = %s
            """
            
            cursor.execute(query, (code.upper(),))
            data = cursor.fetchone()
            
            if not data:
                return None
            
            work_type_dict = dict(data)
            return WorkTypeResponse(
                id=work_type_dict['id'],
                name=work_type_dict['name'],
                code=work_type_dict['code'],
                description=work_type_dict['description'],
                created_at=work_type_dict['created_at'],
                updated_at=work_type_dict['updated_at']
            )

        except Exception as e:
            logger.error(f"Error getting work type by code {code}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def create_work_type(self, work_type_data: WorkTypeCreate) -> Optional[WorkTypeResponse]:
        """
        Create a new work type.
        """
        try:
            # First check if code already exists
            existing = await self.get_work_type_by_code(work_type_data.code)
            if existing:
                raise ValueError(f"Work type with code '{work_type_data.code}' already exists")
            
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO master_work_types 
                (name, code, description)
                VALUES (%s, %s, %s)
                RETURNING 
                    id,
                    name,
                    code,
                    description,
                    created_at,
                    updated_at
            """
            
            cursor.execute(
                query, 
                (
                    work_type_data.name,
                    work_type_data.code.upper(),
                    work_type_data.description
                )
            )
            
            data = cursor.fetchone()
            conn.commit()
            
            if not data:
                return None
            
            work_type_dict = dict(data)
            return WorkTypeResponse(
                id=work_type_dict['id'],
                name=work_type_dict['name'],
                code=work_type_dict['code'],
                description=work_type_dict['description'],
                created_at=work_type_dict['created_at'],
                updated_at=work_type_dict['updated_at']
            )

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Error creating work type: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def update_work_type(
        self, 
        work_type_id: int, 
        work_type_data: WorkTypeUpdate
    ) -> Optional[WorkTypeResponse]:
        """
        Update an existing work type.
        """
        try:
            # First check if work type exists
            existing = await self.get_work_type_by_id(work_type_id)
            if not existing:
                return None
            
            # Check if code is being changed and conflicts with another
            if work_type_data.code and work_type_data.code != existing.code:
                code_exists = await self.get_work_type_by_code(work_type_data.code)
                if code_exists:
                    raise ValueError(f"Work type with code '{work_type_data.code}' already exists")
            
            conn = get_db_connection()
            cursor = conn.cursor()

            # Build dynamic update query
            update_fields = []
            params = []
            
            if work_type_data.name is not None:
                update_fields.append("name = %s")
                params.append(work_type_data.name)
            
            if work_type_data.code is not None:
                update_fields.append("code = %s")
                params.append(work_type_data.code.upper())
            
            if work_type_data.description is not None:
                update_fields.append("description = %s")
                params.append(work_type_data.description)
            
            # Always update updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            # Add WHERE clause
            params.append(work_type_id)
            
            query = f"""
                UPDATE master_work_types 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING 
                    id,
                    name,
                    code,
                    description,
                    created_at,
                    updated_at
            """
            
            cursor.execute(query, params)
            data = cursor.fetchone()
            conn.commit()
            
            if not data:
                return None
            
            work_type_dict = dict(data)
            return WorkTypeResponse(
                id=work_type_dict['id'],
                name=work_type_dict['name'],
                code=work_type_dict['code'],
                description=work_type_dict['description'],
                created_at=work_type_dict['created_at'],
                updated_at=work_type_dict['updated_at']
            )

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Error updating work type {work_type_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def delete_work_type(self, work_type_id: int) -> bool:
        """
        Delete a work type.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                DELETE FROM master_work_types 
                WHERE id = %s
            """
            
            cursor.execute(query, (work_type_id,))
            conn.commit()
            
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error deleting work type {work_type_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def get_active_work_types(self) -> List[WorkTypeResponse]:
        """
        Get all work types (no is_active filter since not in schema).
        """
        return await self.get_all_work_types()


# Service instance
master_work_types_service = MasterWorkTypesService()