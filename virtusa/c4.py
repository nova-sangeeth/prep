"""
You are tasked with building a class PortfolioTracker that processes 
a stream of trade transactions for different assets and tracks the net quantity held for each asset.

The Baseline Setup (Part A)
Each trade comes in as a dictionary containing:

symbol: Asset ticker (e.g., "AAPL", "GOOG")
action: Either "BUY" or "SELL"
quantity: Number of units (integer)
price: Execution price per unit (float)
Task: Implement a class that allows recording trades and calculating the net current quantity of each asset.

Rule: A "BUY" adds to the quantity; a "SELL" subtracts from it.
"""
from collections import defaultdict

class PortfolioTracker:
    def __init__(self):
        # Hint: Think about what data structure to use here
        self.trades = defaultdict(dict)

    def record_trade(self, trade: dict):
        """Processes a single trade record and updates holdings."""
        

    def get_position(self, symbol: str) -> int:
        """Returns the current net quantity for a given asset symbol."""
        pass