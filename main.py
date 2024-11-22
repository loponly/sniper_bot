import argparse
import yaml
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from src.data.data_provider import BinanceDataProvider
from src.strategies.sma_strategy import SMAStrategy
from src.strategies.pump_strategy import PumpStrategy
from src.strategies.dump_strategy import DumpStrategy
from src.backtesting.backtester import Backtester
from src.analysis.market_analyzer import MarketAnalyzer
from src.utils.logger import setup_logger
from src.data.data_manager import DataManager

class CryptoMarketRunner:
    def __init__(self, config_path: str = 'config/config.yaml'):
        """Initialize the market runner"""
        self.logger = setup_logger('market_runner')
        self.config = self._load_config(config_path)
        self.data_provider = BinanceDataProvider()
        self.market_analyzer = MarketAnalyzer()
        self.data_manager = DataManager()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from yaml file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return {}

    def run_analysis(self, 
                    symbol: str,
                    interval: str = '1h',
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> Dict:
        """Run market analysis"""
        try:
            results = self.market_analyzer.analyze_market(
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                volume_threshold=self.config['detectors']['pump']['volume_threshold'],
                price_threshold=self.config['detectors']['pump']['price_threshold']
            )
            return results
        except Exception as e:
            self.logger.error(f"Analysis error: {str(e)}")
            return {}

    def run_backtest(self, 
                    symbol: str,
                    strategy_name: str,
                    start_date: str,
                    end_date: str,
                    interval: str = '1h') -> Dict:
        """Run backtest for specified strategy"""
        try:
            # Get historical data
            data = self.data_provider.get_historical_data(
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )
            
            if data.empty:
                self.logger.error("No data available for backtest")
                return {}
            
            # Initialize strategy
            strategy = self._get_strategy(strategy_name)
            
            # Run backtest with only the supported parameters
            backtester = Backtester(
                data=data,
                strategy=strategy,
                initial_capital=self.config['backtesting']['initial_capital'],
                commission=self.config['backtesting']['commission']
                # Removed slippage parameter as it's not supported
            )
            
            results = backtester.run()
            if results:  # Only save if we have results
                self._save_results(results, f"backtest_{strategy_name}_{symbol}")
            return results
            
        except Exception as e:
            self.logger.error(f"Backtest error: {str(e)}")
            return {
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'number_of_trades': 0,
                'win_rate': 0,
                'equity_curve': []
            }  # Return default values on error

    def run_live(self,
                 symbol: str,
                 strategy_name: str,
                 interval: str = '1h') -> None:
        """Run live trading/monitoring"""
        try:
            self.logger.info(f"Starting live monitoring for {symbol}")
            strategy = self._get_strategy(strategy_name)
            
            while True:
                try:
                    # Get latest data
                    data = self.data_provider.get_historical_data(
                        symbol=symbol,
                        interval=interval,
                        limit=100
                    )
                    
                    # Run analysis
                    analysis = self.market_analyzer.analyze_market(
                        symbol=symbol,
                        interval=interval,
                        data=data
                    )
                    
                    # Generate signals
                    signals = strategy.generate_signals(data)
                    
                    # Log results
                    self._log_live_results(symbol, analysis, signals)
                    
                    # Wait for next interval
                    time.sleep(self._get_interval_seconds(interval))
                    
                except Exception as e:
                    self.logger.error(f"Error in live loop: {str(e)}")
                    time.sleep(60)  # Wait before retry
                    
        except KeyboardInterrupt:
            self.logger.info("Stopping live monitoring...")
        except Exception as e:
            self.logger.error(f"Live monitoring error: {str(e)}")

    def _get_strategy(self, strategy_name: str):
        """Get strategy instance based on name"""
        strategies = {
            'sma': lambda: SMAStrategy(**self.config['strategies']['sma']),
            'pump': lambda: PumpStrategy(**self.config['strategies']['pump']),
            'dump': lambda: DumpStrategy(**self.config['strategies']['dump'])
        }
        
        if strategy_name not in strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
            
        return strategies[strategy_name]()

    def _save_results(self, results: Dict, prefix: str):
        """Save results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/results/{prefix}_{timestamp}.json"
        
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
            
        self.logger.info(f"Results saved to {filename}")

    def _log_live_results(self, symbol: str, analysis: Dict, signals: pd.Series):
        """Log live monitoring results"""
        latest_signal = signals.iloc[-1] if not signals.empty else 0
        
        self.logger.info(f"\nSymbol: {symbol}")
        self.logger.info(f"Signal: {latest_signal}")
        self.logger.info("Market Health:")
        for indicator, value in analysis['health_indicators'].items():
            self.logger.info(f"  {indicator}: {value:.4f}")

    @staticmethod
    def _get_interval_seconds(interval: str) -> int:
        """Convert interval string to seconds"""
        units = {'m': 60, 'h': 3600, 'd': 86400}
        unit = interval[-1]
        value = int(interval[:-1])
        return value * units[unit]

def main():
    parser = argparse.ArgumentParser(description='Crypto Market Runner')
    parser.add_argument('mode', choices=['analyze', 'backtest', 'live'],
                       help='Running mode')
    parser.add_argument('--symbol', type=str, required=True,
                       help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('--strategy', type=str, choices=['sma', 'pump', 'dump'],
                       help='Strategy to use (required for backtest and live modes)')
    parser.add_argument('--interval', type=str, default='1h',
                       help='Time interval')
    parser.add_argument('--start_date', type=str,
                       help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str,
                       help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to config file')
    
    args = parser.parse_args()
    
    runner = CryptoMarketRunner(args.config)
    
    if args.mode == 'analyze':
        results = runner.run_analysis(
            symbol=args.symbol,
            interval=args.interval,
            start_date=args.start_date,
            end_date=args.end_date
        )
        print("\nAnalysis Results:")
        print(json.dumps(results, indent=2))
        
    elif args.mode == 'backtest':
        if not args.strategy:
            print("Error: strategy is required for backtest mode")
            return
            
        results = runner.run_backtest(
            symbol=args.symbol,
            strategy_name=args.strategy,
            start_date=args.start_date,
            end_date=args.end_date,
            interval=args.interval
        )
        
        print("\nBacktest Results:")
        print(f"Total Return: {results['total_return']:.2%}")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"Number of Trades: {results['number_of_trades']}")
        print(f"Win Rate: {results['win_rate']:.2%}")
        
    else:  # live mode
        if not args.strategy:
            print("Error: strategy is required for live mode")
            return
            
        runner.run_live(
            symbol=args.symbol,
            strategy_name=args.strategy,
            interval=args.interval
        )

if __name__ == "__main__":
    main() 