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
