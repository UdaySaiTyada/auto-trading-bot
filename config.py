import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Trading Parameters
TRADING_SYMBOL = 'BTCUSDT'  # Bitcoin/USDT pair
INITIAL_INVESTMENT = 100  # USD
POSITION_SIZE = 0.95  # Use 95% of available balance for trading
STOP_LOSS_PERCENTAGE = 0.02  # 2% stop loss
TAKE_PROFIT_PERCENTAGE = 0.03  # 3% take profit

# Strategy Parameters
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
EMA_FAST = 12
EMA_SLOW = 26

# Timeframes
TIMEFRAME = '15m'  # 15 minute candles

# Risk Management
MAX_DAILY_TRADES = 5
MAX_DAILY_LOSS_PERCENTAGE = 0.05  # 5% max daily loss
