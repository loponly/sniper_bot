import sqlite3
import logging
from typing import Any, List, Optional, Tuple, Union

class LocalDatabase:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.logger = logging.getLogger(__name__)

    def execute_query(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Union[List[Any], int, None]:
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
            elif query.strip().upper().startswith('INSERT'):
                return cursor.lastrowid
            
            return None
            
        except Exception as e:
            self.logger.error(f"Database error: {str(e)}")
            self.connection.rollback()
            raise

    def cursor(self):
        """Get a cursor object"""
        return self.connection.cursor()

    def commit(self):
        """Commit the current transaction"""
        self.connection.commit()