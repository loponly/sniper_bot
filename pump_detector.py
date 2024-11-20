import pandas as pd
import numpy as np
from datetime import datetime
import time
import talib
from data_provider import OHLCVProvider

class PumpDetector:
    def __init__(self, data_provider: OHLCVProvider):
        self.data_provider = data_provider
        self.recent_alerts = {}
        self.config = {
            'volume_spike_threshold': 3,
            'price_rise_threshold': 0.02,
            'rsi_overbought': 70,
            'mfi_overbought': 80,
            'macd_threshold': 0.5,
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
            'CDLPIERCING': 10,
            'CDLMORNINGSTAR': 6,
            'CDL3WHITESOLDIERS': 9,
            'CDLHAMMER': 6,
            'CDLINVERTEDHAMMER': 5,
            'CDLDRAGONFLYDOJI': 6
        }

    def calculate_indicators(self, df):
        """Calculate technical indicators for pump detection using TA-Lib"""
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

    def detect_pump_signals(self, df, symbol):
        """Enhanced pump signal detection"""
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
            if latest['price_change'] > self.config['price_rise_threshold']:
                score += 25
            elif latest['price_change'] > 0.01:
                score += 15
            
            # Technical indicators
            if latest['rsi'] > self.config['rsi_overbought']:
                score += 10
            
            if latest['mfi'] > self.config['mfi_overbought']:
                score += 10
            
            if prev['macd'] < prev['macd_signal'] and latest['macd'] > latest['macd_signal']:
                score += 10
            
            if latest['close'] > latest['bb_upper']:
                score += 10
            
            if latest['obv_change'] > 0.02:
                score += 10
            
            # New technical checks
            # Stochastic RSI overbought
            if latest['fastk'] > 80 and latest['fastd'] > 80:
                score += 10
            
            # Strong uptrend
            if latest['adx'] > 25 and latest['roc'] > 2:
                score += 15
            
            # Positive money flow
            if latest['cmf'] > 0.1:
                score += 10
            
            # Enhanced pattern recognition
            pattern_score = self._check_enhanced_patterns(df)
            score += pattern_score
            
            # Volume profile analysis
            volume_score = self._analyze_volume_profile(df)
            score += volume_score
            
            return min(score, 100)
            
        except Exception as e:
            print(f"Error in pump detection for {symbol}: {str(e)}")
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
                if result > 0:  # Bullish signal
                    pattern_score += weight
            
            # Check for multiple pattern confluence
            if pattern_score > 15:  # Multiple bullish patterns
                pattern_score += 10  # Bonus for confluence
                
        except Exception as e:
            print(f"Error checking enhanced patterns: {str(e)}")
        
        return min(pattern_score, 30)  # Cap pattern score

    def _analyze_volume_profile(self, df):
        """Analyze volume profile for pump signals"""
        try:
            recent_data = df.tail(20)
            score = 0
            
            # Volume increasing while price increasing
            if (recent_data['volume'].is_monotonic_increasing and 
                recent_data['close'].is_monotonic_increasing):
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
        print("\n=== Pump Detector Started ===")
        print(f"Minimum score: {min_score}")
        print("Monitoring market for potential pumps...\n")
        
        while True:
            try:
                symbols = self.data_provider.get_symbols()
                potential_pumps = []
                
                for symbol in symbols:
                    print(f"Analyzing {symbol}...", end='\r')
                    
                    # Multi-timeframe analysis
                    timeframe_scores = []
                    for interval in self.config['intervals']:
                        df = self.data_provider.get_ohlcv(symbol, interval=interval)
                        if df is not None:
                            df = self.calculate_indicators(df)
                            if df is not None:
                                score = self.detect_pump_signals(df, symbol)
                                timeframe_scores.append(score)
                    
                    # Average score across timeframes
                    if timeframe_scores:
                        avg_score = sum(timeframe_scores) / len(timeframe_scores)
                        
                        if avg_score >= min_score:
                            # Collect pump info
                            latest_price = df['close'].iloc[-1]
                            volume_24h = df['volume'].sum()
                            
                            pump_info = {
                                'symbol': symbol,
                                'score': avg_score,
                                'price': latest_price,
                                'volume_24h': volume_24h,
                                'price_change': df['price_change'].iloc[-1] * 100,
                                'rsi': df['rsi'].iloc[-1],
                                'mfi': df['mfi'].iloc[-1],
                                'bb_position': (latest_price - df['bb_lower'].iloc[-1]) / 
                                             (df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1]),
                                'timestamp': datetime.now()
                            }
                            
                            potential_pumps.append(pump_info)
                            self.recent_alerts[symbol] = datetime.now()
                            
                            print("\n" + "="*50)
                            print(f"🚀 POTENTIAL PUMP DETECTED: {symbol}")
                            print("="*50)
                            print(f"Score: {avg_score}/100")
                            print(f"Price change: {pump_info['price_change']:.2f}%")
                            print(f"RSI: {pump_info['rsi']:.2f}")
                            print(f"MFI: {pump_info['mfi']:.2f}")
                            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            print("="*50 + "\n")

                if potential_pumps:
                    self.save_pump_alerts(potential_pumps)

                print("\nWaiting 30 seconds before next scan...", end='\r')
                time.sleep(30)

            except Exception as e:
                print(f"\nError in market monitoring: {str(e)}")
                print("Retrying in 60 seconds...")
                time.sleep(60)

    def save_pump_alerts(self, pumps):
        """Save pump alerts to a CSV file"""
        df = pd.DataFrame(pumps)
        filename = f"pump_alerts_{datetime.now().strftime('%Y%m%d')}.csv"
        
        try:
            df.to_csv(filename, mode='a', header=not pd.io.common.file_exists(filename), index=False)
            print(f"Alert saved to {filename}")
        except Exception as e:
            print(f"Error saving pump alerts: {str(e)}") 