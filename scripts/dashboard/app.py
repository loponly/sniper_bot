from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime
import os
import logging
from typing import Dict, Any

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect('/app/data/trading.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Dashboard home page"""
    return render_template('index.html')

@app.route('/api/agents/status')
def get_agents_status():
    """Get status of all agents"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get agent statuses
            cursor.execute("""
                SELECT agent_type, status, last_active
                FROM agent_status
                ORDER BY last_active DESC
            """)
            agents = cursor.fetchall()
            
            return jsonify({
                'status': 'success',
                'data': [dict(agent) for agent in agents]
            })
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/strategies')
def get_strategies():
    """Get all strategies"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM strategies ORDER BY created_at DESC')
            strategies = cursor.fetchall()
            return jsonify({
                'status': 'success',
                'data': [dict(strategy) for strategy in strategies]
            })
    except Exception as e:
        logger.error(f"Error getting strategies: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/executions')
def get_executions():
    """Get recent code executions"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM code_executions 
                ORDER BY execution_time DESC 
                LIMIT 10
            ''')
            executions = cursor.fetchall()
            return jsonify({
                'status': 'success',
                'data': [dict(execution) for execution in executions]
            })
    except Exception as e:
        logger.error(f"Error getting executions: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/metrics')
def get_metrics():
    """Get system metrics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get strategy counts
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM strategies 
                GROUP BY status
            """)
            strategy_counts = dict(cursor.fetchall())
            
            # Get execution success rate
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful
                FROM code_executions
            """)
            execution_stats = dict(cursor.fetchone())
            
            return jsonify({
                'status': 'success',
                'data': {
                    'strategies': strategy_counts,
                    'executions': execution_stats
                }
            })
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 