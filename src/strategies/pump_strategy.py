from src.strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np
from src.utils.logger import setup_logger
from src.types.trading_signals import TradingSignal

class PumpStrategy(BaseStrategy):
    def __init__(
        self,
        volume_threshold: float = 2.0,
        price_pump_threshold: float = 0.03,
        lookback_period: int = 24,
        profit_target: float = 0.02,
        stop_loss: float = -0.02
    ):
        """Initialize Pump Strategy"""
        super().__init__()
        self.volume_threshold = volume_threshold
        self.price_pump_threshold = price_pump_threshold
        self.lookback_period = lookback_period
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.logger = setup_logger(self.__class__.__name__)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on pump detection"""
        try:
            signals = pd.Series(TradingSignal.HOLD, index=data.index)
            
            # Calculate metrics
            volume_ma = data['volume'].rolling(window=self.lookback_period).mean()
            price_changes = data['close'].pct_change()
            volume_ratio = data['volume'] / volume_ma
            
            # Detect pump conditions
            pump_conditions = (
                (price_changes > self.price_pump_threshold) &  # Price pumped significantly
                (volume_ratio > self.volume_threshold)         # Volume spiked
            )
            
            # Track position entry price for profit/loss calculation
            entry_price = None
            
            for i in range(1, len(data)):
                if pump_conditions.iloc[i] and signals.iloc[i-1] != TradingSignal.BUY:
                    signals.iloc[i] = TradingSignal.BUY
                    entry_price = data['close'].iloc[i]
                
                elif signals.iloc[i-1] == TradingSignal.BUY and entry_price is not None:
                    # Calculate current return
                    current_return = (entry_price - data['close'].iloc[i]) / entry_price
                    
                    # Exit conditions
                    if (current_return >= self.profit_target or  # Take profit
                        current_return <= self.stop_loss):       # Stop loss
                        signals.iloc[i] = TradingSignal.SELL
                        entry_price = None
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {str(e)}")
            return pd.Series(TradingSignal.HOLD, index=data.index)
    
    def calculate_pump_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate additional metrics for pump detection
        Returns DataFrame with pump metrics
        """
        metrics = pd.DataFrame(index=data.index)
        
        # Volume metrics
        metrics['volume_ma'] = data['volume'].rolling(window=self.lookback_period).mean()
        metrics['volume_ratio'] = data['volume'] / metrics['volume_ma']
        
        # Price metrics
        metrics['price_change'] = data['close'].pct_change()
        metrics['price_ma'] = data['close'].rolling(window=self.lookback_period).mean()
        metrics['price_deviation'] = (data['close'] - metrics['price_ma']) / metrics['price_ma']
        
        # Momentum indicators
        metrics['rsi'] = self.calculate_rsi(data['close'])
        
        # Pump score (higher score indicates stronger pump signal)
        metrics['pump_score'] = (
            (metrics['volume_ratio'] - self.volume_threshold) * 
            metrics['price_change'].clip(lower=0)
        )
        
        return metrics
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.clip(lower=0)).rolling(window=period).mean()
        loss = (-delta.clip(upper=0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi 