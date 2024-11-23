from src.strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np
from src.utils.logger import setup_logger
from src.types.trading_signals import TradingSignal

class MACDRSIBBStrategy(BaseStrategy):
    def __init__(
        self,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        rsi_period: int = 14,
        rsi_overbought: float = 70,
        rsi_oversold: float = 30,
        bb_period: int = 20,
        bb_std: float = 2.0,
        **kwargs
    ):
        """
        Initialize MACD + RSI + Bollinger Bands Strategy
        
        Parameters:
        - macd_fast: Fast EMA period for MACD
        - macd_slow: Slow EMA period for MACD
        - macd_signal: Signal line period for MACD
        - rsi_period: Period for RSI calculation
        - rsi_overbought: RSI overbought threshold
        - rsi_oversold: RSI oversold threshold
        - bb_period: Period for Bollinger Bands
        - bb_std: Number of standard deviations for Bollinger Bands
        """
        super().__init__()
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.logger = setup_logger(self.__class__.__name__)

    def calculate_macd(self, prices: pd.Series) -> tuple:
        """Calculate MACD line and signal line"""
        exp1 = prices.ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = prices.ewm(span=self.macd_slow, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        return macd_line, signal_line

    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.clip(lower=0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.clip(upper=0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_bollinger_bands(self, prices: pd.Series) -> tuple:
        """Calculate Bollinger Bands"""
        middle_band = prices.rolling(window=self.bb_period).mean()
        std = prices.rolling(window=self.bb_period).std()
        upper_band = middle_band + (self.bb_std * std)
        lower_band = middle_band - (self.bb_std * std)
        return upper_band, middle_band, lower_band

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on MACD, RSI, and Bollinger Bands"""
        try:
            if not self.validate_data(data):
                self.logger.error("Invalid data format")
                return pd.Series(TradingSignal.HOLD, index=data.index)

            signals = pd.Series(TradingSignal.HOLD, index=data.index)
            
            # Calculate indicators
            macd_line, signal_line = self.calculate_macd(data['close'])
            rsi = self.calculate_rsi(data['close'])
            upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands(data['close'])
            
            # Generate signals based on combined conditions
            for i in range(1, len(data)):
                # Buy conditions:
                # 1. MACD crosses above signal line
                # 2. RSI is oversold
                # 3. Price is near lower Bollinger Band
                macd_cross_up = (macd_line.iloc[i-1] < signal_line.iloc[i-1] and 
                                macd_line.iloc[i] > signal_line.iloc[i])
                
                rsi_oversold = rsi.iloc[i] < self.rsi_oversold
                price_near_lower_bb = (data['close'].iloc[i] <= lower_bb.iloc[i] * 1.02)
                
                if (macd_cross_up and rsi_oversold) or (rsi_oversold and price_near_lower_bb):
                    signals.iloc[i] = TradingSignal.BUY
                
                # Sell conditions:
                # 1. MACD crosses below signal line
                # 2. RSI is overbought
                # 3. Price is near upper Bollinger Band
                macd_cross_down = (macd_line.iloc[i-1] > signal_line.iloc[i-1] and 
                                 macd_line.iloc[i] < signal_line.iloc[i])
                
                rsi_overbought = rsi.iloc[i] > self.rsi_overbought
                price_near_upper_bb = (data['close'].iloc[i] >= upper_bb.iloc[i] * 0.98)
                
                if (macd_cross_down and rsi_overbought) or (rsi_overbought and price_near_upper_bb):
                    signals.iloc[i] = TradingSignal.SELL

            # Remove signals during warmup period
            warmup_period = max(self.macd_slow + self.macd_signal, 
                              self.rsi_period, 
                              self.bb_period)
            signals[:warmup_period] = TradingSignal.HOLD

            return signals

        except Exception as e:
            self.logger.error(f"Error generating signals: {str(e)}")
            raise e

    def calculate_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional strategy metrics"""
        metrics = pd.DataFrame(index=data.index)
        
        # MACD metrics
        macd_line, signal_line = self.calculate_macd(data['close'])
        metrics['macd_line'] = macd_line
        metrics['macd_signal'] = signal_line
        metrics['macd_histogram'] = macd_line - signal_line
        
        # RSI metrics
        metrics['rsi'] = self.calculate_rsi(data['close'])
        
        # Bollinger Bands metrics
        upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands(data['close'])
        metrics['bb_upper'] = upper_bb
        metrics['bb_middle'] = middle_bb
        metrics['bb_lower'] = lower_bb
        metrics['bb_width'] = (upper_bb - lower_bb) / middle_bb
        
        # Price position relative to Bollinger Bands
        metrics['bb_position'] = (data['close'] - lower_bb) / (upper_bb - lower_bb)
        
        return metrics 