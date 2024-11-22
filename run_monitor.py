from monitor.market_monitor import MarketMonitor
from strategies.pump_strategy import PumpStrategy
from strategies.dump_strategy import DumpStrategy
from data_provider import BinanceDataProvider
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize components
        data_provider = BinanceDataProvider()
        
        # Initialize strategies
        strategies = [
            PumpStrategy(min_score=70),
            DumpStrategy(min_score=70)
        ]
        
        # Initialize market monitor
        monitor = MarketMonitor(
            data_provider=data_provider,
            strategies=strategies,
            intervals=['5m', '15m', '1h'],
            min_volume=1000000,
            alert_cooldown=3600
        )
        
        # Start monitoring
        logger.info("Starting market monitor...")
        monitor.monitor_market()
        
    except KeyboardInterrupt:
        logger.info("Shutting down monitor...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Main loop error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 