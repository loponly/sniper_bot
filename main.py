import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from src.utils.local_db import LocalDatabase

# Load configuration
load_dotenv('config.env')

# Setup logging with file rotation
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log', maxBytes=1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ResourceManager:
    """Manage system resources"""
    def __init__(self):
        self.memory_limit = os.getenv('MEMORY_LIMIT', '256m')
        self.cpu_limit = float(os.getenv('CPU_LIMIT', '0.2'))
        
    async def check_resources(self) -> Dict[str, Any]:
        """Check current resource usage"""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except Exception as e:
            logger.error(f"Error checking resources: {str(e)}")
            return {}

class TradingMode:
    def __init__(self):
        self.api_key: Optional[str] = os.getenv('BINANCE_API_KEY')
        self.api_secret: Optional[str] = os.getenv('BINANCE_API_SECRET')
        self.is_dry_run: bool = not (self.api_key and self.api_secret)
        self.initial_balance: float = float(os.getenv('INITIAL_BALANCE', 10000.0))
        
    @property
    def mode(self) -> str:
        return "DRY_RUN" if self.is_dry_run else "LIVE"

class AgentOrchestrator:
    def __init__(self):
        self.trading_mode = TradingMode()
        self.db = LocalDatabase()
        self.resources = ResourceManager()
        
        # Initialize single agent based on configuration
        self.agent_type = os.getenv('AGENT_TYPE', 'strategy_manager')
        self.agent = self._create_agent(self.agent_type)
        
        # Initialize trading mode and balance
        if self.trading_mode.is_dry_run:
            self.db.execute_query(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                ('trading_mode', 'DRY_RUN')
            )
            self.db.execute_query(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                ('simulated_balance', str(self.trading_mode.initial_balance))
            )
            logger.info(f"Starting in DRY RUN mode with {self.trading_mode.initial_balance} USDT")
        else:
            self.db.execute_query(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                ('trading_mode', 'LIVE')
            )
            logger.info("Starting in LIVE mode with Binance API")

    def _create_agent(self, agent_type: str):
        """Create single agent based on type"""
        if agent_type == 'strategy_manager':
            from src.agents.strategy_manager_agent import StrategyManagerAgent
            return StrategyManagerAgent(self.db, self.trading_mode)
        elif agent_type == 'strategy_optimizer':
            from src.agents.strategy_optimizer_agent import StrategyOptimizerAgent
            return StrategyOptimizerAgent(self.db, self.trading_mode)
        elif agent_type == 'code_executor':
            from src.agents.code_executor_agent import CodeExecutorAgent
            return CodeExecutorAgent(self.db, self.trading_mode)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    async def run(self):
        """Run single agent with resource monitoring"""
        try:
            while True:
                # Check resources before running agent
                resources = await self.resources.check_resources()
                if resources.get('memory_percent', 0) > 90 or resources.get('cpu_percent', 0) > 90:
                    logger.warning("High resource usage detected, waiting...")
                    await asyncio.sleep(30)
                    continue

                # Run agent
                await self.agent.run_continuous()
                
                # Short sleep to prevent tight loop
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in agent execution: {str(e)}")
            self.db.execute_query(
                "INSERT INTO errors (error_type, message, timestamp) VALUES (?, ?, ?)",
                ('execution_error', str(e), datetime.now().isoformat())
            )

    async def health_check(self) -> Dict[str, str]:
        """Check system health"""
        try:
            health_status = {
                'agent': 'healthy',
                'database': 'healthy',
                'resources': 'healthy'
            }
            
            # Check database
            try:
                self.db.execute_query("SELECT 1")
            except Exception as e:
                health_status['database'] = 'unhealthy'
                logger.error(f"Database health check failed: {str(e)}")
            
            # Check resources
            resources = await self.resources.check_resources()
            if any(v > 90 for v in resources.values()):
                health_status['resources'] = 'warning'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return {'error': str(e)}

async def main():
    try:
        orchestrator = AgentOrchestrator()
        
        # Check system health
        health_status = await orchestrator.health_check()
        if 'unhealthy' in health_status.values():
            logger.error("System health check failed")
            return
        
        logger.info(f"Starting agent orchestration with type: {orchestrator.agent_type}")
        await orchestrator.run()
        
    except Exception as e:
        logger.error(f"Main loop error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())