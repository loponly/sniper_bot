import sqlite3
import json
from typing import Dict, Any
import logging
from datetime import datetime
import os

class LocalDatabase:
    def __init__(self):
        self.db_path = 'data/trading.db'
        os.makedirs('data', exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create config table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create errors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    quantity REAL NOT NULL,
                    side TEXT NOT NULL,
                    status TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP,
                    pnl REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create strategies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    config TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add strategy_executions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id INTEGER NOT NULL,
                    result TEXT NOT NULL,
                    execution_time TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (strategy_id) REFERENCES strategies (id)
                )
            ''')
            
            # Add optimization_results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id INTEGER NOT NULL,
                    params TEXT NOT NULL,
                    score REAL NOT NULL,
                    optimization_time TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (strategy_id) REFERENCES strategies (id)
                )
            ''')
            
            # Add code_executions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS code_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    params TEXT,
                    result TEXT,
                    status TEXT DEFAULT 'pending',
                    execution_time TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def execute_query(self, query: str, params: tuple = None) -> Any:
        """Execute SQLite query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Database error: {str(e)}")
            raise

    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """Save trade to database"""
        query = '''
            INSERT INTO trades (
                symbol, entry_price, quantity, side, 
                status, strategy, entry_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            trade_data['symbol'],
            trade_data['entry_price'],
            trade_data['quantity'],
            trade_data['side'],
            trade_data['status'],
            trade_data['strategy'],
            trade_data['entry_time']
        )
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def get_active_trades(self) -> list:
        """Get all active trades"""
        query = "SELECT * FROM trades WHERE status = 'open'"
        return self.execute_query(query)

    def update_trade(self, trade_id: int, update_data: Dict[str, Any]) -> bool:
        """Update existing trade"""
        set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
        query = f"UPDATE trades SET {set_clause} WHERE id = ?"
        
        params = tuple(update_data.values()) + (trade_id,)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0 

    def update_strategy(self, strategy_id: int, update_data: Dict[str, Any]) -> bool:
        """Update strategy in database"""
        try:
            set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
            query = f"UPDATE strategies SET {set_clause} WHERE id = ?"
            
            params = tuple(update_data.values()) + (strategy_id,)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating strategy: {str(e)}")
            return False