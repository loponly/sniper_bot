from binance.client import Client
import pandas as pd
from datetime import datetime, timedelta
from src.utils.retry import retry_on_exception
from src.utils.logger import setup_logger
from src.utils.data_downloader import DataDownloader
from pathlib import Path

class BinanceDataProvider:
    def __init__(self):
        self.client = Client()
        self.logger = setup_logger(self.__class__.__name__)
        self.downloader = DataDownloader()
        
    @retry_on_exception(retries=3, delay=5)
    def get_historical_data(
        self,
        symbol: str,
        interval: str,
        start_date: str = None,
        end_date: str = None,
        limit: int = 1000,
        force_download: bool = False
    ) -> pd.DataFrame:
        """Get historical OHLCV data"""
        try:
            # If dates are provided, use downloaded data
            if start_date and end_date:
                df = self.downloader.download_historical_data(
                    symbol=symbol,
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date,
                    force_download=force_download
                )
                if df is not None:
                    return df

            # Fallback to direct API call for recent data
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignored'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            df.set_index('timestamp', inplace=True)
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            return pd.DataFrame()