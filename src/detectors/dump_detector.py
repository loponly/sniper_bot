import pandas as pd
import numpy as np
from datetime import datetime
import time
import talib
from data_provider import OHLCVProvider


class DumpDetector:
    def __init__(self, data_provider: OHLCVProvider):
        self.data_provider = data_provider
        self.recent_alerts = {}
        self.config = {
            'volume_spike_threshold': 3,
            'price_drop_threshold': -0.02,
            'rsi_oversold': 30,
            'mfi_oversold': 20,
            'macd_threshold': -0.5,
            'bollinger_threshold': 2,
            'alert_cooldown': 3600,
            'min_volume': 1000000,  # Minimum 24h volume in USDT
            'min_price': 0.00001,   # Minimum price to consider
            'max_price': 100000,    # Maximum price to consider
            'intervals': ['5m', '15m', '1h'],  # Multiple timeframes
        }
        self.pattern_weights = self._init_pattern_weights()

    def _init_pattern_weights(self):
        """Initialize candlestick pattern weights"""
        return {
            'CDLENGULFING': 8,
            'CDLEVENINGSTAR': 10,
            'CDLHANGINGMAN': 6,
            'CDLDARKCLOUDCOVER': 7,
            'CDL3BLACKCROWS': 9,
            'CDLSHOOTINGSTAR': 6,
            'CDLHARAMI': 5,
            'CDLGRAVESTONEDOJI': 6
        }

    def calculate_indicators(self, df):
        """Calculate technical indicators for dump detection using TA-Lib"""
        if df is None or len(df) < 20:
            return None
            
        try:
            # Convert DataFrame values to numpy arrays for TA-Lib
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df['volume'].values
            
            # Volume indicators
            df['volume_ma'] = talib.SMA(volume, timeperiod=20)
            df['volume_ratio'] = volume / df['volume_ma']
            
            # Price indicators
            df['price_change'] = df['close'].pct_change()
            df['price_ma'] = talib.SMA(close, timeperiod=20)
            
            # RSI
            df['rsi'] = talib.RSI(close, timeperiod=14)
            
            # MFI
            df['mfi'] = talib.MFI(high, low, close, volume, timeperiod=14)
            
            # OBV
            df['obv'] = talib.OBV(close, volume)
            df['obv_change'] = df['obv'].pct_change()
            
            # MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
                close, 
                fastperiod=12, 
                slowperiod=26, 
                signalperiod=9
            )
            
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
                close,
                timeperiod=20,
                nbdevup=2,
                nbdevdn=2,
                matype=0  # Simple Moving Average
            )
            
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            
            # Add new indicators
            # Stochastic RSI
            df['fastk'], df['fastd'] = talib.STOCHRSI(df['close'].values)
            
            # Average Directional Index
            df['adx'] = talib.ADX(high, low, close, timeperiod=14)
            
            # Chaikin Money Flow
            df['cmf'] = talib.ADOSC(high, low, close, volume)
            
            # Rate of Change
            df['roc'] = talib.ROC(close, timeperiod=10)
            
            return df
            
        except Exception as e:
            print(f"Error calculating indicators: {str(e)}")
            return None

    def detect_dump_signals(self, df, symbol):
        """Enhanced dump signal detection"""
        if df is None or len(df) < 20:
            return 0
        
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            score = 0
            
            # Price filter
            if not (self.config['min_price'] <= latest['close'] <= self.config['max_price']):
                return 0
            
            # Check cooldown period
            if symbol in self.recent_alerts:
                last_alert_time = self.recent_alerts[symbol]
                if (datetime.now() - last_alert_time).total_seconds() < self.config['alert_cooldown']:
                    return 0
            
            # Volume analysis
            if latest['volume_ratio'] > self.config['volume_spike_threshold']:
                score += 25
            elif latest['volume_ratio'] > 2:
                score += 15
            
            # Price action
            if latest['price_change'] < self.config['price_drop_threshold']:
                score += 25
            elif latest['price_change'] < -0.01:
                score += 15
            
            # Technical indicators
            if latest['rsi'] < self.config['rsi_oversold']:
                score += 10
            
            if latest['mfi'] < self.config['mfi_oversold']:
                score += 10
            
            if prev['macd'] > prev['macd_signal'] and latest['macd'] < latest['macd_signal']:
                score += 10
            
            if latest['close'] < latest['bb_lower']:
                score += 10
            
            if latest['obv_change'] < -0.02:
                score += 10
            
            # New technical checks
            # Stochastic RSI oversold
            if latest['fastk'] < 20 and latest['fastd'] < 20:
                score += 10
            
            # Strong downtrend
            if latest['adx'] > 25 and latest['roc'] < -2:
                score += 15
            
            # Negative money flow
            if latest['cmf'] < -0.1:
                score += 10
            
            # Enhanced pattern recognition
            pattern_score = self._check_enhanced_patterns(df)
            score += pattern_score
            
            # Volume profile analysis
            volume_score = self._analyze_volume_profile(df)
            score += volume_score
            
            return min(score, 100)
            
        except Exception as e:
            print(f"Error in dump detection for {symbol}: {str(e)}")
            return 0

    def _check_enhanced_patterns(self, df):
        """Enhanced pattern recognition"""
        pattern_score = 0
        try:
            open_prices = df['open'].values
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            
            # Check patterns with weights
            for pattern, weight in self.pattern_weights.items():
                pattern_func = getattr(talib, pattern)
                result = pattern_func(open_prices, high, low, close)[-1]
                if result < 0:  # Bearish signal
                    pattern_score += weight
            
            # Check for multiple pattern confluence
            if pattern_score > 15:  # Multiple bearish patterns
                pattern_score += 10  # Bonus for confluence
                
        except Exception as e:
            print(f"Error checking enhanced patterns: {str(e)}")
        
        return min(pattern_score, 30)  # Cap pattern score

    def _analyze_volume_profile(self, df):
        """Analyze volume profile for dump signals"""
        try:
            recent_data = df.tail(20)
            score = 0
            
            # Volume increasing while price decreasing
            if (recent_data['volume'].is_monotonic_increasing and 
                recent_data['close'].is_monotonic_decreasing):
                score += 15
            
            # Volume concentration
            recent_volume = recent_data['volume'].sum()
            total_volume = df['volume'].sum()
            if recent_volume > total_volume * 0.4:  # 40% of volume in recent candles
                score += 10
            
            # Large volume spikes
            volume_std = df['volume'].std()
            if recent_data['volume'].max() > volume_std * 3:
                score += 5
            
            return score
            
        except Exception as e:
            print(f"Error analyzing volume profile: {str(e)}")
            return 0

    def monitor_market(self, min_score=70):
        """Enhanced market monitoring"""
        print("\n=== Dump Detector Started ===")
        print(f"Minimum score: {min_score}")
        print("Monitoring market for potential dumps...\n")
        
        while True:
            try:
                symbols = self.data_provider.get_symbols()
                potential_dumps = []
                
                for symbol in symbols:
                    print(f"Analyzing {symbol}...", end='\r')
                    
                    # Multi-timeframe analysis
                    timeframe_scores = []
                    for interval in self.config['intervals']:
                        df = self.data_provider.get_ohlcv(symbol, interval=interval)
                        if df is not None:
                            df = self.calculate_indicators(df)
                            if df is not None:
                                score = self.detect_dump_signals(df, symbol)
                                timeframe_scores.append(score)
                    
                    # Average score across timeframes
                    if timeframe_scores:
                        avg_score = sum(timeframe_scores) / len(timeframe_scores)
                        
                        if avg_score >= min_score:
                            # Previous dump info collection and alert logic...
                            
                            print("\n" + "="*50)
                            print(f"🚨 POTENTIAL DUMP DETECTED: {symbol}")
                            print("="*50)
                            print(f"Average Score: {avg_score:.2f}/100")
                            for interval, score in zip(self.config['intervals'], timeframe_scores):
                                print(f"{interval} Score: {score}/100")
                            # ... rest of the alert printing

                # Previous alert saving logic...

            except Exception as e:
                print(f"\nError in market monitoring: {str(e)}")
                print("Retrying in 60 seconds...")
                time.sleep(60)

    def save_dump_alerts(self, dumps):
        """Save dump alerts to a CSV file"""
        df = pd.DataFrame(dumps)
        filename = f"dump_alerts_{datetime.now().strftime('%Y%m%d')}.csv"
        
        try:
            df.to_csv(filename, mode='a', header=not pd.io.common.file_exists(filename), index=False)
            print(f"Alert saved to {filename}")
        except Exception as e:
            print(f"Error saving dump alerts: {str(e)}") 