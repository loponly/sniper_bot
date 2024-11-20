from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
import talib
from datetime import datetime
from data_provider import BinanceDataProvider
import matplotlib.pyplot as plt
from typing import Dict, Tuple

class DumpDetectorStrategy(Strategy):
    # Define fixed parameters
    volume_spike_threshold = 3.0
    price_drop_threshold = -0.02
    rsi_oversold = 30
    mfi_oversold = 20
    min_score = 70
    stop_loss = 0.02
    take_profit = 0.05
    
    def init(self):
        """Initialize indicators"""
        # Store price data
        self.volume = self.data.Volume
        self.close = self.data.Close
        self.high = self.data.High
        self.low = self.data.Low
        
        # Calculate indicators
        self.volume_ma = self.I(talib.SMA, self.volume, 20)
        self.rsi = self.I(talib.RSI, self.close, 14)
        self.mfi = self.I(talib.MFI, self.high, self.low, self.close, self.volume, 14)
        self.adx = self.I(talib.ADX, self.high, self.low, self.close)
        
        # MACD
        self.macd, self.macd_signal, _ = self.I(talib.MACD, self.close)
        
        # Bollinger Bands
        _, _, self.bb_lower = self.I(talib.BBANDS, self.close)

    def calculate_dump_score(self) -> float:
        """Calculate dump score"""
        try:
            score = 0
            
            # Volume analysis
            volume_ratio = self.volume[-1] / self.volume_ma[-1]
            if volume_ratio > self.volume_spike_threshold:
                score += 25
            elif volume_ratio > 2:
                score += 15
            
            # Price action
            price_change = (self.close[-1] - self.close[-2]) / self.close[-2]
            if price_change < self.price_drop_threshold:
                score += 25
            elif price_change < -0.01:
                score += 15
            
            # Technical indicators
            if self.rsi[-1] < self.rsi_oversold:
                score += 10
            
            if self.mfi[-1] < self.mfi_oversold:
                score += 10
            
            # MACD crossover
            if (self.macd[-2] > self.macd_signal[-2] and 
                self.macd[-1] < self.macd_signal[-1]):
                score += 10
            
            # Price below lower Bollinger Band
            if self.close[-1] < self.bb_lower[-1]:
                score += 10
            
            # Strong downtrend
            if self.adx[-1] > 25:
                score += 10
            
            return min(score, 100)
            
        except Exception as e:
            print(f"Error calculating score: {str(e)}")
            return 0

    def next(self):
        """Trading logic"""
        dump_score = self.calculate_dump_score()
        
        # Entry logic
        if not self.position and dump_score >= self.min_score:
            # Enter short position
            entry_price = self.close[-1]
            stop_price = entry_price * (1 + self.stop_loss)
            target_price = entry_price * (1 - self.take_profit)
            
            self.sell(size=1, sl=stop_price, tp=target_price)
        
        # Exit logic
        elif self.position.is_short:
            if dump_score < self.min_score * 0.7:
                self.cover()

class BacktestAnalyzer:
    def __init__(self, symbol: str, timeframe: str = "1h"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.data_provider = BinanceDataProvider()
    
    def prepare_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Prepare data for backtesting"""
        df = self.data_provider.get_ohlcv(
            symbol=self.symbol,
            interval=self.timeframe,
            limit=1000
        )
        
        if df is None:
            raise ValueError(f"Could not fetch data for {self.symbol}")
        
        return self._prepare_dataframe(df)
    
    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame for backtesting"""
        df = df.rename(columns={
            'timestamp': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        df = df[~df.index.duplicated(keep='first')]
        df = df.ffill()
        
        return df
    
    def run_backtest(self, data: pd.DataFrame) -> Dict:
        """Run backtest with default parameters"""
        bt = Backtest(
            data,
            DumpDetectorStrategy,
            cash=1000000,
            commission=0.001,
            margin=1.0,
            trade_on_close=True,
            hedging=False,
            exclusive_orders=True
        )
        
        return bt.run()
    
    def optimize_strategy(self, data: pd.DataFrame) -> Tuple[Dict, pd.DataFrame]:
        """Run optimization"""
        bt = Backtest(
            data,
            DumpDetectorStrategy,
            cash=1000000,
            commission=0.001,
            margin=1.0,
            trade_on_close=True,
            hedging=False,
            exclusive_orders=True
        )
        
        # Define optimization space
        stats = bt.optimize(
            volume_spike_threshold=[2, 3, 4, 5],
            price_drop_threshold=[-0.03, -0.025, -0.02, -0.015, -0.01],
            rsi_oversold=[20, 25, 30, 35],
            mfi_oversold=[15, 20, 25, 30],
            min_score=[60, 65, 70, 75, 80],
            maximize='Sharpe Ratio'
        )
        
        return stats, bt.optimize_results

def main():
    analyzer = BacktestAnalyzer("BTCUSDT", "1h")
    
    try:
        print("Fetching historical data...")
        data = analyzer.prepare_data(
            start_date="2023-01-01",
            end_date="2024-01-01"
        )
        
        print(f"Got {len(data)} candles for analysis")
        
        print("\nRunning backtest with default parameters...")
        default_stats = analyzer.run_backtest(data)
        
        print("\nOptimizing strategy parameters...")
        stats, results = analyzer.optimize_strategy(data)
        
        print("\nBacktest Results:")
        print("================")
        print(f"Return: {stats['Return [%]']:.2f}%")
        print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
        print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
        print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
        print(f"Number of Trades: {stats['# Trades']}")
        
        # Save results
        filename = f'optimization_results_{datetime.now().strftime("%Y%m%d")}.csv'
        results.to_csv(filename)
        print(f"\nOptimization results saved to {filename}")
        
    except Exception as e:
        raise e
        print(f"\nError during backtesting: {str(e)}")
        raise e

if __name__ == "__main__":
    main() 