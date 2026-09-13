"""
Task 1: Write a function calculate_net_balances(transactions) that processes
this list and returns a dictionary mapping each account to its net balance.
(Note: Credits add to the balance, debits subtract from it. Ignore any transactions where status is not "COMPLETED").
"""

"""
Great. Now, we need to flag accounts that violate a certain risk threshold. 
Modify or extend the logic to return only the accounts whose final net balance drops 
below a specific threshold (e.g., 0 or a custom limit).
"""

"""
What if some dictionaries have missing keys (like no amount or a None value), 
or an unexpected type value? Update your function to safely skip invalid 
records and log/count how many errors were encountered during processing.
"""
from collections import defaultdict

transactions = [
    # --- ACC_01: Normal valid mix (Should end up positive: +700.0) ---
    {"id": "T1", "account": "ACC_01", "type": "CREDIT", "amount": 1000.0, "status": "COMPLETED"},
    {
        "id": "T2",
        "account": "ACC_01",
        "type": "DEBIT",
        "amount": 200.0,
        "status": "PENDING",
    },  # Should be ignored (not COMPLETED)
    {"id": "T3", "account": "ACC_01", "type": "DEBIT", "amount": 300.0, "status": "COMPLETED"},
    # --- ACC_02: Heavy debits (Should end up negative: -650.0, triggers risk threshold < 0) ---
    {"id": "T4", "account": "ACC_02", "type": "DEBIT", "amount": 500.0, "status": "COMPLETED"},
    {"id": "T5", "account": "ACC_02", "type": "CREDIT", "amount": 100.0, "status": "COMPLETED"},
    {"id": "T6", "account": "ACC_02", "type": "DEBIT", "amount": 250.0, "status": "COMPLETED"},
    # --- ACC_03: Edge cases & Errors (Missing keys, None values, invalid types) ---
    {"id": "T7", "account": "ACC_03", "type": "CREDIT", "amount": 500.0, "status": "COMPLETED"},  # Valid (+500)
    {"id": "T8", "account": "ACC_03", "type": "CREDIT", "amount": None, "status": "COMPLETED"},  # Error: Amount is None
    {"id": "T9", "account": "ACC_03", "type": "DEBIT", "status": "COMPLETED"},  # Error: Missing 'amount' key entirely
    {"id": "T10", "amount": 100.0, "status": "COMPLETED"},  # Error: Missing 'account' key entirely
    # --- ACC_04: Invalid data types and status ---
    {
        "id": "T11",
        "account": "ACC_04",
        "type": "CREDIT",
        "amount": "three-hundred",
        "status": "COMPLETED",
    },  # Error: Amount is a string
    {
        "id": "T12",
        "account": "ACC_04",
        "type": "UNKNOWN",
        "amount": 50.0,
        "status": "COMPLETED",
    },  # Error/Edge: Unknown transaction type
    {
        "id": "T13",
        "account": "ACC_04",
        "type": "CREDIT",
        "amount": 200.0,
        "status": "FAILED",
    },  # Ignored (status not COMPLETED)
]


def calculate_net_balances(data: list[dict], violation_threshold: float) -> dict[float]:
    """
    Process information from list
    """
    account_map = defaultdict(float)

    for transaction in data:
        account = transaction.get("account")
        type = transaction.get("type")
        amount = transaction.get("amount")
        status = transaction.get("status")

        if status == "COMPLETED":
            if amount is not None and isinstance(amount, (int, float)):
                if type == "CREDIT":
                    account_map[account] += amount
                elif type == "DEBIT":
                    account_map[account] -= amount
                else:
                    print(f"Invalid type detected {type}")
            else:
                print(f"Invalid type amount detected {amount}")
        else:
            print(f"Invalid status detected {status}")

    flagged_acc = {acc: balance for acc, balance in account_map.items() if balance < violation_threshold}
    safe_acc = {acc: balance for acc, balance in account_map.items() if balance >= violation_threshold}
    print("flagged_acc")
    print(flagged_acc)
    print("safe_acc")
    print(safe_acc)
    agg_acc = sorted(safe_acc, key=lambda item: safe_acc.get(item))
    print("agg_acc")
    print(agg_acc)


calculate_net_balances(data=transactions, violation_threshold=30.0)
