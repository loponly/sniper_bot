import sqlite3
import os
import logging

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._ensure_db_directory()
        self.connection = self._create_connection()
        self._init_database()
        self.logger = logging.getLogger(__name__)

    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _create_connection(self):
        """Create a database connection"""
        return sqlite3.connect(self.db_path)

    def _init_database(self):
        """Initialize database with required tables"""
        cursor = self.connection.cursor()
        
        # Create executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                error TEXT
            )
        ''')
        
        # Create code_executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                params TEXT,
                result TEXT,
                status TEXT NOT NULL,
                execution_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                error TEXT,
                stdout TEXT,
                stderr TEXT
            )
        ''')
        
        self.connection.commit()

    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self.connection.commit()
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            elif 'RETURNING' in query.upper():
                return cursor.fetchone()[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Database error: {str(e)}")
            self.connection.rollback()
            raise

    def get_connection(self):
        """Get the database connection"""
        return self.connection

    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close() 