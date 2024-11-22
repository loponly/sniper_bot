import pandas as pd
import numpy as np
from typing import List, Dict, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
from src.utils.logger import setup_logger

@dataclass
class Position:
    entry_price: float
    size: float
    entry_time: pd.Timestamp
    side: str  # 'long' or 'short'

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the data
        Returns a pandas Series with values: 1 (buy), -1 (sell), 0 (hold)
        """
        pass

class Backtester:
    def __init__(
        self,
        data: pd.DataFrame,
        strategy: Strategy,
        initial_capital: float = 10000,
        commission: float = 0.001
    ):
        """
        Initialize backtester with OHLCV data and strategy
        
        Parameters:
        - data: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        - strategy: Strategy instance
        - initial_capital: Starting capital
        - commission: Trading commission (e.g., 0.001 for 0.1%)
        """
        self.data = data
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.logger = setup_logger(self.__class__.__name__)
        self.reset()
        
    def reset(self):
        """Reset backtest state"""
        self.current_position = None
        self.trades = []
        self.equity_curve = []
        
    def run(self) -> Dict:
        """Run backtest and return performance metrics"""
        capital = self.initial_capital
        self.equity_curve = [capital]
        
        try:
            signals = self.strategy.generate_signals(self.data)
            
            for i in range(1, len(self.data)):
                current_price = self.data['close'].iloc[i]
                signal = signals.iloc[i]
                
                # Handle position entry
                if signal == 1 and self.current_position is None:  # Buy signal
                    position_size = capital / current_price
                    cost = position_size * current_price * (1 + self.commission)
                    if cost <= capital:
                        self.current_position = Position(
                            entry_price=current_price,
                            size=position_size,
                            entry_time=self.data.index[i],
                            side='long'
                        )
                        capital -= cost
                
                # Handle position exit
                elif signal == -1 and self.current_position is not None:  # Sell signal
                    exit_value = self.current_position.size * current_price
                    capital += exit_value * (1 - self.commission)
                    self.trades.append({
                        'entry_time': self.current_position.entry_time,
                        'exit_time': self.data.index[i],
                        'entry_price': self.current_position.entry_price,
                        'exit_price': current_price,
                        'pnl': exit_value - (self.current_position.size * self.current_position.entry_price),
                        'return': (current_price - self.current_position.entry_price) / self.current_position.entry_price
                    })
                    self.current_position = None
                
                # Update equity curve
                current_equity = capital
                if self.current_position is not None:
                    position_value = self.current_position.size * current_price
                    current_equity += position_value
                self.equity_curve.append(current_equity)
            
            return self.calculate_metrics()
            
        except Exception as e:
            self.logger.error(f"Error during backtest: {str(e)}")
            return {}
    
    def calculate_metrics(self) -> Dict:
        """Calculate and return performance metrics"""
        equity_curve = pd.Series(self.equity_curve)
        returns = equity_curve.pct_change().dropna()
        
        trades_df = pd.DataFrame(self.trades)
        
        metrics = {
            'total_return': (equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital,
            'sharpe_ratio': np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0,
            'max_drawdown': (equity_curve / equity_curve.cummax() - 1).min(),
            'number_of_trades': len(self.trades),
            'win_rate': len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) if len(trades_df) > 0 else 0,
            'equity_curve': self.equity_curve
        }
        
        return metrics