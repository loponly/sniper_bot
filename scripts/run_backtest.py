import argparse
import yaml
from pathlib import Path
import pandas as pd
from src.data.data_provider import BinanceDataProvider
from src.backtesting.backtester import Backtester
from src.strategies.sma_strategy import SMAStrategy
from src.utils.logger import setup_logger

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description='Run strategy backtest')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--symbol', type=str, required=True,
                       help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('--start', type=str, required=True,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True,
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--interval', type=str, default='1h',
                       help='Timeframe interval')
    args = parser.parse_args()
    
    # Setup
    logger = setup_logger('backtest_runner')
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
        start_date=args.start,
        end_date=args.end,
        interval=args.interval
    )
    
    # Run backtest
    results = backtester.run(data)
    
    # Log results
    logger.info("Backtest Results:")
    logger.info(f"Total Return: {results['total_return']:.2%}")
    logger.info(f"Number of Trades: {results['number_of_trades']}")
    logger.info(f"Win Rate: {results['win_rate']:.2%}")
    logger.info(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"Max Drawdown: {results['max_drawdown']:.2%}")
    
    # Plot results if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 6))
        plt.plot(results['equity_curve'])
        plt.title(f'Equity Curve - {args.symbol}')
        plt.xlabel('Time')
        plt.ylabel('Portfolio Value')
        plt.grid(True)
        plt.savefig(f'backtest_results_{args.symbol}.png')
        plt.close()
    except ImportError:
        logger.warning("Matplotlib not available - skipping plot generation")

if __name__ == "__main__":
    main() 