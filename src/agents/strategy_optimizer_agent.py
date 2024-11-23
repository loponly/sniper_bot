import logging
from typing import Dict, List, Any, Optional, Tuple
import redis
import json
from datetime import datetime
import pandas as pd
import numpy as np
from itertools import product
from concurrent.futures import ThreadPoolExecutor
from sklearn.model_selection import TimeSeriesSplit
import optuna
from src.backtesting.backtester import Backtester

class StrategyOptimizerAgent:
    def __init__(self, redis_client: redis.Redis):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.redis_client = redis_client
        self.optimization_results = {}
        self.current_study = None
        
    async def optimize_strategy(self, 
                              strategy_code: str, 
                              param_space: Dict[str, Any],
                              market_data: pd.DataFrame,
                              optimization_method: str = 'bayesian',
                              n_trials: int = 100,
                              cv_folds: int = 5) -> Dict[str, Any]:
        """
        Optimize strategy using either grid search or Bayesian optimization
        """
        try:
            if optimization_method == 'grid':
                return await self._grid_search_optimization(
                    strategy_code, 
                    param_space, 
                    market_data,
                    cv_folds
                )
            else:
                return await self._bayesian_optimization(
                    strategy_code,
                    param_space,
                    market_data,
                    n_trials,
                    cv_folds
                )
                
        except Exception as e:
            self.logger.error(f"Optimization error: {str(e)}")
            return {'error': str(e)}

    async def _bayesian_optimization(self,
                                   strategy_code: str,
                                   param_space: Dict[str, Any],
                                   market_data: pd.DataFrame,
                                   n_trials: int,
                                   cv_folds: int) -> Dict[str, Any]:
        """
        Perform Bayesian optimization using Optuna
        """
        def objective(trial):
            params = {}
            for param_name, param_config in param_space.items():
                if param_config['type'] == 'int':
                    params[param_name] = trial.suggest_int(
                        param_name,
                        param_config['low'],
                        param_config['high']
                    )
                elif param_config['type'] == 'float':
                    params[param_name] = trial.suggest_float(
                        param_name,
                        param_config['low'],
                        param_config['high'],
                        log=param_config.get('log', False)
                    )
                elif param_config['type'] == 'categorical':
                    params[param_name] = trial.suggest_categorical(
                        param_name,
                        param_config['choices']
                    )
            
            # Cross-validation
            tscv = TimeSeriesSplit(n_splits=cv_folds)
            scores = []
            
            for train_idx, test_idx in tscv.split(market_data):
                train_data = market_data.iloc[train_idx]
                test_data = market_data.iloc[test_idx]
                
                # Run backtest on test set
                result = self._backtest_strategy(
                    strategy_code,
                    params,
                    train_data,
                    test_data
                )
                
                scores.append(result['sharpe_ratio'])
            
            return np.mean(scores)

        # Create and run Optuna study
        study = optuna.create_study(direction='maximize')
        self.current_study = study
        study.optimize(objective, n_trials=n_trials)
        
        # Get best parameters and results
        best_params = study.best_params
        best_value = study.best_value
        
        # Run final backtest with best parameters
        final_result = self._backtest_strategy(
            strategy_code,
            best_params,
            market_data,
            market_data
        )
        
        optimization_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        results = {
            'optimization_id': optimization_id,
            'method': 'bayesian',
            'best_params': best_params,
            'best_score': best_value,
            'performance': final_result,
            'study_trials': len(study.trials),
            'optimization_history': [
                {
                    'trial': t.number,
                    'params': t.params,
                    'value': t.value
                }
                for t in study.trials
            ]
        }
        
        self.optimization_results[optimization_id] = results
        self.publish_optimization_result(results)
        
        return results

    def _backtest_strategy(self,
                          strategy_code: str,
                          params: Dict[str, Any],
                          train_data: pd.DataFrame,
                          test_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run backtest with specific parameters
        """
        try:
            # Initialize backtester
            backtester = Backtester(
                data=test_data,
                initial_capital=10000,
                commission=0.001
            )
            
            # Inject parameters into strategy code
            parameterized_code = self._inject_parameters(strategy_code, params)
            
            # Run backtest
            results = backtester.run_strategy(parameterized_code)
            
            # Calculate additional metrics
            metrics = self._calculate_metrics(results)
            
            return {
                'params': params,
                'sharpe_ratio': metrics['sharpe_ratio'],
                'total_return': metrics['total_return'],
                'max_drawdown': metrics['max_drawdown'],
                'win_rate': metrics['win_rate'],
                'profit_factor': metrics['profit_factor'],
                'recovery_factor': metrics['recovery_factor']
            }
            
        except Exception as e:
            self.logger.error(f"Backtest error: {str(e)}")
            return {
                'sharpe_ratio': -np.inf,
                'error': str(e)
            }

    def _calculate_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate comprehensive trading metrics
        """
        returns = pd.Series(results['returns'])
        
        metrics = {
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'total_return': returns.sum(),
            'max_drawdown': self._calculate_max_drawdown(returns),
            'win_rate': len(returns[returns > 0]) / len(returns),
            'profit_factor': abs(returns[returns > 0].sum() / returns[returns < 0].sum()),
            'recovery_factor': returns.sum() / self._calculate_max_drawdown(returns)
        }
        
        return metrics

    def publish_optimization_result(self, results: Dict[str, Any]):
        """
        Publish optimization results to Redis
        """
        message = {
            'timestamp': datetime.now().isoformat(),
            'type': 'optimization_result',
            'data': results
        }
        self.redis_client.publish('strategy_optimization', json.dumps(message))

    async def run_continuous(self):
        """
        Run continuous optimization monitoring
        """
        self.logger.info("Starting Strategy Optimizer Agent")
        
        while True:
            try:
                # Check for optimization requests
                request_data = self.redis_client.brpop('optimization_requests', timeout=1)
                
                if request_data:
                    _, request_str = request_data
                    request = json.loads(request_str)
                    
                    # Run optimization
                    results = await self.optimize_strategy(
                        request['strategy_code'],
                        request['param_space'],
                        pd.DataFrame(request['market_data']),
                        request.get('optimization_method', 'bayesian'),
                        request.get('n_trials', 100),
                        request.get('cv_folds', 5)
                    )
                    
                    # Store results
                    self.redis_client.setex(
                        f"optimization_result:{results['optimization_id']}",
                        3600,  # expire in 1 hour
                        json.dumps(results)
                    )
                    
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {str(e)}")
                self.publish_optimization_result({'error': str(e)}) 