from dump_detector import DumpDetector
from pump_detector import PumpDetector
from data_provider import BinanceDataProvider
import concurrent.futures
import logging
import time
import sys
from typing import Callable

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_detector(detector_func: Callable, data_provider: BinanceDataProvider, name: str) -> None:
    """
    Run a detector with error handling and automatic restart
    """
    while True:
        try:
            logger.info(f"Starting {name}")
            detector_func(data_provider)
        except Exception as e:
            logger.error(f"Error in {name}: {str(e)}")
            logger.info(f"Restarting {name} in 5 seconds...")
            time.sleep(5)

def run_dump_detector(data_provider: BinanceDataProvider) -> None:
    dump_detector = DumpDetector(data_provider)
    dump_detector.monitor_market(min_score=70)

def run_pump_detector(data_provider: BinanceDataProvider) -> None:
    pump_detector = PumpDetector(data_provider)
    pump_detector.monitor_market(min_score=70)

def main():
    try:
        # Initialize Binance data provider
        data_provider = BinanceDataProvider()
        logger.info("Initialized data provider")
        
        # Use ThreadPoolExecutor to run detectors in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both detectors
            futures = [
                executor.submit(run_detector, run_dump_detector, data_provider, "Dump Detector"),
                executor.submit(run_detector, run_pump_detector, data_provider, "Pump Detector")
            ]
            
            # Wait for both to complete (they shouldn't unless there's an error)
            concurrent.futures.wait(futures)
            
            # Check for exceptions
            for future in futures:
                if future.exception():
                    logger.error(f"Detector failed with error: {future.exception()}")

    except KeyboardInterrupt:
        logger.info("Shutting down detectors...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Main loop error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 