from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import numpy as np
from datetime import datetime
import time
from loguru import logger
import config
import ta

class TradingBot:
    def __init__(self):
        self.client = Client(config.API_KEY, config.API_SECRET)
        self.symbol = config.TRADING_SYMBOL
        self.position = None
        self.trades_today = 0
        self.daily_loss = 0
        logger.add("trading_bot.log", rotation="1 day")

    def get_account_balance(self):
        """Get current USDT balance"""
        try:
            balance = self.client.get_asset_balance(asset='USDT')
            return float(balance['free'])
        except BinanceAPIException as e:
            logger.error(f"Error getting balance: {e}")
            return 0

    def get_historical_data(self):
        """Get historical klines/candlestick data"""
        try:
            klines = self.client.get_historical_klines(
                self.symbol,
                config.TIMEFRAME,
                "1 day ago UTC"
            )
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close',
                'volume', 'close_time', 'quote_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignored'
            ])
            df['close'] = pd.to_numeric(df['close'])
            return df
        except BinanceAPIException as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        try:
            # Calculate RSI
            df['RSI'] = ta.momentum.RSIIndicator(
                df['close'], window=config.RSI_PERIOD
            ).rsi()

            # Calculate EMAs
            df['EMA_fast'] = ta.trend.EMAIndicator(
                df['close'], window=config.EMA_FAST
            ).ema_indicator()
            df['EMA_slow'] = ta.trend.EMAIndicator(
                df['close'], window=config.EMA_SLOW
            ).ema_indicator()

            return df
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return None

    def should_buy(self, df):
        """Determine if we should buy based on our strategy"""
        if len(df) < 2:
            return False

        last_row = df.iloc[-1]
        
        # Check if RSI is oversold and EMAs are aligned for uptrend
        if (last_row['RSI'] < config.RSI_OVERSOLD and
            last_row['EMA_fast'] > last_row['EMA_slow']):
            return True
        return False

    def should_sell(self, df):
        """Determine if we should sell based on our strategy"""
        if len(df) < 2:
            return False

        last_row = df.iloc[-1]
        
        # Check if RSI is overbought and EMAs are aligned for downtrend
        if (last_row['RSI'] > config.RSI_OVERBOUGHT and
            last_row['EMA_fast'] < last_row['EMA_slow']):
            return True
        return False

    def place_buy_order(self, price):
        """Place a buy order"""
        try:
            balance = self.get_account_balance()
            quantity = (balance * config.POSITION_SIZE) / price
            quantity = float(f"{quantity:.6f}")  # Format to 6 decimal places

            order = self.client.create_order(
                symbol=self.symbol,
                side='BUY',
                type='MARKET',
                quantity=quantity
            )
            
            logger.info(f"Buy order placed: {order}")
            self.position = {
                'entry_price': price,
                'quantity': quantity,
                'stop_loss': price * (1 - config.STOP_LOSS_PERCENTAGE),
                'take_profit': price * (1 + config.TAKE_PROFIT_PERCENTAGE)
            }
            self.trades_today += 1
            return True
        except BinanceAPIException as e:
            logger.error(f"Error placing buy order: {e}")
            return False

    def place_sell_order(self):
        """Place a sell order"""
        try:
            if not self.position:
                return False

            order = self.client.create_order(
                symbol=self.symbol,
                side='SELL',
                type='MARKET',
                quantity=self.position['quantity']
            )
            
            logger.info(f"Sell order placed: {order}")
            
            # Calculate profit/loss
            exit_price = float(order['fills'][0]['price'])
            profit = (exit_price - self.position['entry_price']) * self.position['quantity']
            if profit < 0:
                self.daily_loss += abs(profit)
            
            self.position = None
            return True
        except BinanceAPIException as e:
            logger.error(f"Error placing sell order: {e}")
            return False

    def check_stop_loss_take_profit(self, current_price):
        """Check if we should exit position based on SL/TP"""
        if not self.position:
            return False

        if (current_price <= self.position['stop_loss'] or 
            current_price >= self.position['take_profit']):
            return self.place_sell_order()
        return False

    def run(self):
        """Main trading loop"""
        logger.info("Starting trading bot...")
        
        while True:
            try:
                # Reset daily counters at midnight
                if datetime.now().hour == 0 and datetime.now().minute == 0:
                    self.trades_today = 0
                    self.daily_loss = 0

                # Check if we've hit our daily limits
                if (self.trades_today >= config.MAX_DAILY_TRADES or 
                    self.daily_loss >= (config.INITIAL_INVESTMENT * config.MAX_DAILY_LOSS_PERCENTAGE)):
                    logger.info("Daily limits reached, waiting for reset...")
                    time.sleep(60)
                    continue

                # Get market data
                df = self.get_historical_data()
                if df is None:
                    continue

                df = self.calculate_indicators(df)
                if df is None:
                    continue

                current_price = float(df.iloc[-1]['close'])

                # Check existing position
                if self.position:
                    if self.check_stop_loss_take_profit(current_price):
                        continue
                    if self.should_sell(df):
                        self.place_sell_order()
                else:
                    if self.should_buy(df):
                        self.place_buy_order(current_price)

                time.sleep(60)  # Wait for 1 minute before next iteration

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
