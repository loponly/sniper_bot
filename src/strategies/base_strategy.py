from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any
from src.utils.logger import setup_logger

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
            Series with trading signals (1: buy, -1: sell, 0: hold)
        """
        pass
        
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data has required columns"""
        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        return all(col in data.columns for col in required_columns) 