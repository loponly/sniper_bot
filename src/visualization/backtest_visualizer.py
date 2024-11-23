import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
from src.types.trading_signals import TradingSignal

class BacktestVisualizer:
    def __init__(self, data: pd.DataFrame, signals: pd.Series, equity_curve: List[float], trades: List[Dict], capital_history: List[float]):
        """
        Initialize BacktestVisualizer
        
        Parameters:
        - data: OHLCV DataFrame
        - signals: Series of trading signals
        - equity_curve: List of equity values over time
        - trades: List of trade dictionaries with entry/exit info
        - capital_history: List of available capital values over time
        """
        self.data = data
        self.signals = signals
        self.equity_curve = pd.Series(equity_curve, index=data.index)
        self.capital_history = pd.Series(capital_history, index=data.index)
        self.trades = trades

    def plot_backtest_results(self, 
                            strategy_metrics: Optional[pd.DataFrame] = None,
                            show_signals: bool = True,
                            show_equity: bool = True) -> go.Figure:
        """
        Create an interactive plot of backtest results
        
        Parameters:
        - strategy_metrics: DataFrame with additional strategy-specific metrics
        - show_signals: Whether to show entry/exit signals
        - show_equity: Whether to show equity curve
        
        Returns:
        - Plotly figure object
        """
        # Determine number of subplots needed
        n_rows = 1 + bool(show_equity) + bool(strategy_metrics is not None)
        
        # Create figure with subplots
        fig = make_subplots(
            rows=n_rows, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Price Action', 'Capital & Equity', 'Strategy Metrics')[:n_rows],
            row_heights=[0.5] + [0.25] * (n_rows - 1)
        )

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=self.data.index,
                open=self.data['open'],
                high=self.data['high'],
                low=self.data['low'],
                close=self.data['close'],
                name='Price'
            ),
            row=1, col=1
        )

        # Add entry/exit points if requested
        if show_signals:
            # Buy signals
            buy_points = self.signals == TradingSignal.BUY
            fig.add_trace(
                go.Scatter(
                    x=self.data.index[buy_points],
                    y=self.data['low'][buy_points],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=15, color='green'),
                    name='Buy Signal'
                ),
                row=1, col=1
            )

            # Sell signals
            sell_points = self.signals == TradingSignal.SELL
            fig.add_trace(
                go.Scatter(
                    x=self.data.index[sell_points],
                    y=self.data['high'][sell_points],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=15, color='red'),
                    name='Sell Signal'
                ),
                row=1, col=1
            )

        # Add equity and capital curves if requested
        if show_equity:
            # Add equity curve
            fig.add_trace(
                go.Scatter(
                    x=self.equity_curve.index,
                    y=self.equity_curve,
                    mode='lines',
                    name='Total Equity',
                    line=dict(color='blue')
                ),
                row=2, col=1
            )
            
            # Add available capital
            fig.add_trace(
                go.Scatter(
                    x=self.capital_history.index,
                    y=self.capital_history,
                    mode='lines',
                    name='Available Capital',
                    line=dict(color='green', dash='dash')
                ),
                row=2, col=1
            )

        # Add strategy metrics if provided
        if strategy_metrics is not None and n_rows > 2:
            for column in strategy_metrics.columns:
                fig.add_trace(
                    go.Scatter(
                        x=strategy_metrics.index,
                        y=strategy_metrics[column],
                        mode='lines',
                        name=column
                    ),
                    row=3, col=1
                )

        # Update layout
        fig.update_layout(
            title='Backtest Results',
            xaxis_title='Date',
            height=300 * n_rows,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )

        # Update y-axis labels
        fig.update_yaxes(title_text="Price", row=1, col=1)
        if show_equity:
            fig.update_yaxes(title_text="Value", row=2, col=1)
        if strategy_metrics is not None:
            fig.update_yaxes(title_text="Metric Value", row=3, col=1)

        return fig

    def plot_trade_distribution(self) -> go.Figure:
        """Create a plot showing the distribution of trade returns"""
        if not self.trades:
            return None

        returns = [trade['return'] for trade in self.trades]
        
        fig = go.Figure()
        fig.add_trace(
            go.Histogram(
                x=returns,
                nbinsx=50,
                name='Trade Returns'
            )
        )

        fig.update_layout(
            title='Trade Returns Distribution',
            xaxis_title='Return (%)',
            yaxis_title='Frequency',
            showlegend=True
        )

        return fig

    def plot_drawdown(self) -> go.Figure:
        """Create a plot showing the drawdown over time"""
        rolling_max = self.equity_curve.expanding().max()
        drawdown = (self.equity_curve - rolling_max) / rolling_max * 100

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown,
                mode='lines',
                name='Drawdown',
                fill='tozeroy',
                line=dict(color='red')
            )
        )

        fig.update_layout(
            title='Portfolio Drawdown',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            showlegend=True
        )

        return fig

    def save_plots(self, directory: str = 'results/plots/') -> None:
        """Save all plots to files"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        # Save main backtest plot
        fig_backtest = self.plot_backtest_results(show_signals=True, show_equity=True)
        fig_backtest.write_html(f"{directory}backtest_results.html")
        
        # Save trade distribution
        fig_dist = self.plot_trade_distribution()
        if fig_dist:
            fig_dist.write_html(f"{directory}trade_distribution.html")
        
        # Save drawdown plot
        fig_dd = self.plot_drawdown()
        fig_dd.write_html(f"{directory}drawdown.html") 