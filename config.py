import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Trading Parameters
TRADING_PAIRS = [
    'BTCUSDT',
    'ETHUSDT',
    'BNBUSDT',
    'ADAUSDT',
    'DOGEUSDT',
    'XRPUSDT',
    'MATICUSDT',
    'SOLUSDT',
    'AVAXUSDT',
    'DOTUSDT'
]

INITIAL_INVESTMENT = 5  # USDT
POSITION_SIZE = 0.2  # Use 20% of available balance per trade
STOP_LOSS_PERCENTAGE = 0.005  # 0.5% stop loss
TAKE_PROFIT_PERCENTAGE = 0.008  # 0.8% take profit

# Strategy Parameters
RSI_PERIOD = 7  # Shorter period for faster signals
RSI_OVERBOUGHT = 60  # More aggressive levels
RSI_OVERSOLD = 40
EMA_FAST = 5   # Very fast EMAs
EMA_SLOW = 12

# Timeframes
TIMEFRAME = '1m'    # 1 minute candles for quick trades

# Risk Management
MAX_DAILY_TRADES = 50  # Increased for more opportunities
MAX_DAILY_LOSS_PERCENTAGE = 0.10  # 10% max daily loss
MAX_POSITIONS = 5  # Maximum number of simultaneous positions

# Minimum price movement required to trade (in percentage)
MIN_PRICE_MOVEMENT = 0.002  # 0.2% minimum price movement

# Volume Requirements
MIN_24H_VOLUME = 500000  # Reduced minimum volume requirement
MIN_TRADES = 500        # Minimum number of trades in timeframe

# Quick Sell Parameters
QUICK_SELL_TIME = 300  # Sell after 5 minutes if no profit
TRAILING_STOP_PERCENTAGE = 0.003  # 0.3% trailing stop
PROFIT_LOCK_PERCENTAGE = 0.004  # Lock in profits after 0.4% gain

# MIN_PRICE_MOVEMENT = 0.005  # 0.5% minimum price movement
# MIN_24H_VOLUME = 1000000  # Minimum 24h volume in USDT
# MIN_TRADES = 1000        # Minimum number of trades in timeframe
# MAX_DAILY_TRADES = 10  # Increased max trades
# MAX_DAILY_LOSS_PERCENTAGE = 0.05  # 5% max daily loss
# TIMEFRAME = '5m'    # Changed to 5 minute candles for more opportunities

# RSI_PERIOD = 14
# RSI_OVERBOUGHT = 65  # Made more sensitive
# RSI_OVERSOLD = 35   # Made more sensitive
# EMA_FAST = 8        # Made faster
# EMA_SLOW = 21       # Made faster

# POSITION_SIZE = 0.95  # Use 95% of available balance for trading
# STOP_LOSS_PERCENTAGE = 0.01  # 1% stop loss
# TAKE_PROFIT_PERCENTAGE = 0.015  # 1.5% take profit