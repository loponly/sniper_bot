# Crypto Market Analyzer

A comprehensive cryptocurrency market analysis tool that includes market pattern detection, trading strategy backtesting, and real-time monitoring.

## Features

- Real-time detection of market pumps and dumps
- Multiple timeframe analysis
- Customizable trading strategies:
  - SMA (Simple Moving Average)
  - MACD + RSI + Bollinger Bands
  - Pump Detection
  - Dump Detection
- Backtesting system with detailed performance metrics
- Technical indicator analysis
- Interactive data visualization tools

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-market-analyzer.git
cd crypto-market-analyzer
```

2. Create and activate a virtual environment:
```bash
# On Linux/Mac
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create necessary directories:
```bash
mkdir -p data/historical data/results logs results/plots
```

## Configuration

1. Copy the example config file:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Edit `config/config.yaml` to customize your settings:
```yaml
strategies:
  sma:
    short_window: 20
    long_window: 50
  
  macd_rsi_bb:
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
    rsi_period: 14
    rsi_overbought: 70
    rsi_oversold: 30
    bb_period: 20
    bb_std: 2.0

backtesting:
  initial_capital: 10000
  commission: 0.001
```

## Usage

### Running Backtests

1. Basic SMA Strategy:
```bash
python main.py backtest --symbol BTCUSDT --strategy sma --interval 1h --start_date 2024-01-01 --end_date 2024-11-02
```

2. MACD+RSI+Bollinger Bands Strategy:
```bash
python main.py backtest --symbol BTCUSDT --strategy macd_rsi_bb --interval 15m --start_date 2024-01-01 --end_date 2024-11-02
```

3. Pump/Dump Detection:
```bash
python main.py backtest --symbol BTCUSDT --strategy pump --interval 1h
python main.py backtest --symbol BTCUSDT --strategy dump --interval 1h
```

### Market Analysis

Run market analysis without trading:
```bash
python main.py analyze --symbol BTCUSDT --interval 1h
```

### Live Trading/Monitoring

Start live monitoring:
```bash
python main.py live --symbol BTCUSDT --strategy macd_rsi_bb --interval 15m
```

## Customization

### Adding New Strategies

1. Create a new strategy file in `src/strategies/`:
```python
from src.strategies.base_strategy import BaseStrategy
from src.types.trading_signals import TradingSignal

class MyStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__()
        # Initialize your parameters
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(TradingSignal.HOLD, index=data.index)
        # Add your strategy logic here
        return signals
```

2. Add strategy configuration to `config.yaml`:
```yaml
strategies:
  my_strategy:
    param1: value1
    param2: value2
```

3. Register strategy in `main.py`:
```python
def _get_strategy(self, strategy_name: str):
    strategies = {
        'my_strategy': lambda: MyStrategy(**self.config['strategies']['my_strategy']),
        # ... other strategies
    }
```

### Modifying Visualization

1. Update plot settings in `src/visualization/backtest_visualizer.py`:
```python
def plot_backtest_results(self, 
                         strategy_metrics: Optional[pd.DataFrame] = None,
                         show_signals: bool = True,
                         show_equity: bool = True) -> go.Figure:
    # Customize your plots
```

## Project Structure

```
crypto-market-analyzer/
├── config/
│   └── config.yaml         # Configuration file
├── src/
│   ├── analysis/          # Market analysis modules
│   ├── backtesting/       # Backtesting engine
│   ├── data/             # Data management
│   ├── detectors/        # Pattern detectors
│   ├── strategies/       # Trading strategies
│   ├── utils/           # Utility functions
│   └── visualization/    # Plotting tools
├── data/
│   ├── historical/      # Historical price data
│   └── results/         # Backtest results
├── logs/               # Application logs
├── results/
│   └── plots/          # Generated plots
├── tests/             # Unit tests
├── main.py           # Main application entry
└── requirements.txt  # Python dependencies
```

## Testing

Run the test suite:
```bash
pytest tests/
```

## Deployment

### Docker Deployment

1. Build image:
```bash
docker build -t crypto-analyzer .
```

2. Run container:
```bash
docker run -d \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  crypto-analyzer
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.