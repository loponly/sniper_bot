import unittest
import pandas as pd
import numpy as np
from src.detectors.dump_detector import DumpDetector
from src.detectors.pump_detector import PumpDetector
from src.utils.logger import setup_logger

class TestDetectors(unittest.TestCase):
    def setUp(self):
        self.logger = setup_logger('test_logger')
        
        # Create more realistic test data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        self.test_data = pd.DataFrame({
            'open': np.random.normal(100, 10, 100),
            'high': np.random.normal(105, 10, 100),
            'low': np.random.normal(95, 10, 100),
            'close': np.random.normal(100, 10, 100),
            'volume': np.random.normal(1000, 100, 100)
        }, index=dates)
        
        # Add technical indicators
        self.test_data['rsi'] = 50 + np.random.normal(0, 10, 100)
        
    def test_dump_detector(self):
        detector = DumpDetector()
        score = detector.calculate_score(self.test_data)
        self.assertIsInstance(score, float)
        self.assertTrue(0 <= score <= 100)
        
        # Test with empty data
        empty_score = detector.calculate_score(pd.DataFrame())
        self.assertEqual(empty_score, 0)
        
    def test_metrics(self):
        detector = DumpDetector()
        metrics = detector.get_metrics(self.test_data)
        
        required_metrics = {'price', 'volume', 'rsi', 'volume_ratio', 'price_change'}
        self.assertTrue(all(metric in metrics for metric in required_metrics))

if __name__ == '__main__':
    unittest.main() 