from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from binance.client import Client
import time

class OHLCVProvider(ABC):
    """Abstract base class for OHLCV data providers"""
    
    @abstractmethod
    def get_symbols(self) -> list:
        """Get list of available trading symbols"""
        pass
    
    @abstractmethod
    def get_ohlcv(self, symbol: str, interval: str = '5m', limit: int = 100) -> Optional[pd.DataFrame]:
        """Get OHLCV data for a symbol"""
        pass

class BinanceDataProvider(OHLCVProvider):
    """Fetch OHLCV data from Binance API"""
    def __init__(self):
        self.client = Client(None, None)  # No API keys needed for public data
        self._cache = {}
        self._last_update = {}
        self.update_interval = 30  # Seconds between updates
        
        # Binance kline intervals mapping
        self.intervals = {
            '1m': Client.KLINE_INTERVAL_1MINUTE,
            '3m': Client.KLINE_INTERVAL_3MINUTE,
            '5m': Client.KLINE_INTERVAL_5MINUTE,
            '15m': Client.KLINE_INTERVAL_15MINUTE,
            '30m': Client.KLINE_INTERVAL_30MINUTE,
            '1h': Client.KLINE_INTERVAL_1HOUR,
            '2h': Client.KLINE_INTERVAL_2HOUR,
            '4h': Client.KLINE_INTERVAL_4HOUR,
            '6h': Client.KLINE_INTERVAL_6HOUR,
            '8h': Client.KLINE_INTERVAL_8HOUR,
            '12h': Client.KLINE_INTERVAL_12HOUR,
            '1d': Client.KLINE_INTERVAL_1DAY,
        }
    
    def get_symbols(self) -> list:
        """Get all USDT trading pairs from Binance"""
        try:
            exchange_info = self.client.get_exchange_info()
            usdt_pairs = [
                symbol['symbol'] for symbol in exchange_info['symbols']
                if symbol['symbol'].endswith('USDT') 
                and symbol['status'] == 'TRADING'
                and symbol['isSpotTradingAllowed']
            ]
            return usdt_pairs
        except Exception as e:
            print(f"Error fetching symbols: {str(e)}")
            return []

    def _should_update_cache(self, symbol: str, interval: str) -> bool:
        """Check if we should update the cached data"""
        cache_key = f"{symbol}_{interval}"
        if cache_key not in self._last_update:
            return True
        
        elapsed = time.time() - self._last_update[cache_key]
        return elapsed >= self.update_interval

    def get_ohlcv(self, symbol: str, interval: str = '5m', limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from Binance"""
        try:
            cache_key = f"{symbol}_{interval}"
            
            # Check if we need to update the cache
            if self._should_update_cache(symbol, interval):
                # Convert interval to Binance format
                binance_interval = self.intervals.get(interval, Client.KLINE_INTERVAL_5MINUTE)
                
                # Fetch klines from Binance
                klines = self.client.get_klines(
                    symbol=symbol,
                    interval=binance_interval,
                    limit=limit
                )
                
                # Convert to DataFrame
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 
                    'volume', 'close_time', 'quote_volume', 'trades',
                    'taker_base', 'taker_quote', 'ignore'
                ])
                
                # Convert types
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Update cache
                self._cache[cache_key] = df
                self._last_update[cache_key] = time.time()
            
            return self._cache[cache_key].copy()
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def get_24h_volume(self, symbol: str) -> float:
        """Get 24h volume for a symbol in USDT"""
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            return float(ticker['quoteVolume'])
        except Exception as e:
            print(f"Error fetching 24h volume for {symbol}: {str(e)}")
            return 0.0