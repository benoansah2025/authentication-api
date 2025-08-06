import psycopg2
from psycopg2.extras import RealDictCursor
from decouple import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    'host': config('DB_HOST', default='localhost'),
    'port': config('DB_PORT', default='5432', cast=int),
    'database': config('DB_NAME', default='flutter_auth_db'),
    'user': config('DB_USER'),
    'password': config('DB_PASSWORD')
}

class DatabaseConnection:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            self.connection.autocommit = False
            logger.info("Database connection established successfully")
            return self.connection
        except psycopg2.Error as e:
            logger.error(f"Error connecting to PostgreSQL database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def get_cursor(self):
        """Get database cursor with RealDictCursor for dictionary-like results"""
        if not self.connection or self.connection.closed:
            self.connect()
        return self.connection.cursor(cursor_factory=RealDictCursor)
    
    def commit(self):
        """Commit current transaction"""
        if self.connection:
            self.connection.commit()
    
    def rollback(self):
        """Rollback current transaction"""
        if self.connection:
            self.connection.rollback()

# Global database instance
db = DatabaseConnection()

def get_db_connection():
    """Dependency function to get database connection"""
    try:
        db.connect()
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        db.disconnect()