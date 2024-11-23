import logging
from typing import Dict, List, Any, Optional
import redis
import json
from datetime import datetime
import pandas as pd
from src.backtesting.backtester import Backtester

class StrategyManagerAgent:
    def __init__(self, redis_client: redis.Redis):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.redis_client = redis_client
        self.strategies = {}
        self.backtest_results = {}
        
    async def add_strategy(self, strategy_code: str, strategy_config: Dict[str, Any]) -> bool:
        """Add new strategy to the pool"""
        try:
            strategy_id = f"strategy_{len(self.strategies) + 1}"
            
            # Validate strategy through backtesting
            validation_result = await self.validate_strategy(strategy_code, strategy_config)
            
            if validation_result['success']:
                self.strategies[strategy_id] = {
                    'code': strategy_code,
                    'config': strategy_config,
                    'performance': validation_result['performance'],
                    'created_at': datetime.now().isoformat()
                }
                
                # Publish strategy addition
                self.publish_event('strategy_added', {
                    'strategy_id': strategy_id,
                    'performance': validation_result['performance']
                })
                
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding strategy: {str(e)}")
            return False

    async def remove_strategy(self, strategy_id: str) -> bool:
        """Remove strategy from pool"""
        try:
            if strategy_id in self.strategies:
                del self.strategies[strategy_id]
                
                # Publish strategy removal
                self.publish_event('strategy_removed', {
                    'strategy_id': strategy_id
                })
                
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing strategy: {str(e)}")
            return False

    async def update_strategy(self, strategy_id: str, 
                            strategy_code: Optional[str] = None, 
                            strategy_config: Optional[Dict] = None) -> bool:
        """Update existing strategy"""
        try:
            if strategy_id not in self.strategies:
                return False
                
            current_strategy = self.strategies[strategy_id]
            
            # Update code and/or config
            if strategy_code:
                current_strategy['code'] = strategy_code
            if strategy_config:
                current_strategy['config'].update(strategy_config)
                
            # Revalidate strategy
            validation_result = await self.validate_strategy(
                current_strategy['code'],
                current_strategy['config']
            )
            
            if validation_result['success']:
                current_strategy['performance'] = validation_result['performance']
                current_strategy['updated_at'] = datetime.now().isoformat()
                
                # Publish strategy update
                self.publish_event('strategy_updated', {
                    'strategy_id': strategy_id,
                    'performance': validation_result['performance']
                })
                
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating strategy: {str(e)}")
            return False

    async def validate_strategy(self, strategy_code: str, 
                              strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate strategy through backtesting"""
        try:
            # Get historical data for backtesting
            historical_data = await self.get_historical_data(
                strategy_config.get('symbol', 'BTCUSDT'),
                strategy_config.get('interval', '1h'),
                strategy_config.get('lookback_days', 30)
            )
            
            # Create backtester instance
            backtester = Backtester(
                data=historical_data,
                initial_capital=10000,
                commission=0.001
            )
            
            # Run backtest
            results = await backtester.run_strategy(strategy_code, strategy_config)
            
            # Store backtest results
            backtest_id = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.backtest_results[backtest_id] = results
            
            # Calculate performance metrics
            performance = {
                'total_return': results['total_return'],
                'sharpe_ratio': results['sharpe_ratio'],
                'max_drawdown': results['max_drawdown'],
                'win_rate': results['win_rate']
            }
            
            return {
                'success': True,
                'performance': performance,
                'backtest_id': backtest_id
            }
            
        except Exception as e:
            self.logger.error(f"Error validating strategy: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def optimize_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Optimize strategy parameters"""
        try:
            if strategy_id not in self.strategies:
                return {'success': False, 'error': 'Strategy not found'}
                
            strategy = self.strategies[strategy_id]
            
            # Define parameter ranges for optimization
            param_ranges = self.get_parameter_ranges(strategy['config'])
            
            # Run optimization
            best_params = await self.grid_search(
                strategy['code'],
                param_ranges,
                strategy['config']
            )
            
            # Update strategy with optimized parameters
            await self.update_strategy(
                strategy_id,
                strategy_config=best_params
            )
            
            return {
                'success': True,
                'optimized_params': best_params
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing strategy: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish strategy management events to Redis"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        self.redis_client.publish('strategy_management', json.dumps(message))

    async def run_continuous(self):
        """Run continuous strategy management"""
        self.logger.info("Starting Strategy Manager Agent")
        
        while True:
            try:
                # Check for strategy management commands
                command_data = self.redis_client.brpop('strategy_commands', timeout=1)
                
                if command_data:
                    _, command_str = command_data
                    command = json.loads(command_str)
                    
                    # Process commands
                    if command['action'] == 'add':
                        await self.add_strategy(
                            command['code'],
                            command['config']
                        )
                    elif command['action'] == 'remove':
                        await self.remove_strategy(command['strategy_id'])
                    elif command['action'] == 'update':
                        await self.update_strategy(
                            command['strategy_id'],
                            command.get('code'),
                            command.get('config')
                        )
                    elif command['action'] == 'optimize':
                        await self.optimize_strategy(command['strategy_id'])
                
                # Periodically optimize all strategies
                await self.optimize_all_strategies()
                
            except Exception as e:
                self.logger.error(f"Error in strategy management loop: {str(e)}")
                self.publish_event('error', {'error': str(e)}) 