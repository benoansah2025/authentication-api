import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
import logging
from models import UserCreate, UserUpdate, UserResponse
from auth import auth_manager
from database import DatabaseConnection

logger = logging.getLogger(__name__)

class UserService:
    """Service class for user CRUD operations"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> dict:
        """Create a new user in the database"""
        try:
            cursor = self.db.get_cursor()
            
            # Check if username, email, or phone number already exists
            check_query = """
                SELECT username, email, phone_number 
                FROM users 
                WHERE username = %s OR email = %s OR phone_number = %s
            """
            cursor.execute(check_query, (user_data.username, user_data.email, user_data.phone_number))
            existing_user = cursor.fetchone()
            
            if existing_user:
                if existing_user['username'] == user_data.username:
                    raise ValueError("Username already exists")
                elif existing_user['email'] == user_data.email:
                    raise ValueError("Email already exists")
                elif existing_user['phone_number'] == user_data.phone_number:
                    raise ValueError("Phone number already exists")
            
            # Hash the password
            hashed_password = auth_manager.hash_password(user_data.password)
            
            # Insert new user
            insert_query = """
                INSERT INTO users (username, email, phone_number, password)
                VALUES (%s, %s, %s, %s)
                RETURNING id, username, email, phone_number, created_at, updated_at
            """
            cursor.execute(insert_query, (
                user_data.username,
                user_data.email,
                user_data.phone_number,
                hashed_password
            ))
            
            new_user = cursor.fetchone()
            self.db.commit()
            
            logger.info(f"User created successfully: {user_data.username}")
            return dict(new_user)
            
        except psycopg2.Error as e:
            self.db.rollback()
            logger.error(f"Database error creating user: {e}")
            raise ValueError(f"Database error: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get a user by ID"""
        try:
            cursor = self.db.get_cursor()
            
            query = """
                SELECT id, username, email, phone_number, created_at, updated_at
                FROM users
                WHERE id = %s
            """
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            
            return dict(user) if user else None
            
        except psycopg2.Error as e:
            logger.error(f"Database error getting user by ID: {e}")
            raise ValueError(f"Database error: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get a user by username (includes password for authentication)"""
        try:
            cursor = self.db.get_cursor()
            
            query = """
                SELECT id, username, email, phone_number, password, created_at, updated_at
                FROM users
                WHERE username = %s
            """
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            
            return dict(user) if user else None
            
        except psycopg2.Error as e:
            logger.error(f"Database error getting user by username: {e}")
            raise ValueError(f"Database error: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get a user by email"""
        try:
            cursor = self.db.get_cursor()
            
            query = """
                SELECT id, username, email, phone_number, created_at, updated_at
                FROM users
                WHERE email = %s
            """
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            
            return dict(user) if user else None
            
        except psycopg2.Error as e:
            logger.error(f"Database error getting user by email: {e}")
            raise ValueError(f"Database error: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """Get all users with pagination"""
        try:
            cursor = self.db.get_cursor()
            
            query = """
                SELECT id, username, email, phone_number, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (limit, offset))
            users = cursor.fetchall()
            
            return [dict(user) for user in users]
            
        except psycopg2.Error as e:
            logger.error(f"Database error getting all users: {e}")
            raise ValueError(f"Database error: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[dict]:
        """Update user information"""
        try:
            cursor = self.db.get_cursor()
            
            # Build dynamic update query
            update_fields = []
            values = []
            
            if user_data.username is not None:
                update_fields.append("username = %s")
                values.append(user_data.username)
            
            if user_data.email is not None:
                update_fields.append("email = %s")
                values.append(user_data.email)
            
            if user_data.phone_number is not None:
                update_fields.append("phone_number = %s")
                values.append(user_data.phone_number)
            
            if user_data.password is not None:
                update_fields.append("password = %s")
                values.append(auth_manager.hash_password(user_data.password))
            
            if not update_fields:
                raise ValueError("No fields to update")
            
            values.append(user_id)
            
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, username, email, phone_number, created_at, updated_at
            """
            
            cursor.execute(query, values)
            updated_user = cursor.fetchone()
            
            if updated_user:
                self.db.commit()
                logger.info(f"User updated successfully: {user_id}")
                return dict(updated_user)
            else:
                return None
                
        except psycopg2.Error as e:
            self.db.rollback()
            logger.error(f"Database error updating user: {e}")
            raise ValueError(f"Database error: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID"""
        try:
            cursor = self.db.get_cursor()
            
            query = "DELETE FROM users WHERE id = %s RETURNING id"
            cursor.execute(query, (user_id,))
            deleted_user = cursor.fetchone()
            
            if deleted_user:
                self.db.commit()
                logger.info(f"User deleted successfully: {user_id}")
                return True
            else:
                return False
                
        except psycopg2.Error as e:
            self.db.rollback()
            logger.error(f"Database error deleting user: {e}")
            raise ValueError(f"Database error: {e}")
        finally:
            if cursor:
                cursor.close()
    
    
    
    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user"""
        try:
            # Get user by username (try username first, then email)
            user = self.get_user_by_username(username)
            
            if not user:
                # Try with email if username lookup fails
                cursor = self.db.get_cursor()
                query = """
                    SELECT id, username, email, phone_number, password, created_at, updated_at
                    FROM users
                    WHERE email = %s
                """
                cursor.execute(query, (username,))
                user = cursor.fetchone()
                if user:
                    user = dict(user)
                cursor.close()
            
            if not user:
                return None
            
            # Verify password
            if not auth_manager.verify_password(password, user['password']):
                return None
            
            # Remove password from response
            user_response = {k: v for k, v in user.items() if k != 'password'}
            return user_response
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None