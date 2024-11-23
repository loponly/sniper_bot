from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any
from src.utils.logger import setup_logger
from src.types.trading_signals import TradingSignal

class BaseStrategy(ABC):
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize base strategy"""
        self.config = config or {}
        self.logger = setup_logger(self.__class__.__name__)
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals from market data
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with trading signals (TradingSignal enum values)
        """
        pass
        
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data has required columns"""
        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        return all(col in data.columns for col in required_columns) 