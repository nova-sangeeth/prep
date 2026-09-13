"""
Given a list of transaction dictionaries
(e.g., [{'id': 1, 'account': 'A', 'amount': 150.0}, {'id': 2, 'account': 'B', 'amount': -50.0}]),
write a function that filters out transactions with missing amounts,
aggregates the net balance per account, and returns a sorted list of accounts by their final balance in descending order.

"""

from collections import defaultdict

transactions_1 = [
    {"id": 1, "account": "A", "amount": 100.0},
    {"id": 2, "account": "B", "amount": 250.0},
    {"id": 3, "account": "A", "amount": -50.0},
    {"id": 4, "account": "C", "amount": None},  # Missing amount (None)
    {"id": 5, "account": "B", "amount": -100.0},
    {"id": 6, "account": "A"},  # Missing amount key entirely
    {"id": 7, "account": "C", "amount": 75.0},
]


def main(data: list[dict]) -> list[str]:
    agg_data = defaultdict(float)

    # Check of transactions with no amounts
    for transaction in data:
        account = transaction.get("account")
        amount = transaction.get("amount")

        if amount is not None:
            if isinstance(amount, (float, int)):
                agg_data[account] += amount

    print(agg_data)
    account_keys = agg_data.keys()
    result = sorted(account_keys, key=lambda item: agg_data[item], reverse=True)
    print(result)
    return result
 

main(data=transactions_1)
