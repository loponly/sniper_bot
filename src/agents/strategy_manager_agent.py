import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from src.utils.local_db import LocalDatabase

class StrategyManagerAgent:
    def __init__(self, db: LocalDatabase, trading_mode):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db
        self.trading_mode = trading_mode
        self.active_strategies = {}

    async def add_strategy(self, strategy_data: Dict[str, Any]) -> int:
        """Add new strategy to database"""
        try:
            strategy_id = self.db.execute_query(
                """
                INSERT INTO strategies (name, config, status)
                VALUES (?, ?, ?)
                """,
                (
                    strategy_data['name'],
                    str(strategy_data['config']),
                    'active'
                )
            )
            self.logger.info(f"Added new strategy: {strategy_data['name']}")
            return strategy_id
        except Exception as e:
            self.logger.error(f"Error adding strategy: {str(e)}")
            raise

    async def update_strategy(self, strategy_id: int, update_data: Dict[str, Any]) -> bool:
        """Update existing strategy"""
        try:
            success = self.db.update_strategy(strategy_id, update_data)
            if success:
                self.logger.info(f"Updated strategy {strategy_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error updating strategy: {str(e)}")
            return False

    async def get_active_strategies(self) -> list:
        """Get all active strategies"""
        try:
            return self.db.execute_query(
                "SELECT * FROM strategies WHERE status = 'active'"
            )
        except Exception as e:
            self.logger.error(f"Error getting active strategies: {str(e)}")
            return []

    async def execute_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """Execute a strategy"""
        try:
            strategy = self.db.execute_query(
                "SELECT * FROM strategies WHERE id = ?",
                (strategy_id,)
            )[0]

            if self.trading_mode.is_dry_run:
                # Simulate execution in dry run mode
                result = {
                    'strategy_id': strategy_id,
                    'execution_time': datetime.now().isoformat(),
                    'mode': 'DRY_RUN',
                    'simulated_result': 'Strategy execution simulated'
                }
            else:
                # Real execution logic here
                result = {
                    'strategy_id': strategy_id,
                    'execution_time': datetime.now().isoformat(),
                    'mode': 'LIVE',
                    'result': 'Strategy executed'
                }

            # Save execution result
            self.db.execute_query(
                """
                INSERT INTO strategy_executions (strategy_id, result, execution_time)
                VALUES (?, ?, ?)
                """,
                (strategy_id, str(result), datetime.now().isoformat())
            )

            return result

        except Exception as e:
            self.logger.error(f"Error executing strategy: {str(e)}")
            return {'error': str(e)}

    async def monitor_strategies(self):
        """Monitor and execute active strategies"""
        while True:
            try:
                active_strategies = await self.get_active_strategies()
                for strategy in active_strategies:
                    await self.execute_strategy(strategy['id'])
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in strategy monitoring: {str(e)}")
                await asyncio.sleep(5)

    async def run_continuous(self):
        """Run continuous strategy management"""
        self.logger.info("Starting Strategy Manager Agent")
        
        try:
            await self.monitor_strategies()
        except Exception as e:
            self.logger.error(f"Error in continuous run: {str(e)}")
            raise 