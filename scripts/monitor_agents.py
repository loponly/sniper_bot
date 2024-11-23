import redis
import json
import time
from datetime import datetime
import os
import argparse

class AgentMonitor:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=True
        )
        
    def monitor_messages(self, channels):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(channels)
        
        print(f"Monitoring channels: {', '.join(channels)}")
        print("-" * 50)
        
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    self._process_message(message)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            
    def _process_message(self, message):
        channel = message['channel']
        try:
            data = json.loads(message['data'])
            timestamp = datetime.fromisoformat(data['timestamp'])
            
            print(f"\nChannel: {channel}")
            print(f"Time: {timestamp}")
            
            if 'error' in data:
                print(f"ERROR: {data['error']}")
            elif 'result' in data:
                print(f"Result: {data['result']}")
            elif 'results' in data:
                print(f"Analysis: {data['results']}")
                
            print("-" * 50)
        except Exception as e:
            print(f"Error processing message: {e}")

def main():
    parser = argparse.ArgumentParser(description='Monitor trading agents')
    parser.add_argument('--host', default='localhost', help='Redis host')
    parser.add_argument('--port', type=int, default=6379, help='Redis port')
    args = parser.parse_args()
    
    channels = [
        'market_analysis',
        'execution_results',
        'execution_errors',
        'analysis_errors'
    ]
    
    monitor = AgentMonitor(args.host, args.port)
    monitor.monitor_messages(channels)

if __name__ == '__main__':
    main() 