import asyncio
import logging
from typing import Dict, Any
import redis
import json
from datetime import datetime
from huggingface_hub import snapshot_download
import os

# Import agents
from src.agents.strategy_manager_agent import StrategyManagerAgent
from src.agents.strategy_optimizer_agent import StrategyOptimizerAgent
from src.agents.code_executor_agent import CodeExecutorAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        # Initialize agents
        self.strategy_manager = StrategyManagerAgent(self.redis_client)
        self.strategy_optimizer = StrategyOptimizerAgent(self.redis_client)
        self.code_executor = CodeExecutorAgent(self.redis_client)
        
        # Setup communication channels
        self.channels = {
            'strategy_management': 'strategy_management',
            'optimization_requests': 'optimization_requests',
            'code_execution': 'code_execution',
            'agent_communication': 'agent_communication'
        }

    async def handle_agent_communication(self, message: Dict[str, Any]):
        """Handle inter-agent communication"""
        try:
            msg_type = message.get('type')
            data = message.get('data', {})
            
            if msg_type == 'optimize_strategy':
                # Strategy Manager requesting optimization
                await self.strategy_optimizer.optimize_strategy(
                    data['strategy_code'],
                    data['param_space'],
                    data['market_data']
                )
                
            elif msg_type == 'execute_strategy':
                # Strategy Manager requesting code execution
                await self.code_executor.execute_code(
                    data['strategy_code'],
                    data.get('context')
                )
                
            elif msg_type == 'strategy_result':
                # Code Executor reporting strategy results
                await self.strategy_manager.process_strategy_results(data)
                
            elif msg_type == 'optimization_complete':
                # Optimizer reporting optimization results
                await self.strategy_manager.update_strategy(
                    data['strategy_id'],
                    strategy_config=data['optimized_params']
                )

        except Exception as e:
            logger.error(f"Error handling agent communication: {str(e)}")
            self.publish_error('agent_communication_error', str(e))

    def publish_error(self, error_type: str, error_message: str):
        """Publish error messages to Redis"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'type': 'error',
            'error_type': error_type,
            'message': error_message
        }
        self.redis_client.publish('errors', json.dumps(message))

    async def monitor_channels(self):
        """Monitor Redis channels for agent communication"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.channels.values())
        
        logger.info("Starting agent communication monitoring...")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    await self.handle_agent_communication(data)
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    self.publish_error('message_processing_error', str(e))

    async def run_agents(self):
        """Run all agents concurrently"""
        try:
            await asyncio.gather(
                self.strategy_manager.run_continuous(),
                self.strategy_optimizer.run_continuous(),
                self.code_executor.run_continuous(),
                self.monitor_channels()
            )
        except Exception as e:
            logger.error(f"Error running agents: {str(e)}")
            self.publish_error('agent_runtime_error', str(e))

    async def health_check(self) -> Dict[str, str]:
        """Check health of all agents and services"""
        health_status = {
            'strategy_manager': 'healthy',
            'strategy_optimizer': 'healthy',
            'code_executor': 'healthy',
            'redis': 'healthy'
        }
        
        try:
            # Check Redis connection
            self.redis_client.ping()
        except Exception as e:
            health_status['redis'] = 'unhealthy'
            logger.error(f"Redis health check failed: {str(e)}")
        
        return health_status

async def main():
    try:
        orchestrator = AgentOrchestrator()
        
        # Start health check endpoint
        health_status = await orchestrator.health_check()
        if any(status == 'unhealthy' for status in health_status.values()):
            logger.error("System health check failed")
            return
        
        logger.info("Starting agent orchestration...")
        await orchestrator.run_agents()
        
    except Exception as e:
        logger.error(f"Main loop error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())