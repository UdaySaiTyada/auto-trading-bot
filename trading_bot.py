from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from loguru import logger
import config
import ta
import json
from pathlib import Path
from visualizer import TradeVisualizer

class TradingBot:
    def __init__(self):
        # Set up logging configuration
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Add trading activity logger
        logger.add(
            "logs/trading_{time}.log",
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO",
            compression="zip"
        )
        
        # Add error logger
        logger.add(
            "logs/error_{time}.log",
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}",
            level="ERROR",
            compression="zip"
        )
        
        # Add performance logger
        logger.add(
            "logs/performance_{time}.log",
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            filter=lambda record: "PERFORMANCE" in record["extra"],
            compression="zip"
        )

        logger.info("Initializing Trading Bot...")
        try:
            self.client = Client(config.API_KEY, config.API_SECRET)
            self.positions = {}  # Dictionary to track positions for multiple pairs
            self.trades_today = 0
            self.daily_loss = 0
            self.total_trades = 0
            self.successful_trades = 0
            self.failed_trades = 0
            self.start_balance = self.get_account_balance()
            
            # Initialize trading pairs info
            self.trading_pairs_info = {}
            self.update_trading_pairs_info()
            
            self.visualizer = TradeVisualizer()
            self.performance_data = {
                'timestamps': [],
                'balances': [],
                'successful_trades': 0,
                'failed_trades': 0
            }
            
            logger.info(f"Bot initialized successfully")
            logger.info(f"Trading pairs: {', '.join(config.TRADING_PAIRS)}")
            logger.info(f"Initial balance: {self.start_balance} USDT")
            self.log_trading_parameters()
        except Exception as e:
            logger.error(f"Failed to initialize bot: {str(e)}")
            raise

    def log_trading_parameters(self):
        """Log all trading parameters for reference"""
        params = {
            "Trading Pairs": ', '.join(config.TRADING_PAIRS),
            "Initial Investment": config.INITIAL_INVESTMENT,
            "Position Size": f"{config.POSITION_SIZE * 100}%",
            "Stop Loss": f"{config.STOP_LOSS_PERCENTAGE * 100}%",
            "Take Profit": f"{config.TAKE_PROFIT_PERCENTAGE * 100}%",
            "RSI Period": config.RSI_PERIOD,
            "RSI Overbought": config.RSI_OVERBOUGHT,
            "RSI Oversold": config.RSI_OVERSOLD,
            "EMA Fast": config.EMA_FAST,
            "EMA Slow": config.EMA_SLOW,
            "Min 24h Volume": config.MIN_24H_VOLUME,
            "Min Price Movement": config.MIN_PRICE_MOVEMENT
        }
        logger.info("Trading Parameters:")
        for key, value in params.items():
            logger.info(f"{key}: {value}")

    def log_performance_metrics(self):
        """Log performance metrics"""
        current_balance = self.get_account_balance()
        total_profit = current_balance - self.start_balance
        win_rate = (self.successful_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        metrics = {
            "Total Trades": self.total_trades,
            "Successful Trades": self.successful_trades,
            "Failed Trades": self.failed_trades,
            "Win Rate": f"{win_rate:.2f}%",
            "Starting Balance": f"{self.start_balance:.4f} USDT",
            "Current Balance": f"{current_balance:.4f} USDT",
            "Total Profit/Loss": f"{total_profit:.4f} USDT",
            "Daily Loss": f"{self.daily_loss:.4f} USDT"
        }
        
        logger.bind(PERFORMANCE=True).info(f"Performance Metrics: {json.dumps(metrics, indent=2)}")

    def get_account_balance(self):
        """Get current USDT balance"""
        try:
            balance = self.client.get_asset_balance(asset='USDT')
            return float(balance['free'])
        except BinanceAPIException as e:
            logger.error(f"Error getting balance: {e}")
            return 0

    def get_historical_data(self, symbol):
        """Get historical klines/candlestick data"""
        try:
            # Get more data to ensure we have enough for indicators
            klines = self.client.get_historical_klines(
                symbol,
                config.TIMEFRAME,
                "2 days ago UTC"  # Increased from 1 day to 2 days
            )
            
            if not klines or len(klines) < 30:  # Minimum required candles
                logger.warning(f"Insufficient data for {symbol}. Got {len(klines) if klines else 0} candles, need at least 30")
                return None
                
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close',
                'volume', 'close_time', 'quote_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignored'
            ])
            
            # Convert all necessary columns to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            # Remove any rows with NaN values
            df = df.dropna()
            
            # Ensure we still have enough data after cleaning
            if len(df) < 30:
                logger.warning(f"Insufficient clean data for {symbol} after processing")
                return None
                
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting data for {symbol}: {str(e)}")
            return None

    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        try:
            if len(df) < max(config.RSI_PERIOD, config.EMA_SLOW) + 1:
                logger.warning(f"Not enough data points for calculating indicators. Need at least {max(config.RSI_PERIOD, config.EMA_SLOW) + 1}")
                return None

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

            # Remove any NaN values that might have been introduced
            df = df.dropna()

            # Verify we have enough data after calculations
            if len(df) < 2:
                logger.warning("Insufficient data after calculating indicators")
                return None

            return df
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return None

    def update_trading_pairs_info(self):
        """Update 24h trading information for all pairs"""
        try:
            tickers = self.client.get_ticker()
            for ticker in tickers:
                if ticker['symbol'] in config.TRADING_PAIRS:
                    self.trading_pairs_info[ticker['symbol']] = {
                        'volume': float(ticker['volume']) * float(ticker['lastPrice']),
                        'price_change_percent': float(ticker['priceChangePercent']),
                        'last_price': float(ticker['lastPrice'])
                    }
            logger.info(f"Updated trading pairs info: {json.dumps(self.trading_pairs_info, indent=2)}")
        except Exception as e:
            logger.error(f"Error updating trading pairs info: {str(e)}")

    def should_trade_pair(self, symbol):
        """Determine if we should trade this pair based on volume and volatility"""
        if symbol not in self.trading_pairs_info:
            return False
            
        info = self.trading_pairs_info[symbol]
        
        # Check minimum volume
        if info['volume'] < config.MIN_24H_VOLUME:
            logger.info(f"{symbol} volume too low: {info['volume']:.2f} USDT")
            return False
            
        # Check price movement
        if abs(info['price_change_percent']) < config.MIN_PRICE_MOVEMENT * 100:
            logger.info(f"{symbol} price movement too low: {info['price_change_percent']}%")
            return False
            
        return True

    def should_buy(self, df, symbol):
        """Enhanced buy strategy"""
        try:
            if len(df) < 2:
                return False
                
            if not self.should_trade_pair(symbol):
                return False

            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            # Ensure all required indicators are present
            required_indicators = ['RSI', 'EMA_fast', 'EMA_slow', 'volume', 'close']
            if not all(indicator in df.columns for indicator in required_indicators):
                logger.warning(f"Missing required indicators for {symbol}")
                return False
            
            # RSI conditions
            rsi_oversold = last_row['RSI'] < config.RSI_OVERSOLD
            rsi_increasing = last_row['RSI'] > prev_row['RSI']
            
            # EMA conditions
            ema_crossover = (prev_row['EMA_fast'] <= prev_row['EMA_slow'] and 
                            last_row['EMA_fast'] > last_row['EMA_slow'])
            
            # Volume confirmation
            volume_increasing = last_row['volume'] > prev_row['volume']
            
            # Price action
            price_increasing = last_row['close'] > prev_row['close']
            
            if (rsi_oversold and rsi_increasing and 
                (ema_crossover or (last_row['EMA_fast'] > last_row['EMA_slow'])) and
                volume_increasing and price_increasing):
                
                logger.info(f"Buy signal for {symbol}:")
                logger.info(f"RSI: {last_row['RSI']:.2f}")
                logger.info(f"EMA Fast: {last_row['EMA_fast']:.2f}")
                logger.info(f"EMA Slow: {last_row['EMA_slow']:.2f}")
                logger.info(f"Volume: {last_row['volume']:.2f}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error in should_buy for {symbol}: {str(e)}")
            return False

    def should_sell(self, df, symbol):
        """Enhanced sell strategy"""
        if len(df) < 2:
            return False

        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        # RSI conditions
        rsi_overbought = last_row['RSI'] > config.RSI_OVERBOUGHT
        rsi_decreasing = last_row['RSI'] < prev_row['RSI']
        
        # EMA conditions
        ema_crossover = (prev_row['EMA_fast'] >= prev_row['EMA_slow'] and 
                        last_row['EMA_fast'] < last_row['EMA_slow'])
        
        # Volume confirmation
        volume_increasing = last_row['volume'] > prev_row['volume']
        
        # Price action
        price_decreasing = last_row['close'] < prev_row['close']
        
        if (rsi_overbought and rsi_decreasing and 
            (ema_crossover or (last_row['EMA_fast'] < last_row['EMA_slow'])) and
            volume_increasing and price_decreasing):
            
            logger.info(f"Sell signal for {symbol}:")
            logger.info(f"RSI: {last_row['RSI']:.2f}")
            logger.info(f"EMA Fast: {last_row['EMA_fast']:.2f}")
            logger.info(f"EMA Slow: {last_row['EMA_slow']:.2f}")
            logger.info(f"Volume: {last_row['volume']:.2f}")
            return True
            
        return False

    def place_buy_order(self, symbol, price):
        """Place a buy order"""
        try:
            balance = self.get_account_balance()
            quantity = (balance * config.POSITION_SIZE) / price
            quantity = float(f"{quantity:.6f}")  # Format to 6 decimal places

            logger.info(f"Attempting to place buy order for {symbol}:")
            logger.info(f"Current price: {price:.2f} USDT")
            logger.info(f"Available balance: {balance:.4f} USDT")
            logger.info(f"Quantity to buy: {quantity:.6f}")

            order = self.client.create_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=quantity
            )
            
            self.total_trades += 1
            self.trades_today += 1
            
            avg_price = float(order['fills'][0]['price'])
            executed_qty = float(order['executedQty'])
            cost = avg_price * executed_qty
            
            logger.info(f"Buy order executed successfully for {symbol}:")
            logger.info(f"Order ID: {order['orderId']}")
            logger.info(f"Average price: {avg_price:.2f} USDT")
            logger.info(f"Executed quantity: {executed_qty:.6f}")
            logger.info(f"Total cost: {cost:.4f} USDT")
            
            self.positions[symbol] = {
                'entry_price': avg_price,
                'quantity': executed_qty,
                'stop_loss': avg_price * (1 - config.STOP_LOSS_PERCENTAGE),
                'take_profit': avg_price * (1 + config.TAKE_PROFIT_PERCENTAGE),
                'order_id': order['orderId'],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Position details for {symbol}:")
            logger.info(f"Stop Loss: {self.positions[symbol]['stop_loss']:.2f} USDT")
            logger.info(f"Take Profit: {self.positions[symbol]['take_profit']:.2f} USDT")
            
            # Create trade data for visualization
            trade_data = {
                'buy_time': datetime.now().isoformat(),
                'buy_price': avg_price,
                'stop_loss': self.positions[symbol]['stop_loss'],
                'take_profit': self.positions[symbol]['take_profit'],
                'ema_fast': config.EMA_FAST,
                'ema_slow': config.EMA_SLOW
            }
            
            # Generate and save the graph
            graph_path = self.visualizer.plot_trade(df, symbol, trade_data,
                f"trade_{symbol}_entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            if graph_path:
                logger.info(f"Trade entry graph saved to: {graph_path}")
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error while placing buy order for {symbol}: {str(e)}")
            logger.error(f"Error code: {e.code}")
            logger.error(f"Error message: {e.message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while placing buy order for {symbol}: {str(e)}")
            return False

    def place_sell_order(self, symbol):
        """Place a sell order"""
        try:
            if symbol not in self.positions:
                logger.warning(f"Attempted to sell {symbol} without an open position")
                return False

            logger.info(f"Attempting to sell position for {symbol}:")
            logger.info(f"Position quantity: {self.positions[symbol]['quantity']:.6f}")
            logger.info(f"Entry price: {self.positions[symbol]['entry_price']:.2f} USDT")

            order = self.client.create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=self.positions[symbol]['quantity']
            )
            
            avg_price = float(order['fills'][0]['price'])
            executed_qty = float(order['executedQty'])
            revenue = avg_price * executed_qty
            profit = revenue - (self.positions[symbol]['entry_price'] * executed_qty)
            
            logger.info(f"Sell order executed successfully for {symbol}:")
            logger.info(f"Order ID: {order['orderId']}")
            logger.info(f"Average price: {avg_price:.2f} USDT")
            logger.info(f"Executed quantity: {executed_qty:.6f}")
            logger.info(f"Total revenue: {revenue:.4f} USDT")
            logger.info(f"Profit/Loss: {profit:.4f} USDT")
            
            if profit < 0:
                self.daily_loss += abs(profit)
                self.failed_trades += 1
                logger.warning(f"Trade resulted in loss for {symbol}. Daily loss: {self.daily_loss:.4f} USDT")
            else:
                self.successful_trades += 1
                logger.info(f"Trade resulted in profit for {symbol}: {profit:.4f} USDT")
            
            hold_time = datetime.now() - datetime.fromisoformat(self.positions[symbol]['timestamp'])
            logger.info(f"Position held for {symbol}: {hold_time}")
            
            # Calculate trade duration
            start_time = datetime.fromisoformat(self.positions[symbol]['timestamp'])
            duration = datetime.now() - start_time
            
            # Create trade data for visualization
            trade_data = {
                'buy_time': self.positions[symbol]['timestamp'],
                'buy_price': self.positions[symbol]['entry_price'],
                'sell_time': datetime.now().isoformat(),
                'sell_price': avg_price,
                'profit': profit,
                'duration': str(duration),
                'ema_fast': config.EMA_FAST,
                'ema_slow': config.EMA_SLOW
            }
            
            # Generate and save the graph
            graph_path = self.visualizer.plot_trade(df, symbol, trade_data,
                f"trade_{symbol}_exit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            if graph_path:
                logger.info(f"Trade exit graph saved to: {graph_path}")
            
            # Update performance data
            self.performance_data['timestamps'].append(datetime.now().isoformat())
            self.performance_data['balances'].append(self.get_account_balance())
            if profit > 0:
                self.performance_data['successful_trades'] += 1
            else:
                self.performance_data['failed_trades'] += 1
            
            # Generate performance graph every 10 trades
            total_trades = (self.performance_data['successful_trades'] + 
                          self.performance_data['failed_trades'])
            if total_trades % 10 == 0:
                perf_graph_path = self.visualizer.create_performance_graph(
                    self.performance_data,
                    f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                if perf_graph_path:
                    logger.info(f"Performance graph saved to: {perf_graph_path}")
            
            del self.positions[symbol]
            self.log_performance_metrics()
            return True
        except BinanceAPIException as e:
            logger.error(f"Binance API error while placing sell order for {symbol}: {str(e)}")
            logger.error(f"Error code: {e.code}")
            logger.error(f"Error message: {e.message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while placing sell order for {symbol}: {str(e)}")
            return False

    def check_stop_loss_take_profit(self, current_price, symbol):
        """Check if we should exit position based on SL/TP"""
        if symbol not in self.positions:
            return False

        if (current_price <= self.positions[symbol]['stop_loss'] or 
            current_price >= self.positions[symbol]['take_profit']):
            return self.place_sell_order(symbol)
        return False

    def run(self):
        """Enhanced main trading loop"""
        logger.info("Starting trading bot...")
        last_performance_log = datetime.now()
        last_pairs_update = datetime.now()
        
        while True:
            try:
                current_time = datetime.now()
                
                # Update trading pairs info every 5 minutes
                if (current_time - last_pairs_update).seconds >= 300:
                    self.update_trading_pairs_info()
                    last_pairs_update = current_time
                
                # Reset daily counters at midnight
                if current_time.hour == 0 and current_time.minute == 0:
                    logger.info("Resetting daily counters")
                    self.trades_today = 0
                    self.daily_loss = 0
                
                # Log performance metrics every hour
                if (current_time - last_performance_log).seconds >= 3600:
                    self.log_performance_metrics()
                    last_performance_log = current_time

                # Check daily limits
                if self.trades_today >= config.MAX_DAILY_TRADES:
                    logger.warning("Daily trade limit reached")
                    time.sleep(60)
                    continue
                
                if self.daily_loss >= (config.INITIAL_INVESTMENT * config.MAX_DAILY_LOSS_PERCENTAGE):
                    logger.warning("Daily loss limit reached")
                    time.sleep(60)
                    continue

                # Iterate through all trading pairs
                for symbol in config.TRADING_PAIRS:
                    try:
                        # Get market data
                        df = self.get_historical_data(symbol)
                        if df is None:
                            continue

                        df = self.calculate_indicators(df)
                        if df is None:
                            continue

                        current_price = float(df.iloc[-1]['close'])
                        logger.info(f"Current {symbol} price: {current_price:.2f} USDT")

                        # Check existing position
                        if symbol in self.positions:
                            if self.check_stop_loss_take_profit(current_price, symbol):
                                continue
                            if self.should_sell(df, symbol):
                                logger.info(f"Sell signal detected for {symbol}")
                                self.place_sell_order(symbol)
                        else:
                            if self.should_buy(df, symbol):
                                logger.info(f"Buy signal detected for {symbol}")
                                self.place_buy_order(symbol, current_price)
                    
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {str(e)}")
                        continue

                time.sleep(10)  # Reduced sleep time for more active trading

            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
