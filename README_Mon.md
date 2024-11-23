# Crypto Market Analyzer | Крипто Зах Зээлийн Шинжээч

[English](#crypto-market-analyzer) | [Монгол](#крипто-зах-зээлийн-шинжээч)

... (Previous English content remains the same) ...

# Крипто Зах Зээлийн Шинжээч

Крипто зах зээлийн хэв маягийг илрүүлэх, арилжааны стратегийг туршиж үзэх, бодит цагийн хяналт хийх цогц хэрэгсэл.

## Үндсэн боломжууд

- Зах зээлийн өсөлт, уналтыг бодит цагт илрүүлэх
- Олон цагийн хүрээний шинжилгээ
- Тохируулах боломжтой арилжааны стратегиуд:
  - SMA (Энгийн Хөдөлгөөнт Дундаж)
  - MACD + RSI + Bollinger Bands
  - Өсөлтийг Илрүүлэх
  - Уналтыг Илрүүлэх
- Гүйцэтгэлийн дэлгэрэнгүй үзүүлэлттэй туршилтын систем
- Техникийн үзүүлэлтийн шинжилгээ
- Интерактив өгөгдлийн визуалчлал

## Суулгах

1. Repository-г clone хийх:
```bash
git clone https://github.com/yourusername/crypto-market-analyzer.git
cd crypto-market-analyzer
```

2. Virtual environment үүсгэж идэвхжүүлэх:
```bash
# Linux/Mac дээр
python -m venv venv
source venv/bin/activate

# Windows дээр
python -m venv venv
venv\Scripts\activate
```

3. Шаардлагатай сангуудыг суулгах:
```bash
pip install -r requirements.txt
```

4. Шаардлагатай фолдерууд үүсгэх:
```bash
mkdir -p data/historical data/results logs results/plots
```

## Тохиргоо

1. Жишээ тохиргооны файлыг хуулах:
```bash
cp config/config.example.yaml config/config.yaml
```

2. `config/config.yaml` файлд өөрийн тохиргоог оруулах:
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

## Хэрэглээ

### Туршилт Ажиллуулах

1. Энгийн SMA Стратеги:
```bash
python main.py backtest --symbol BTCUSDT --strategy sma --interval 1h --start_date 2024-01-01 --end_date 2024-11-02
```

2. MACD+RSI+Bollinger Bands Стратеги:
```bash
python main.py backtest --symbol BTCUSDT --strategy macd_rsi_bb --interval 15m --start_date 2024-01-01 --end_date 2024-11-02
```

3. Өсөлт/Уналтыг Илрүүлэх:
```bash
python main.py backtest --symbol BTCUSDT --strategy pump --interval 1h
python main.py backtest --symbol BTCUSDT --strategy dump --interval 1h
```

### Зах Зээлийн Шинжилгээ

Арилжаагүйгээр зах зээлийн шинжилгээ хийх:
```bash
python main.py analyze --symbol BTCUSDT --interval 1h
```

### Бодит Цагийн Арилжаа/Хяналт

Бодит цагийн хяналт эхлүүлэх:
```bash
python main.py live --symbol BTCUSDT --strategy macd_rsi_bb --interval 15m
```

## Өөрчлөлт Хийх

### Шинэ Стратеги Нэмэх

1. `src/strategies/` дотор шинэ стратегийн файл үүсгэх:
```python
from src.strategies.base_strategy import BaseStrategy
from src.types.trading_signals import TradingSignal

class MyStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__()
        # Параметрүүдээ эхлүүлэх
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(TradingSignal.HOLD, index=data.index)
        # Стратегийн логик энд бичих
        return signals
```

2. `config.yaml`-д стратегийн тохиргоо нэмэх:
```yaml
strategies:
  my_strategy:
    param1: value1
    param2: value2
```

## Тестүүд Ажиллуулах

Тест ажиллуулах:
```bash
pytest tests/
```

## Docker ашиглан Ажиллуулах

1. Docker image бүтээх:
```bash
docker build -t crypto-analyzer .
```

2. Container ажиллуулах:
```bash
docker run -d \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  crypto-analyzer
```

## Хувь Нэмэр Оруулах

1. Repository-г fork хийх
2. Feature branch үүсгэх
3. Өөрчлөлтүүдээ commit хийх
4. Branch руугаа push хийх
5. Pull Request үүсгэх

## Лиценз

Энэхүү төсөл нь MIT License-тэй - дэлгэрэнгүйг LICENSE файлаас харна уу.