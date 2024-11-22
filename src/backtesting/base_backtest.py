import pandas as pd
import numpy as np
from typing import Dict, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
from datetime import datetime
import matplotlib.pyplot as plt

@dataclass
class Position:
    entry_price: float
    size: float
    entry_time: pd.Timestamp
    side: str  # 'long' or 'short'

class BacktestResult:
    def __init__(
        self,
        equity_curve: List[float],
        trades: List[Dict],
        metrics: Dict,
        symbol: str,
        strategy_name: str,
        params: Dict
    ):
        self.equity_curve = equity_curve
        self.trades = trades
        self.metrics = metrics
        self.symbol = symbol
        self.strategy_name = strategy_name
        self.params = params
        self.timestamp = datetime.now()
    
    def save(self, filename: str = None):
        """Save backtest results to file"""
        if filename is None:
            timestamp = self.timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_results_{self.symbol}_{self.strategy_name}_{timestamp}.json"
        
        results = {
            'symbol': self.symbol,
            'strategy': self.strategy_name,
            'parameters': self.params,
            'metrics': self.metrics,
            'trades': self.trades,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
            
        print(f"Results saved to {filename}")
    
    def plot(self, show_trades: bool = True):
        """Plot backtest results"""
        plt.figure(figsize=(15, 10))
        
        # Plot equity curve
        plt.subplot(2, 1, 1)
        plt.plot(self.equity_curve, label='Portfolio Value')
        plt.title(f'Backtest Results - {self.symbol} ({self.strategy_name})')
        plt.xlabel('Time')
        plt.ylabel('Portfolio Value')
        plt.grid(True)
        plt.legend()
        
        # Add metrics text box
        metrics_text = (
            f"Total Return: {self.metrics['total_return']:.2%}\n"
            f"Sharpe Ratio: {self.metrics['sharpe_ratio']:.2f}\n"
            f"Max Drawdown: {self.metrics['max_drawdown']:.2%}\n"
            f"Win Rate: {self.metrics['win_rate']:.2%}\n"
            f"Number of Trades: {self.metrics['number_of_trades']}"
        )
        
        plt.text(
            0.02, 0.98, metrics_text,
            transform=plt.gca().transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )
        
        # Plot drawdown
        plt.subplot(2, 1, 2)
        equity_series = pd.Series(self.equity_curve)
        drawdown = (equity_series / equity_series.cummax() - 1)
        plt.plot(drawdown, color='red', label='Drawdown')
        plt.fill_between(range(len(drawdown)), drawdown, 0, color='red', alpha=0.3)
        plt.xlabel('Time')
        plt.ylabel('Drawdown')
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        
        # Save plot
        timestamp = self.timestamp.strftime('%Y%m%d_%H%M%S')
        filename = f"backtest_plot_{self.symbol}_{self.strategy_name}_{timestamp}.png"
        plt.savefig(filename)
        print(f"Plot saved to {filename}")
        plt.close()

class Backtester:
    def __init__(
        self,
        data: pd.DataFrame,
        strategy: 'Strategy',
        initial_capital: float = 10000,
        commission: float = 0.001
    ):
        self.data = data
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.current_position = None
        self.trades = []
        self.equity_curve = []
    
    def run(self) -> BacktestResult:
        """Run backtest and return results"""
        capital = self.initial_capital
        self.equity_curve = [capital]
        
        signals = self.strategy.generate_signals(self.data)
        
        for i in range(1, len(self.data)):
            current_price = self.data['close'].iloc[i]
            signal = signals.iloc[i]
            
            # Handle position entry
            if signal == 1 and self.current_position is None:
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
            elif signal == -1 and self.current_position is not None:
                exit_value = self.current_position.size * current_price
                capital += exit_value * (1 - self.commission)
                self.trades.append({
                    'entry_time': self.current_position.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'exit_time': self.data.index[i].strftime('%Y-%m-%d %H:%M:%S'),
                    'entry_price': float(self.current_position.entry_price),
                    'exit_price': float(current_price),
                    'pnl': float(exit_value - (self.current_position.size * self.current_position.entry_price)),
                    'return': float((current_price - self.current_position.entry_price) / self.current_position.entry_price)
                })
                self.current_position = None
            
            # Update equity curve
            current_equity = capital
            if self.current_position is not None:
                position_value = self.current_position.size * current_price
                current_equity += position_value
            self.equity_curve.append(current_equity)
        
        metrics = self.calculate_metrics()
        
        return BacktestResult(
            equity_curve=self.equity_curve,
            trades=self.trades,
            metrics=metrics,
            symbol=self.strategy.symbol if hasattr(self.strategy, 'symbol') else 'Unknown',
            strategy_name=self.strategy.__class__.__name__,
            params=self.strategy.get_params() if hasattr(self.strategy, 'get_params') else {}
        )
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        equity_curve = pd.Series(self.equity_curve)
        returns = equity_curve.pct_change().dropna()
        
        trades_df = pd.DataFrame(self.trades)
        
        metrics = {
            'total_return': float((equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital),
            'sharpe_ratio': float(np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0),
            'max_drawdown': float((equity_curve / equity_curve.cummax() - 1).min()),
            'number_of_trades': len(self.trades),
            'win_rate': float(len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) if len(trades_df) > 0 else 0),
            'avg_trade_return': float(trades_df['return'].mean() if len(trades_df) > 0 else 0),
            'profit_factor': float(
                abs(trades_df[trades_df['pnl'] > 0]['pnl'].sum() / 
                trades_df[trades_df['pnl'] < 0]['pnl'].sum())
                if len(trades_df[trades_df['pnl'] < 0]) > 0 else 0
            )
        }
        
        return metrics 