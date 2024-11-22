import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from src.utils.logger import setup_logger

class DataManager:
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.data_dir = Path("data")
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        for dir_name in ['historical', 'results', 'cache']:
            (self.data_dir / dir_name).mkdir(parents=True, exist_ok=True)

    def save_data(self, data: pd.DataFrame, filename: str, subdir: str = 'historical'):
        """Save data to file"""
        try:
            filepath = self.data_dir / subdir / filename
            data.to_csv(filepath)
            self.logger.info(f"Data saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")

    def load_data(self, filename: str, subdir: str = 'historical') -> Optional[pd.DataFrame]:
        """Load data from file"""
        try:
            filepath = self.data_dir / subdir / filename
            if not filepath.exists():
                self.logger.warning(f"File not found: {filepath}")
                return None
            
            df = pd.read_csv(filepath, index_col='timestamp', parse_dates=True)
            self.logger.info(f"Data loaded from {filepath}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            return None

    def list_available_data(self, subdir: str = 'historical') -> Dict:
        """List available data files"""
        try:
            files = list((self.data_dir / subdir).glob('*.csv'))
            return {
                'symbols': list(set(f.stem.split('_')[0] for f in files)),
                'intervals': list(set(f.stem.split('_')[1] for f in files)),
                'files': [f.name for f in files]
            }
        except Exception as e:
            self.logger.error(f"Error listing data: {str(e)}")
            return {'symbols': [], 'intervals': [], 'files': []} 