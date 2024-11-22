import pandas as pd
import yfinance as yf
from backtesting_system import Backtester
from sma_strategy import SMAStrategy

# Get sample data (you can replace this with your own data source)
def get_sample_data():
    # Download Bitcoin data from Yahoo Finance
    btc = yf.download('BTC-USD', start='2020-01-01', end='2023-12-31')
    return btc[['Open', 'High', 'Low', 'Close', 'Volume']].rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })

def main():
    # Get data
    data = get_sample_data()
    
    # Create strategy instance
    strategy = SMAStrategy(short_window=20, long_window=50)
    
    # Create and run backtester
    backtester = Backtester(
        data=data,
        strategy=strategy,
        initial_capital=10000,
        commission=0.001
    )
    
    # Run backtest
    results = backtester.run()
    
    # Print results
    print("\nBacktest Results:")
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"Number of Trades: {results['number_of_trades']}")
    print(f"Win Rate: {results['win_rate']:.2%}")
    
    # Plot equity curve
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    plt.plot(results['equity_curve'])
    plt.title('Equity Curve')
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main() 