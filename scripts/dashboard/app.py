from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import redis
import json
import threading
import time
from datetime import datetime
import docker
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app)

# Redis connection
redis_client = redis.Redis(
    host='redis',
    port=6379,
    decode_responses=True
)

# Docker client
docker_client = docker.from_env()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/agent/<agent_type>/restart', methods=['POST'])
def restart_agent(agent_type: str):
    try:
        container_name = f"crypto-trading-agents_{agent_type}_1"
        container = docker_client.containers.get(container_name)
        container.restart()
        return jsonify({
            'status': 'success',
            'message': f'Agent {agent_type} restarted successfully'
        })
    except Exception as e:
        logger.error(f"Error restarting agent {agent_type}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/agents/start', methods=['POST'])
def start_all_agents():
    try:
        agent_statuses = {}
        for container in docker_client.containers.list(all=True):
            if any(agent in container.name for agent in ['strategy_finder', 'market_analyzer', 'strategy_executor']):
                container.start()
                agent_statuses[container.name] = 'active'
        return jsonify(agent_statuses)
    except Exception as e:
        logger.error(f"Error starting agents: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/stop', methods=['POST'])
def stop_all_agents():
    try:
        agent_statuses = {}
        for container in docker_client.containers.list():
            if any(agent in container.name for agent in ['strategy_finder', 'market_analyzer', 'strategy_executor']):
                container.stop()
                agent_statuses[container.name] = 'stopped'
        return jsonify(agent_statuses)
    except Exception as e:
        logger.error(f"Error stopping agents: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics')
def get_metrics():
    try:
        metrics = {
            'total_trades': int(redis_client.get('total_trades') or 0),
            'success_rate': float(redis_client.get('success_rate') or 0),
            'current_strategy': redis_client.get('current_strategy') or '-',
            'portfolio_value': float(redis_client.get('portfolio_value') or 0)
        }
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check() -> Dict:
    try:
        health_status = {
            'agents': {},
            'redis': 'unknown',
            'system': 'healthy'
        }
        
        # Check agent containers
        for container in docker_client.containers.list():
            if any(agent in container.name for agent in ['strategy_finder', 'market_analyzer', 'strategy_executor']):
                health_status['agents'][container.name] = container.status
                
        # Check Redis
        if redis_client.ping():
            health_status['redis'] = 'healthy'
        else:
            health_status['redis'] = 'unhealthy'
            health_status['system'] = 'degraded'
            
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        return jsonify({
            'system': 'unhealthy',
            'error': str(e)
        }), 500

def redis_listener():
    pubsub = redis_client.pubsub()
    channels = [
        'market_analysis',
        'execution_results',
        'execution_errors',
        'analysis_errors'
    ]
    pubsub.subscribe(channels)
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                data['channel'] = message['channel']
                socketio.emit('agent_update', data)
            except Exception as e:
                logger.error(f"Error processing message: {e}")

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

if __name__ == '__main__':
    # Start Redis listener in background
    thread = threading.Thread(target=redis_listener)
    thread.daemon = True
    thread.start()
    
    # Run Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 