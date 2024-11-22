from src.strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np
from src.utils.logger import setup_logger

class SMAStrategy(BaseStrategy):
    def __init__(self, short_window: int = 20, long_window: int = 50, **kwargs):
        """Initialize SMA Strategy"""
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
        self.logger = setup_logger(self.__class__.__name__)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on SMA crossover"""
        try:
            if not self.validate_data(data):
                self.logger.error("Invalid data format")
                return pd.Series(0, index=data.index)
                
            signals = pd.Series(0, index=data.index)
            
            # Calculate SMAs
            short_sma = data['close'].rolling(window=self.short_window).mean()
            long_sma = data['close'].rolling(window=self.long_window).mean()
            
            # Generate signals
            signals[short_sma > long_sma] = 1  # Buy signal
            signals[short_sma < long_sma] = -1  # Sell signal
            
            # Remove signals before both SMAs are available
            signals[:self.long_window] = 0
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {str(e)}")
            return pd.Series(0, index=data.index) 