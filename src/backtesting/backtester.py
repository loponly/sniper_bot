import pandas as pd
import numpy as np
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from src.utils.logger import setup_logger
from src.types.trading_signals import TradingSignal

@dataclass
class Position:
    entry_price: np.float64
    size: np.float64
    entry_time: pd.Timestamp
    side: str  # 'long' or 'short'

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the data
        Returns a pandas Series with TradingSignal enum values
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
        self.initial_capital = np.float64(initial_capital)
        self.commission = np.float64(commission)
        self.logger = setup_logger(self.__class__.__name__)
        self.reset()
        
    def reset(self) -> None:
        """Reset backtest state"""
        self.current_position: Optional[Position] = None
        self.trades: List[Dict] = []
        self.equity_curve: List[np.float64] = []
        
    def run(self) -> Dict:
        """Run backtest and return performance metrics"""
        capital = np.float64(self.initial_capital)
        self.equity_curve = [capital]
        
        try:
            signals = self.strategy.generate_signals(self.data)
            
            for i in range(1, len(self.data)):
                current_price = np.float64(self.data['close'].iloc[i])
                signal_value = int(signals.iloc[i])
                signal = TradingSignal(signal_value)
                
                # Handle position entry
                if (signal == TradingSignal.BUY and self.current_position is None):
                    # Calculate maximum position size considering commission
                    max_position_size = np.float64(capital / (current_price * (1 + self.commission)))
                    position_size = max_position_size  # Use maximum available size
                    
                    # Calculate total cost including commission
                    cost = np.float64(position_size * current_price * (1 + self.commission))
                    
                    if cost <= capital:
                        self.current_position = Position(
                            entry_price=current_price,
                            size=position_size,
                            entry_time=self.data.index[i],
                            side='long'
                        )
                        capital -= cost
                
                # Handle position exit
                elif (signal == TradingSignal.SELL and 
                      self.current_position is not None):
                    # Calculate exit value after commission
                    gross_value = np.float64(self.current_position.size * current_price)
                    exit_value = np.float64(gross_value * (1 - self.commission))
                    capital += exit_value
                    
                    self.trades.append({
                        'entry_time': self.current_position.entry_time,
                        'exit_time': self.data.index[i],
                        'entry_price': float(self.current_position.entry_price),
                        'exit_price': float(current_price),
                        'pnl': float(exit_value - (self.current_position.size * self.current_position.entry_price * (1 + self.commission))),
                        'return': float((exit_value - (self.current_position.size * self.current_position.entry_price * (1 + self.commission))) / 
                                     (self.current_position.size * self.current_position.entry_price * (1 + self.commission)))
                    })
                    self.current_position = None
                
                # Update equity curve
                current_equity = np.float64(capital)
                if self.current_position is not None:
                    position_value = np.float64(self.current_position.size * current_price)
                    current_equity += position_value
                self.equity_curve.append(current_equity)
            
            return self.calculate_metrics()
            
        except Exception as e:
            self.logger.error(f"Error during backtest: {str(e)}")
            raise e
    
    def calculate_metrics(self) -> Dict:
        """Calculate and return performance metrics"""
        equity_curve = pd.Series(self.equity_curve)
        returns = equity_curve.pct_change().dropna()
        
        trades_df = pd.DataFrame(self.trades)
        
        metrics = {
            'total_return': float((equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital),
            'sharpe_ratio': float(np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0),
            'max_drawdown': float((equity_curve / equity_curve.cummax() - 1).min()),
            'number_of_trades': int(len(self.trades)),
            'win_rate': float(len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) if len(trades_df) > 0 else 0),
            'equity_curve': [float(x) for x in self.equity_curve]
        }
        
        return metrics