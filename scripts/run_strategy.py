import argparse
import yaml
from pathlib import Path
import pandas as pd
from src.data.data_provider import BinanceDataProvider
from src.strategies.sma_strategy import SMAStrategy
from src.backtesting.backtester import Backtester
from src.utils.logger import setup_logger

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description='Run trading strategy')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--symbol', type=str, required=True,
                       help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('--interval', type=str, default='1h',
                       help='Timeframe interval')
    args = parser.parse_args()
    
    # Setup
    logger = setup_logger('strategy_runner')
    config = load_config(args.config)
    
    # Initialize components
    data_provider = BinanceDataProvider()
    strategy = SMAStrategy(**config['strategies']['sma'])
    backtester = Backtester(
        strategy=strategy,
        **config['backtesting']
    )
    
    # Get historical data
    data = data_provider.get_historical_data(
        symbol=args.symbol,
        interval=args.interval
    )
    
    # Run backtest
    results = backtester.run(data)
    logger.info(f"Backtest Results: {results}")

if __name__ == "__main__":
    main() 