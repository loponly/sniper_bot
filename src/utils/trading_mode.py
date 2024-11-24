class TradingMode:
    def __init__(self, mode: str):
        self.mode = mode.upper()
        self.is_dry_run = self.mode == 'DRY_RUN'
        self.is_live = self.mode == 'LIVE'
        self.is_backtest = self.mode == 'BACKTEST'

    def __str__(self):
        return self.mode

    @property
    def allow_trades(self):
        return self.is_live 