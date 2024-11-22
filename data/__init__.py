"""
Data package for Crypto Market Analyzer.
Provides access to historical market data and analysis results.
"""

from pathlib import Path

# Define data directory paths
DATA_DIR = Path(__file__).parent
HISTORICAL_DIR = DATA_DIR / 'historical'
RESULTS_DIR = DATA_DIR / 'results'
CACHE_DIR = DATA_DIR / 'cache'

# Create directories if they don't exist
for directory in [HISTORICAL_DIR, RESULTS_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def get_data_path(data_type: str) -> Path:
    """Get the appropriate data directory path."""
    paths = {
        'historical': HISTORICAL_DIR,
        'results': RESULTS_DIR,
        'cache': CACHE_DIR
    }
    return paths.get(data_type, DATA_DIR) 