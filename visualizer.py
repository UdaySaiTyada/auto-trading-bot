import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from datetime import datetime
import os
from pathlib import Path

class TradeVisualizer:
    def __init__(self):
        self.graphs_dir = Path("graphs")
        self.graphs_dir.mkdir(exist_ok=True)
        
        # Set style for plots
        plt.style.use('dark_background')
        
    def plot_trade(self, df, symbol, trade_data, filename=None):
        """
        Create a candlestick chart with trade entry/exit points
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading pair symbol
            trade_data: Dict containing trade information
            filename: Optional filename for saving the plot
        """
        try:
            # Convert timestamp to datetime
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            
            # Prepare the candlestick data
            df_plot = df[['open', 'high', 'low', 'close', 'volume']].copy()
            
            # Create the plot
            fig, axes = mpf.plot(df_plot, type='candle', style='charles',
                               volume=True, returnfig=True,
                               title=f'\n{symbol} Trading Activity\n',
                               figsize=(15, 10))
            
            ax1 = axes[0]  # Price axis
            ax2 = axes[2]  # Volume axis
            
            # Add RSI
            ax3 = ax1.twinx()
            ax3.plot(df.index, df['RSI'], color='purple', alpha=0.7, label='RSI')
            ax3.axhline(y=30, color='g', linestyle='--', alpha=0.5)
            ax3.axhline(y=70, color='r', linestyle='--', alpha=0.5)
            
            # Add EMAs
            ax1.plot(df.index, df['EMA_fast'], color='yellow', alpha=0.7, label=f'EMA {trade_data["ema_fast"]}')
            ax1.plot(df.index, df['EMA_slow'], color='blue', alpha=0.7, label=f'EMA {trade_data["ema_slow"]}')
            
            # Add buy point
            if 'buy_time' in trade_data:
                buy_time = pd.to_datetime(trade_data['buy_time'])
                if buy_time in df.index:
                    ax1.scatter(buy_time, trade_data['buy_price'], 
                              color='g', marker='^', s=100, label='Buy')
                    ax1.axhline(y=trade_data['buy_price'], color='g', 
                              linestyle='--', alpha=0.3)
            
            # Add sell point
            if 'sell_time' in trade_data:
                sell_time = pd.to_datetime(trade_data['sell_time'])
                if sell_time in df.index:
                    ax1.scatter(sell_time, trade_data['sell_price'], 
                              color='r', marker='v', s=100, label='Sell')
                    ax1.axhline(y=trade_data['sell_price'], color='r', 
                              linestyle='--', alpha=0.3)
            
            # Add stop loss and take profit lines if trade is active
            if 'buy_price' in trade_data and 'sell_time' not in trade_data:
                ax1.axhline(y=trade_data['stop_loss'], color='r', 
                          linestyle=':', alpha=0.5, label='Stop Loss')
                ax1.axhline(y=trade_data['take_profit'], color='g', 
                          linestyle=':', alpha=0.5, label='Take Profit')
            
            # Add profit/loss annotation
            if 'profit' in trade_data:
                profit_color = 'g' if trade_data['profit'] > 0 else 'r'
                plt.figtext(0.15, 0.95, f"Profit/Loss: {trade_data['profit']:.4f} USDT",
                          color=profit_color, fontsize=10)
            
            # Add trade duration if available
            if 'duration' in trade_data:
                plt.figtext(0.35, 0.95, f"Duration: {trade_data['duration']}",
                          color='white', fontsize=10)
            
            # Add legends
            ax1.legend(loc='upper left')
            ax3.legend(loc='upper right')
            
            # Save the plot
            if filename is None:
                filename = f"trade_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            plt.savefig(self.graphs_dir / filename, bbox_inches='tight', dpi=300)
            plt.close()
            
            return str(self.graphs_dir / filename)
            
        except Exception as e:
            print(f"Error creating trade visualization: {str(e)}")
            return None
    
    def create_performance_graph(self, performance_data, filename=None):
        """
        Create a performance overview graph
        
        Args:
            performance_data: Dict containing performance metrics
            filename: Optional filename for saving the plot
        """
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
            
            # Plot balance over time
            times = [pd.to_datetime(x) for x in performance_data['timestamps']]
            ax1.plot(times, performance_data['balances'], color='g', label='Account Balance')
            ax1.set_title('Account Balance Over Time')
            ax1.set_ylabel('USDT')
            ax1.grid(True, alpha=0.3)
            
            # Plot win rate and trade count
            ax2.bar(['Successful', 'Failed'], 
                   [performance_data['successful_trades'], performance_data['failed_trades']],
                   color=['g', 'r'])
            ax2.set_title('Trade Performance')
            ax2.set_ylabel('Number of Trades')
            
            # Add win rate annotation
            win_rate = (performance_data['successful_trades'] / 
                       (performance_data['successful_trades'] + performance_data['failed_trades']) 
                       * 100 if performance_data['successful_trades'] + performance_data['failed_trades'] > 0 else 0)
            plt.figtext(0.15, 0.95, f"Win Rate: {win_rate:.2f}%",
                       color='white', fontsize=10)
            
            if filename is None:
                filename = f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            plt.savefig(self.graphs_dir / filename, bbox_inches='tight', dpi=300)
            plt.close()
            
            return str(self.graphs_dir / filename)
            
        except Exception as e:
            print(f"Error creating performance visualization: {str(e)}")
            return None
