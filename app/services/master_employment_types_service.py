from typing import Optional, List, Dict, Any
from loguru import logger

from app.schemas.master_employment_types import (
    EmploymentTypeCreate, 
    EmploymentTypeUpdate, 
    EmploymentTypeResponse
)
from app.services.database import get_db_connection, release_connection


class MasterEmploymentTypesService:
    """Service for managing master employment types."""
    
    async def get_all_employment_types(self) -> List[EmploymentTypeResponse]:
        """
        Get all employment types.
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
                FROM master_employement_types 
                ORDER BY id
            """
            
            cursor.execute(query)
            employment_types_data = cursor.fetchall()
            
            employment_types = []
            for data in employment_types_data:
                emp_type_dict = dict(data)
                employment_types.append(
                    EmploymentTypeResponse(
                        id=emp_type_dict['id'],
                        name=emp_type_dict['name'],
                        code=emp_type_dict['code'],
                        description=emp_type_dict['description'],
                        created_at=emp_type_dict['created_at'],
                        updated_at=emp_type_dict['updated_at']
                    )
                )
            
            return employment_types

        except Exception as e:
            logger.error(f"Error getting employment types: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def get_employment_type_by_id(self, employment_type_id: int) -> Optional[EmploymentTypeResponse]:
        """
        Get employment type by ID.
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
                FROM master_employement_types 
                WHERE id = %s
            """
            
            cursor.execute(query, (employment_type_id,))
            data = cursor.fetchone()
            
            if not data:
                return None
            
            emp_type_dict = dict(data)
            return EmploymentTypeResponse(
                id=emp_type_dict['id'],
                name=emp_type_dict['name'],
                code=emp_type_dict['code'],
                description=emp_type_dict['description'],
                created_at=emp_type_dict['created_at'],
                updated_at=emp_type_dict['updated_at']
            )

        except Exception as e:
            logger.error(f"Error getting employment type {employment_type_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def get_employment_type_by_code(self, code: str) -> Optional[EmploymentTypeResponse]:
        """
        Get employment type by code.
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
                FROM master_employement_types 
                WHERE code = %s
            """
            
            cursor.execute(query, (code.upper(),))
            data = cursor.fetchone()
            
            if not data:
                return None
            
            emp_type_dict = dict(data)
            return EmploymentTypeResponse(
                id=emp_type_dict['id'],
                name=emp_type_dict['name'],
                code=emp_type_dict['code'],
                description=emp_type_dict['description'],
                created_at=emp_type_dict['created_at'],
                updated_at=emp_type_dict['updated_at']
            )

        except Exception as e:
            logger.error(f"Error getting employment type by code {code}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def create_employment_type(self, employment_type_data: EmploymentTypeCreate) -> Optional[EmploymentTypeResponse]:
        """
        Create a new employment type.
        """
        try:
            # First check if code already exists
            existing = await self.get_employment_type_by_code(employment_type_data.code)
            if existing:
                raise ValueError(f"Employment type with code '{employment_type_data.code}' already exists")
            
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO master_employement_types 
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
                    employment_type_data.name,
                    employment_type_data.code.upper(),
                    employment_type_data.description
                )
            )
            
            data = cursor.fetchone()
            conn.commit()
            
            if not data:
                return None
            
            emp_type_dict = dict(data)
            return EmploymentTypeResponse(
                id=emp_type_dict['id'],
                name=emp_type_dict['name'],
                code=emp_type_dict['code'],
                description=emp_type_dict['description'],
                created_at=emp_type_dict['created_at'],
                updated_at=emp_type_dict['updated_at']
            )

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Error creating employment type: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def update_employment_type(
        self, 
        employment_type_id: int, 
        employment_type_data: EmploymentTypeUpdate
    ) -> Optional[EmploymentTypeResponse]:
        """
        Update an existing employment type.
        """
        try:
            # First check if employment type exists
            existing = await self.get_employment_type_by_id(employment_type_id)
            if not existing:
                return None
            
            # Check if code is being changed and conflicts with another
            if employment_type_data.code and employment_type_data.code != existing.code:
                code_exists = await self.get_employment_type_by_code(employment_type_data.code)
                if code_exists:
                    raise ValueError(f"Employment type with code '{employment_type_data.code}' already exists")
            
            conn = get_db_connection()
            cursor = conn.cursor()

            # Build dynamic update query
            update_fields = []
            params = []
            
            if employment_type_data.name is not None:
                update_fields.append("name = %s")
                params.append(employment_type_data.name)
            
            if employment_type_data.code is not None:
                update_fields.append("code = %s")
                params.append(employment_type_data.code.upper())
            
            if employment_type_data.description is not None:
                update_fields.append("description = %s")
                params.append(employment_type_data.description)
            
            # Always update updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            # Add WHERE clause
            params.append(employment_type_id)
            
            query = f"""
                UPDATE master_employement_types 
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
            
            emp_type_dict = dict(data)
            return EmploymentTypeResponse(
                id=emp_type_dict['id'],
                name=emp_type_dict['name'],
                code=emp_type_dict['code'],
                description=emp_type_dict['description'],
                created_at=emp_type_dict['created_at'],
                updated_at=emp_type_dict['updated_at']
            )

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Error updating employment type {employment_type_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def delete_employment_type(self, employment_type_id: int) -> bool:
        """
        Delete an employment type.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                DELETE FROM master_employement_types 
                WHERE id = %s
            """
            
            cursor.execute(query, (employment_type_id,))
            conn.commit()
            
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error deleting employment type {employment_type_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    async def get_employment_types_for_select(self) -> List[Dict[str, Any]]:
        """
        Get employment types for dropdown/select options.
        Returns simplified format: [{id, name, code}]
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    id,
                    name,
                    code
                FROM master_employement_types 
                ORDER BY name
            """
            
            cursor.execute(query)
            data = cursor.fetchall()
            
            result = []
            for row in data:
                row_dict = dict(row)
                result.append({
                    'id': row_dict['id'],
                    'name': row_dict['name'],
                    'code': row_dict['code']
                })
            
            return result

        except Exception as e:
            logger.error(f"Error getting employment types for select: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)


# Service instance
master_employment_types_service = MasterEmploymentTypesService()