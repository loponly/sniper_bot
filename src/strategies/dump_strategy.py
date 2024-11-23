from src.strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np
from src.utils.logger import setup_logger
from src.types.trading_signals import TradingSignal

class DumpStrategy(BaseStrategy):
    def __init__(
        self,
        volume_threshold: float = 2.0,
        price_drop_threshold: float = -0.03,
        lookback_period: int = 24,
        recovery_threshold: float = 0.02
    ):
        """
        Initialize Dump Strategy
        
        Parameters:
        - volume_threshold: Multiple of average volume to trigger alert (e.g., 2.0 = 200% of avg volume)
        - price_drop_threshold: Minimum price drop to consider as dump (-0.03 = -3%)
        - lookback_period: Period for calculating average volume
        - recovery_threshold: Price increase to consider for recovery trades (0.02 = 2%)
        """
        super().__init__()
        self.volume_threshold = volume_threshold
        self.price_drop_threshold = price_drop_threshold
        self.lookback_period = lookback_period
        self.recovery_threshold = recovery_threshold
        self.logger = setup_logger(self.__class__.__name__)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on dump detection"""
        try:
            signals = pd.Series(TradingSignal.HOLD, index=data.index)
            
            # Calculate rolling volume average
            volume_ma = data['volume'].rolling(window=self.lookback_period).mean()
            
            # Calculate price changes
            price_changes = data['close'].pct_change()
            
            # Calculate volume ratio
            volume_ratio = data['volume'] / volume_ma
            
            # Detect dump conditions
            dump_conditions = (
                (price_changes < self.price_drop_threshold) &  # Price dropped significantly
                (volume_ratio > self.volume_threshold)         # Volume spiked
            )
            
            # Generate entry signals (buy after dump)
            for i in range(1, len(data)):
                if dump_conditions.iloc[i]:
                    signals.iloc[i] = TradingSignal.BUY
                
                # Exit conditions
                elif signals.iloc[i-1] == TradingSignal.BUY:  # If we're in a position
                    price_change_since_entry = (
                        data['close'].iloc[i] / data['close'].iloc[i-1] - 1
                    )
                    
                    # Exit if price recovers to target or drops further
                    if (price_change_since_entry >= self.recovery_threshold or 
                        price_change_since_entry < self.price_drop_threshold):
                        signals.iloc[i] = TradingSignal.SELL
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {str(e)}")
            return pd.Series(TradingSignal.HOLD, index=data.index)
    
    def calculate_dump_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate additional metrics for dump detection
        Returns DataFrame with dump metrics
        """
        try:
            metrics = pd.DataFrame(index=data.index)
            
            # Volume metrics
            metrics['volume_ma'] = data['volume'].rolling(window=self.lookback_period).mean()
            metrics['volume_ratio'] = data['volume'] / metrics['volume_ma']
            
            # Price metrics
            metrics['price_change'] = data['close'].pct_change()
            metrics['price_ma'] = data['close'].rolling(window=self.lookback_period).mean()
            metrics['price_deviation'] = (data['close'] - metrics['price_ma']) / metrics['price_ma']
            
            # Dump score (higher score indicates stronger dump signal)
            metrics['dump_score'] = (
                (metrics['volume_ratio'] - self.volume_threshold) * 
                abs(metrics['price_change'].clip(upper=0))
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}")
            return pd.DataFrame()