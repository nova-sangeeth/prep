class StockPortfolioTracker:
    def __init__(self, transactions, current_prices):
        self.transactions = transactions
        self.current_prices = current_prices

    def filter_holdings_by_value(self, threshold):
        shares_held = {}
        
        for tx in self.transactions:
            action, ticker, shares = tx
            
            if ticker not in shares_held:
                shares_held[ticker] = 0
                
            # BUG 1: Treating SELL as a purchase (adding instead of subtracting shares)
            if action == "BUY":
                shares_held[ticker] += shares
            elif action == "SELL":
                # Incorrectly adding or doing nothing instead of decrementing
                shares_held[ticker] += shares  # <-- Bug here! Should be -= shares

        below_threshold = []
        above_threshold = []
        
        for ticker, shares in shares_held.items():
            # BUG 2: Missing price multiplication (comparing share count instead of total market value)
            market_value = shares  # <-- Bug here! Should be shares * self.current_prices[ticker]
            
            # BUG 3: Incorrect boundary check (strict '>' instead of '>=')
            if market_value > threshold:  # <-- Bug here! Should be >= threshold
                above_threshold.append(ticker)
            else:
                below_threshold.append(ticker)
                
        return [below_threshold, above_threshold]

# --- Test Runner ---
if __name__ == "__main__":
    transactions = [
        ["BUY", "AAPL", 10],
        ["BUY", "MSFT", 5],
        ["SELL", "AAPL", 2],
        ["BUY", "GOOG", 4],
        ["SELL", "MSFT", 1],
        ["BUY", "AAPL", 3]
    ]
    
    current_prices = {
        "AAPL": 150,  # 11 shares * 150 = 1650
        "MSFT": 300,  # 4 shares * 300 = 1200
        "GOOG": 100   # 4 shares * 100 = 400
    }
    
    tracker = StockPortfolioTracker(transactions, current_prices)
    
    print("Testing Threshold = 1500:")
    print("Result:", tracker.filter_holdings_by_value(1500))
    print("Expected: [['MSFT', 'GOOG'], ['AAPL']] (order may vary)\n")
    
    print("Testing Threshold = 1200:")
    print("Result:", tracker.filter_holdings_by_value(1200))
    print("Expected: [['GOOG'], ['AAPL', 'MSFT']]\n")