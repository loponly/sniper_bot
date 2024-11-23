class BacktestRunner:
    def run_backtest(
        self,
        symbol: str,
        strategy_name: str,
        start_date: str,
        end_date: str,
        interval: str = "1h",
        show_plot: bool = True,
        save_plot: bool = True
    ) -> Dict:
        """
        Run backtest for specified symbol and strategy
        
        Parameters:
        - symbol: Trading pair symbol (e.g., 'BTCUSDT')
        - strategy_name: Name of strategy to use
        - start_date: Start date for backtest
        - end_date: End date for backtest
        - interval: Data interval
        - show_plot: Whether to display the plot
        - save_plot: Whether to save the plot to file
        """
        try:
            # Get strategy configuration
            strategy_config = self.config['strategies'].get(strategy_name, {})
            
            # Create strategy instance
            strategy = self.create_strategy(strategy_name, strategy_config)
            
            # Get historical data
            data = self.data_provider.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            
            # Initialize and run backtester
            backtester = Backtester(
                data=data,
                strategy=strategy,
                initial_capital=self.config['backtesting']['initial_capital'],
                commission=self.config['backtesting']['commission'],
                show_plot=show_plot,
                save_plot=save_plot
            )
            
            results = backtester.run()
            
            # Save results
            self.save_results(results, symbol, strategy_name)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error running backtest: {str(e)}")
            raise e 