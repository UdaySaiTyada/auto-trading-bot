# Automated Trading Bot

This is a cryptocurrency trading bot that implements a simple but effective trading strategy using technical indicators (RSI and EMA crossovers) with proper risk management.

## Features

- Integration with Binance exchange
- RSI and EMA-based trading strategy
- Configurable stop-loss and take-profit levels
- Risk management with daily trade limits
- Comprehensive logging
- Position size management

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with your Binance API credentials:
```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

3. Configure trading parameters in `config.py`:
- Adjust trading pair (default: BTCUSDT)
- Modify risk parameters
- Change technical indicator settings

## Usage

Run the bot:
```bash
python trading_bot.py
```

## Risk Warning

This bot is for educational purposes only. Cryptocurrency trading carries significant risks, and you should never trade with money you cannot afford to lose. Always start with small amounts and test thoroughly on a testnet first.

## Strategy

The bot uses the following strategy:
- Buy when RSI is oversold (< 30) and fast EMA crosses above slow EMA
- Sell when RSI is overbought (> 70) and fast EMA crosses below slow EMA
- Implements stop-loss and take-profit for risk management
- Limits daily trades and losses

## Logging

The bot logs all activities to `trading_bot.log`. Monitor this file for detailed information about trades and errors.

## Monitoring Logs

The bot generates detailed logs in the `logs/` directory with different log files for different purposes:

### Trading Activity Logs
```bash
# Watch real-time trading activity
tail -f logs/trading_*.log

# View last 100 lines of trading activity
tail -n 100 logs/trading_*.log

# Search for specific trading pair
grep "BTCUSDT" logs/trading_*.log
```

### Error Logs
```bash
# Monitor errors in real-time
tail -f logs/error_*.log

# View all errors from today
grep "$(date +%Y-%m-%d)" logs/error_*.log
```

### Performance Metrics
```bash
# Watch performance updates in real-time
tail -f logs/performance_*.log

# View all performance metrics from today
grep "$(date +%Y-%m-%d)" logs/performance_*.log
```

### Log File Structure
- `trading_*.log`: Contains all trading activities, signals, and order executions
- `error_*.log`: Contains errors, warnings, and system issues
- `performance_*.log`: Contains periodic performance metrics and statistics

### Important Log Patterns
- Buy Signals: Look for "Buy signal detected"
- Sell Signals: Look for "Sell signal detected"
- Profits/Losses: Search for "Trade resulted in"
- Stop Loss/Take Profit: Search for "Stop Loss triggered" or "Take Profit triggered"

### Log Rotation
- Logs are rotated daily
- Compressed after rotation
- Kept for 30 days
- Old logs are automatically deleted

### Monitoring Multiple Files
```bash
# Watch all log files simultaneously with different colors
tail -f logs/*.log | grep --color=always -E '^|error|warning|profit|loss'

# Monitor specific trading pairs
tail -f logs/trading_*.log | grep -E 'BTCUSDT|ETHUSDT'

# Watch only profitable trades
tail -f logs/trading_*.log | grep "resulted in profit"
```

### Performance Analysis
```bash
# Calculate total profit for today
grep "resulted in profit" logs/trading_*.log | awk '{sum += $NF} END {print "Total profit: " sum}'

# Count successful trades
grep -c "Trade resulted in profit" logs/trading_*.log

# View win rate
grep "Win Rate" logs/performance_*.log | tail -n 1
