from abc import ABC, abstractmethod
import logging
from typing import Dict, List
import pandas as pd
from datetime import datetime

class BaseDetector(ABC):
    def __init__(self, min_score: float = 70):
        self.min_score = min_score
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def calculate_score(self, data: pd.DataFrame) -> float:
        """Calculate detection score"""
        pass
        
    @abstractmethod
    def detect_signals(self, data: pd.DataFrame) -> Dict:
        """Detect market signals"""
        pass
        
    def get_metrics(self, data: pd.DataFrame) -> Dict:
        """Get common metrics"""
        try:
            latest = data.iloc[-1]
            return {
                'price': latest['close'],
                'volume': latest['volume'],
                'rsi': latest['rsi'],
                'volume_ratio': latest['volume'] / data['volume'].rolling(24).mean().iloc[-1],
                'price_change': data['close'].pct_change().iloc[-1]
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics: {str(e)}")
            return {} 