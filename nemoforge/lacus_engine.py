import json
import os
import pandas as pd
import numpy as np

class LacusEngine:
    """
    Lacus Backtest Engine - Production-grade frictionless & real-friction simulator
    Supports both Spot and Futures trading across all Kraken contracts dynamically.
    """
    def __init__(self, initial_capital=50000.0, fee_rate=0.0026, slippage_rate=0.0):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        
        # Simulated Wallet State
        self.capital = initial_capital
        self.positions = {}  # Symbol -> {"size": float, "entry_price": float, "leverage": float}
        self.trade_history = []
        self.equity_curve = []
        
    def reset(self):
        self.capital = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.equity_curve = []

    def load_ohlcv(self, filepath):
        """Loads historical candles (expects columns: timestamp, open, high, low, close, volume)"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Historical data file not found: {filepath}")
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp')

    def execute_order(self, symbol, action, volume, price, leverage=1.0, timestamp=None):
        """
        Executes a simulated paper order.
        - action: 'buy' (long) or 'sell' (short)
        - leverage: leverage factor for Futures
        """
        nominal_value = volume * price
        slippage_drag = nominal_value * self.slippage_rate
        fee = nominal_value * self.fee_rate
        
        # Adjust execution price for slippage
        exec_price = price
        if action == 'buy':
            exec_price += price * self.slippage_rate
        else:
            exec_price -= price * self.slippage_rate
            
        margin_required = nominal_value / leverage
        if margin_required > self.capital and symbol not in self.positions:
            return {"status": "error", "reason": "Insufficient margin"}
            
        # Capital reduction on fees
        self.capital -= fee
        
        if symbol not in self.positions:
            # Open new position
            self.positions[symbol] = {
                "size": volume if action == 'buy' else -volume,
                "entry_price": exec_price,
                "leverage": leverage,
                "opened_at": timestamp
            }
        else:
            # Manage existing position (simple partial close or addition)
            pos = self.positions[symbol]
            current_size = pos["size"]
            
            if (current_size > 0 and action == 'sell') or (current_size < 0 and action == 'buy'):
                # Close or reduce position
                realized_pnl = 0.0
                if current_size > 0: # Long
                    realized_pnl = (exec_price - pos["entry_price"]) * min(volume, abs(current_size))
                else: # Short
                    realized_pnl = (pos["entry_price"] - exec_price) * min(volume, abs(current_size))
                    
                self.capital += realized_pnl
                
                # Update size
                new_size = current_size - volume if current_size > 0 else current_size + volume
                if abs(new_size) < 1e-8:
                    del self.positions[symbol]
                else:
                    self.positions[symbol]["size"] = new_size
            else:
                # Add to position (averaging entry price)
                total_size = current_size + (volume if action == 'buy' else -volume)
                new_entry = ((pos["entry_price"] * abs(current_size)) + (exec_price * volume)) / abs(total_size)
                self.positions[symbol]["size"] = total_size
                self.positions[symbol]["entry_price"] = new_entry

        trade_record = {
            "timestamp": str(timestamp) if timestamp else str(datetime.now()),
            "symbol": symbol,
            "action": action,
            "volume": volume,
            "price": exec_price,
            "fee": fee,
            "capital_after": self.capital
        }
        self.trade_history.append(trade_record)
        return {"status": "success", "record": trade_record}

    def get_equity(self, current_prices):
        """Returns current unified equity (capital + unrealized PnL)"""
        unrealized_pnl = 0.0
        for symbol, pos in self.positions.items():
            current_price = current_prices.get(symbol)
            if not current_price:
                continue
            size = pos["size"]
            if size > 0: # Long
                unrealized_pnl += (current_price - pos["entry_price"]) * size
            else: # Short
                unrealized_pnl += (pos["entry_price"] - current_price) * abs(size)
        return self.capital + unrealized_pnl
