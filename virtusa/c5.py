## Rate-Limit Violation Detector

"""
A mobile app backend must detect users who exceed rate limits within sliding time windows to prevent abuse. 
Your task is to implement a rate-limit tracker that counts API requests per user within a configurable 
time window and identifies repeat offenders.
"""

### Part A — Bug Fix

"""
Read through and understand the code below. 
The assertion testing `count_requests_in_window()` is not passing due to a bug in the `RateLimitTracker` class. 
Make the necessary changes to fix the bug.
"""
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import heapq


class RateLimitTracker:
    """Analyzes API request events to detect rate-limit violations within sliding time windows."""

    def __init__(self, window_seconds=60):
        # Initialize tracker with configurable time window in seconds
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # user_id -> list of (timestamp_seconds)
        self.violation_count = defaultdict(int)  # user_id -> violation count

    def log_request(self, user_id, timestamp_seconds):
        # Record an API request for a user at a given Unix timestamp
        self.requests[user_id].append(timestamp_seconds)

    def count_requests_in_window(self, user_id, end_timestamp_seconds):
        """Count requests for user within [end_timestamp - window, end_timestamp)."""
        if user_id not in self.requests:
            return 0
        window_start = end_timestamp_seconds - self.window_seconds
        count = 0
        for ts in self.requests[user_id]:
            if window_start <= ts < end_timestamp_seconds:
                count += 1
        return count

    def check_violation(self, user_id, limit, end_timestamp_seconds):
        # Check if user exceeded request limit; increment violation counter if true
        request_count = self.count_requests_in_window(user_id, end_timestamp_seconds)
        if request_count > limit:
            self.violation_count[user_id] += 1
            return True
        return False

    def get_violations(self, user_id):
        # Return total violation count for a user
        return self.violation_count[user_id]


def main():
    # Initialize tracker with 10-second sliding window
    tracker = RateLimitTracker(window_seconds=10)

    # User alice: requests at t=0, 5, 10 seconds
    # At t=10: window is [0, 10) — should count requests at 0, 5 (not 10)
    tracker.log_request("alice", 0)
    tracker.log_request("alice", 5)
    tracker.log_request("alice", 10)

    # User bob: requests at t=100, 105, 110 seconds
    # At t=110: window is [100, 110) — should count requests at 100, 105 (not 110)
    tracker.log_request("bob", 100)
    tracker.log_request("bob", 105)
    tracker.log_request("bob", 110)

    # User charlie: requests at t=200, 201, 202 seconds
    # At t=210: window is [200, 210) — should count all 3 requests
    tracker.log_request("charlie", 200)
    tracker.log_request("charlie", 201)
    tracker.log_request("charlie", 202)

    # Verify alice has 2 requests in window [0, 10)
    assert tracker.count_requests_in_window("alice", 10) == 2, "alice should have 2 requests at boundary"

    # Verify bob has 2 requests in window [100, 110)
    assert tracker.count_requests_in_window("bob", 110) == 2, "bob should have 2 requests at boundary"

    # Verify charlie has 3 requests in window [200, 210)
    assert tracker.count_requests_in_window("charlie", 210) == 3, "charlie should have 3 requests in window"

    # Verify violation detection with limit=2: alice at t=10 should not violate (exactly 2 requests)
    assert tracker.check_violation("alice", 2, 10) == False, "alice with 2 requests should not exceed limit 2"

    # Verify violation detection: charlie at t=210 should violate (3 requests > limit 2)
    assert tracker.check_violation("charlie", 2, 210) == True, "charlie with 3 requests should exceed limit 2"

    # Verify violation counter incremented for charlie
    assert tracker.get_violations("charlie") == 1, "charlie should have 1 violation"

    print("All tests passed!")


if __name__ == "__main__":
    main()

### Part B — New Feature

"""
Add method get_top_offenders(n) to the RateLimitTracker class that returns a list of the top n users by violation count, 
sorted in descending order by violation count (ties broken alphabetically by user_id). 
The method should return a list of tuples (user_id, violation_count).
 
"""
# Test get_top_offenders with multiple violations
tracker2 = RateLimitTracker(window_seconds=10)
tracker2.violation_count["user_a"] = 5
tracker2.violation_count["user_b"] = 3
tracker2.violation_count["user_c"] = 5
assert tracker2.get_top_offenders(2) == [
    ("user_a", 5),
    ("user_c", 5),
], "top 2 offenders sorted by count then alphabetically"
assert tracker2.get_top_offenders(1) == [("user_a", 5)], "top 1 offender"
assert tracker2.get_top_offenders(5) == [
    ("user_a", 5),
    ("user_c", 5),
    ("user_b", 3),
], "request more than available returns all sorted"
assert tracker2.get_top_offenders(0) == [], "requesting 0 offenders returns empty list"
