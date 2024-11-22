import pandas as pd
from binance.client import Client
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from src.utils.logger import setup_logger

class DataDownloader:
    def __init__(self):
        self.client = Client()
        self.logger = setup_logger(self.__class__.__name__)
        self.data_dir = Path("data/historical")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_historical_data(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str,
        force_download: bool = False
    ) -> Optional[pd.DataFrame]:
        """Download and save historical data"""
        try:
            filename = self._get_filename(symbol, interval, start_date, end_date)
            filepath = self.data_dir / filename

            # Return cached data if exists and not force download
            if filepath.exists() and not force_download:
                self.logger.info(f"Loading cached data from {filepath}")
                return pd.read_csv(filepath, index_col='timestamp', parse_dates=True)

            # Download data
            self.logger.info(f"Downloading data for {symbol} from {start_date} to {end_date}")
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_date,
                end_str=end_date
            )

            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])

            # Process data
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Save to file
            df.set_index('timestamp', inplace=True)
            df.to_csv(filepath)
            self.logger.info(f"Data saved to {filepath}")

            return df[['open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            self.logger.error(f"Error downloading data: {str(e)}")
            return None

    def _get_filename(self, symbol: str, interval: str, start_date: str, end_date: str) -> str:
        """Generate filename for data storage"""
        return f"{symbol}_{interval}_{start_date}_{end_date}.csv" 