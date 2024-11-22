from src.data.data_provider import BinanceDataProvider
from src.strategies.pump_strategy import PumpStrategy
from src.strategies.dump_strategy import DumpStrategy
from src.backtesting.backtester import Backtester
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, Tuple
import json
from src.utils.logger import setup_logger

class MarketAnalyzer:
    def __init__(self):
        self.data_provider = BinanceDataProvider()
        self.logger = setup_logger(self.__class__.__name__)
        
    def analyze_market(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str,
        volume_threshold: float = 2.0,
        price_threshold: float = 0.03,
        lookback_period: int = 24
    ) -> Dict:
        """
        Perform comprehensive market analysis for both pumps and dumps
        """
        try:
            # Get market data
            data = self.data_provider.get_historical_data(
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )
            
            if data.empty:
                self.logger.error("No data available for analysis")
                return {}
            
            # Initialize strategies
            pump_strategy = PumpStrategy(
                volume_threshold=volume_threshold,
                price_pump_threshold=price_threshold,
                lookback_period=lookback_period
            )
            
            dump_strategy = DumpStrategy(
                volume_threshold=volume_threshold,
                price_drop_threshold=-price_threshold,
                lookback_period=lookback_period
            )
            
            # Calculate metrics
            pump_metrics = pump_strategy.calculate_pump_metrics(data)
            dump_metrics = dump_strategy.calculate_dump_metrics(data)
            
            # Combine metrics
            combined_metrics = self.combine_metrics(pump_metrics, dump_metrics)
            
            # Generate analysis
            analysis_results = self.generate_analysis(data, combined_metrics, symbol)
            
            # Save results
            self._save_analysis(analysis_results, symbol)
            
            # Plot analysis
            self._plot_combined_analysis(data, combined_metrics, symbol)
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Error in market analysis: {str(e)}")
            return {}
    
    def combine_metrics(self, pump_metrics: pd.DataFrame, dump_metrics: pd.DataFrame) -> pd.DataFrame:
        """Combine pump and dump metrics into a single DataFrame"""
        combined = pd.DataFrame(index=pump_metrics.index)
        
        # Volume metrics
        combined['volume_ratio'] = pump_metrics['volume_ratio']
        combined['volume_ma'] = pump_metrics['volume_ma']
        
        # Price metrics
        combined['price_change'] = pump_metrics['price_change']
        combined['price_ma'] = pump_metrics['price_ma']
        combined['price_deviation'] = pump_metrics['price_deviation']
        
        # Momentum
        combined['rsi'] = pump_metrics['rsi']
        
        # Manipulation scores
        combined['pump_score'] = pump_metrics['pump_score']
        combined['dump_score'] = dump_metrics['dump_score']
        
        # Combined manipulation score
        combined['manipulation_score'] = combined['pump_score'] - combined['dump_score']
        
        return combined
    
    def generate_analysis(self, data: pd.DataFrame, metrics: pd.DataFrame, symbol: str) -> Dict:
        """Generate comprehensive market analysis"""
        # Identify significant events
        significant_events = self.identify_significant_events(data, metrics)
        
        # Calculate pattern statistics
        pattern_stats = self.calculate_pattern_statistics(metrics)
        
        # Generate market health indicators
        health_indicators = self.calculate_market_health(metrics)
        
        return {
            'symbol': symbol,
            'period_start': data.index[0].strftime('%Y-%m-%d'),
            'period_end': data.index[-1].strftime('%Y-%m-%d'),
            'significant_events': significant_events,
            'pattern_statistics': pattern_stats,
            'health_indicators': health_indicators
        }
    
    def identify_significant_events(self, data: pd.DataFrame, metrics: pd.DataFrame) -> Dict:
        """Identify significant market events"""
        events = []
        
        # Define significance thresholds
        SIGNIFICANCE_THRESHOLD = 3.0  # 3x standard deviation
        
        # Calculate standard deviations
        manipulation_std = metrics['manipulation_score'].std()
        
        for i in range(1, len(metrics)):
            score = metrics['manipulation_score'].iloc[i]
            if abs(score) > SIGNIFICANCE_THRESHOLD * manipulation_std:
                events.append({
                    'timestamp': metrics.index[i].strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'pump' if score > 0 else 'dump',
                    'score': float(score),
                    'price': float(data['close'].iloc[i]),
                    'volume_ratio': float(metrics['volume_ratio'].iloc[i])
                })
        
        return events
    
    def calculate_pattern_statistics(self, metrics: pd.DataFrame) -> Dict:
        """Calculate statistics about market patterns"""
        return {
            'avg_volume_ratio': float(metrics['volume_ratio'].mean()),
            'max_pump_score': float(metrics['pump_score'].max()),
            'max_dump_score': float(metrics['dump_score'].max()),
            'volatility': float(metrics['price_change'].std()),
            'avg_rsi': float(metrics['rsi'].mean())
        }
    
    def calculate_market_health(self, metrics: pd.DataFrame) -> Dict:
        """Calculate market health indicators"""
        return {
            'manipulation_risk': float(abs(metrics['manipulation_score']).mean()),
            'volume_stability': float(1 / metrics['volume_ratio'].std()),
            'price_stability': float(1 / metrics['price_deviation'].std()),
            'momentum_balance': float(metrics['rsi'].mean() / 50.0)
        }
    
    def _plot_combined_analysis(self, data: pd.DataFrame, metrics: pd.DataFrame, symbol: str):
        """Create comprehensive analysis plots"""
        plt.style.use('seaborn')
        fig, axes = plt.subplots(5, 1, figsize=(15, 25))
        
        # Price and Volume
        ax1 = axes[0]
        ax1.plot(data.index, data['close'], label='Price', color='blue')
        ax1_volume = ax1.twinx()
        ax1_volume.bar(data.index, data['volume'], alpha=0.3, color='gray', label='Volume')
        ax1.set_title(f'Market Analysis - {symbol}')
        ax1.set_ylabel('Price')
        ax1_volume.set_ylabel('Volume')
        
        # Volume Ratio and Manipulation Score
        ax2 = axes[1]
        ax2.plot(metrics.index, metrics['volume_ratio'], label='Volume Ratio', color='orange')
        ax2.axhline(y=2.0, color='r', linestyle='--', label='Threshold')
        ax2.set_ylabel('Volume Ratio')
        ax2.legend()
        
        # RSI
        ax3 = axes[2]
        ax3.plot(metrics.index, metrics['rsi'], label='RSI', color='purple')
        ax3.axhline(y=70, color='r', linestyle='--')
        ax3.axhline(y=30, color='g', linestyle='--')
        ax3.set_ylabel('RSI')
        ax3.legend()
        
        # Pump and Dump Scores
        ax4 = axes[3]
        ax4.plot(metrics.index, metrics['pump_score'], label='Pump Score', color='green')
        ax4.plot(metrics.index, -metrics['dump_score'], label='Dump Score', color='red')
        ax4.set_ylabel('Manipulation Scores')
        ax4.legend()
        
        # Combined Manipulation Score
        ax5 = axes[4]
        ax5.plot(metrics.index, metrics['manipulation_score'], label='Manipulation Score', color='blue')
        ax5.fill_between(metrics.index, metrics['manipulation_score'], 0, 
                        where=metrics['manipulation_score'] >= 0, color='green', alpha=0.3)
        ax5.fill_between(metrics.index, metrics['manipulation_score'], 0, 
                        where=metrics['manipulation_score'] < 0, color='red', alpha=0.3)
        ax5.set_ylabel('Combined Score')
        ax5.legend()
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"market_analysis_{symbol}_{timestamp}.png"
        plt.savefig(filename)
        print(f"Analysis plot saved to {filename}")
        plt.close()
    
    def _save_analysis(self, analysis_results: Dict, symbol: str):
        """Save analysis results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"market_analysis_{symbol}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(analysis_results, f, indent=4)
        
        print(f"Analysis results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Analyze market manipulation patterns')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading pair symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Timeframe interval')
    parser.add_argument('--start_date', type=str, default='2023-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, default='2023-12-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--volume_threshold', type=float, default=2.0, help='Volume spike threshold')
    parser.add_argument('--price_threshold', type=float, default=0.03, help='Price change threshold')
    
    args = parser.parse_args()
    
    analyzer = MarketAnalyzer()
    results = analyzer.analyze_market(
        symbol=args.symbol,
        interval=args.interval,
        start_date=args.start_date,
        end_date=args.end_date,
        volume_threshold=args.volume_threshold,
        price_threshold=args.price_threshold
    )
    
    print("\nAnalysis Summary:")
    print(f"Period: {results['period_start']} to {results['period_end']}")
    print(f"Significant Events Detected: {len(results['significant_events'])}")
    print("\nMarket Health Indicators:")
    for indicator, value in results['health_indicators'].items():
        print(f"{indicator}: {value:.4f}")

if __name__ == "__main__":
    main() 