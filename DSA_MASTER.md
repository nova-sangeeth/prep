# DSA — Master Reference

Generated dump of every solution under `dsa/`. Each problem: source file path + full code.

## Index (from `dsa/README.md`)

# DSA — NeetCode 150

150 essential coding-interview problems, one self-contained `.py` per problem: problem statement + approach + Big-O in the docstring, typed solution, inline `assert` tests.

Run any file directly to execute its tests:

```bash
python3 arrays_hashing/two_sum.py   # -> ok
```

## Tiers

Each file is tagged with the smallest list it belongs to. Tiers nest: **core ⊂ Blind 75 ⊂ NeetCode 150**.

| Badge | Tier | Count | Use |
|---|---|---|---|
| 🟢50 | core | 47 | highest-frequency must-knows |
| 🔵75 | Blind 75 | 78 | standard interview prep |
| ⚪150 | NeetCode 150 | 150 | thorough coverage |

## Problems by category

### Arrays & Hashing (9)

| Problem | Tiers | File |
|---|---|---|
| Contains Duplicate | 🟢50 🔵75 ⚪150 | [`contains_duplicate.py`](arrays_hashing/contains_duplicate.py) |
| Encode and Decode Strings | 🔵75 ⚪150 | [`encode_decode_strings.py`](arrays_hashing/encode_decode_strings.py) |
| Group Anagrams | 🟢50 🔵75 ⚪150 | [`group_anagrams.py`](arrays_hashing/group_anagrams.py) |
| Longest Consecutive Sequence | 🔵75 ⚪150 | [`longest_consecutive.py`](arrays_hashing/longest_consecutive.py) |
| Product of Array Except Self | 🔵75 ⚪150 | [`product_except_self.py`](arrays_hashing/product_except_self.py) |
| Top K Frequent Elements | 🔵75 ⚪150 | [`top_k_frequent.py`](arrays_hashing/top_k_frequent.py) |
| Two Sum | 🟢50 🔵75 ⚪150 | [`two_sum.py`](arrays_hashing/two_sum.py) |
| Valid Anagram | 🟢50 🔵75 ⚪150 | [`valid_anagram.py`](arrays_hashing/valid_anagram.py) |
| Valid Sudoku | ⚪150 | [`valid_sudoku.py`](arrays_hashing/valid_sudoku.py) |

### Two Pointers (5)

| Problem | Tiers | File |
|---|---|---|
| Container With Most Water | 🟢50 🔵75 ⚪150 | [`container_with_most_water.py`](two_pointers/container_with_most_water.py) |
| 3Sum | 🟢50 🔵75 ⚪150 | [`three_sum.py`](two_pointers/three_sum.py) |
| Trapping Rain Water | 🟢50 ⚪150 | [`trapping_rain_water.py`](two_pointers/trapping_rain_water.py) |
| Two Sum II (Input Sorted) | ⚪150 | [`two_sum_ii_sorted.py`](two_pointers/two_sum_ii_sorted.py) |
| Valid Palindrome | 🟢50 🔵75 ⚪150 | [`valid_palindrome.py`](two_pointers/valid_palindrome.py) |

### Sliding Window (6)

| Problem | Tiers | File |
|---|---|---|
| Best Time to Buy and Sell Stock | 🟢50 🔵75 ⚪150 | [`best_time_buy_sell_stock.py`](sliding_window/best_time_buy_sell_stock.py) |
| Longest Repeating Character Replacement | 🟢50 🔵75 ⚪150 | [`longest_repeating_char_replacement.py`](sliding_window/longest_repeating_char_replacement.py) |
| Longest Substring Without Repeating Characters | 🟢50 🔵75 ⚪150 | [`longest_substring_without_repeating.py`](sliding_window/longest_substring_without_repeating.py) |
| Minimum Window Substring | 🔵75 ⚪150 | [`minimum_window_substring.py`](sliding_window/minimum_window_substring.py) |
| Permutation in String | ⚪150 | [`permutation_in_string.py`](sliding_window/permutation_in_string.py) |
| Sliding Window Maximum | ⚪150 | [`sliding_window_maximum.py`](sliding_window/sliding_window_maximum.py) |

### Stack (7)

| Problem | Tiers | File |
|---|---|---|
| Car Fleet | ⚪150 | [`car_fleet.py`](stack/car_fleet.py) |
| Daily Temperatures | 🟢50 ⚪150 | [`daily_temperatures.py`](stack/daily_temperatures.py) |
| Evaluate Reverse Polish Notation | 🟢50 ⚪150 | [`eval_reverse_polish.py`](stack/eval_reverse_polish.py) |
| Generate Parentheses | ⚪150 | [`generate_parentheses.py`](stack/generate_parentheses.py) |
| Largest Rectangle in Histogram | ⚪150 | [`largest_rectangle_histogram.py`](stack/largest_rectangle_histogram.py) |
| Min Stack | 🔵75 ⚪150 | [`min_stack.py`](stack/min_stack.py) |
| Valid Parentheses | 🟢50 🔵75 ⚪150 | [`valid_parentheses.py`](stack/valid_parentheses.py) |

### Binary Search (7)

| Problem | Tiers | File |
|---|---|---|
| Binary Search | 🟢50 ⚪150 | [`binary_search.py`](binary_search/binary_search.py) |
| Find Minimum in Rotated Sorted Array | 🟢50 🔵75 ⚪150 | [`find_min_rotated.py`](binary_search/find_min_rotated.py) |
| Koko Eating Bananas | 🟢50 ⚪150 | [`koko_eating_bananas.py`](binary_search/koko_eating_bananas.py) |
| Median of Two Sorted Arrays | ⚪150 | [`median_two_sorted_arrays.py`](binary_search/median_two_sorted_arrays.py) |
| Search a 2D Matrix | ⚪150 | [`search_2d_matrix.py`](binary_search/search_2d_matrix.py) |
| Search in Rotated Sorted Array | 🟢50 🔵75 ⚪150 | [`search_rotated.py`](binary_search/search_rotated.py) |
| Time Based Key-Value Store | ⚪150 | [`time_based_kv_store.py`](binary_search/time_based_kv_store.py) |

### Linked List (11)

| Problem | Tiers | File |
|---|---|---|
| Add Two Numbers | ⚪150 | [`add_two_numbers.py`](linked_list/add_two_numbers.py) |
| Copy List with Random Pointer | ⚪150 | [`copy_list_random_pointer.py`](linked_list/copy_list_random_pointer.py) |
| Find the Duplicate Number | ⚪150 | [`find_duplicate_number.py`](linked_list/find_duplicate_number.py) |
| Linked List Cycle | 🟢50 🔵75 ⚪150 | [`linked_list_cycle.py`](linked_list/linked_list_cycle.py) |
| LRU Cache | 🟢50 🔵75 ⚪150 | [`lru_cache.py`](linked_list/lru_cache.py) |
| Merge K Sorted Lists | 🔵75 ⚪150 | [`merge_k_sorted_lists.py`](linked_list/merge_k_sorted_lists.py) |
| Merge Two Sorted Lists | 🟢50 🔵75 ⚪150 | [`merge_two_sorted_lists.py`](linked_list/merge_two_sorted_lists.py) |
| Remove Nth Node From End of List | 🟢50 🔵75 ⚪150 | [`remove_nth_from_end.py`](linked_list/remove_nth_from_end.py) |
| Reorder List | 🔵75 ⚪150 | [`reorder_list.py`](linked_list/reorder_list.py) |
| Reverse Linked List | 🟢50 🔵75 ⚪150 | [`reverse_linked_list.py`](linked_list/reverse_linked_list.py) |
| Reverse Nodes in K-Group | ⚪150 | [`reverse_nodes_k_group.py`](linked_list/reverse_nodes_k_group.py) |

### Trees (15)

| Problem | Tiers | File |
|---|---|---|
| Balanced Binary Tree | ⚪150 | [`balanced_binary_tree.py`](trees/balanced_binary_tree.py) |
| Binary Tree Maximum Path Sum | 🔵75 ⚪150 | [`binary_tree_max_path_sum.py`](trees/binary_tree_max_path_sum.py) |
| Construct Binary Tree from Preorder and Inorder | 🔵75 ⚪150 | [`construct_from_preorder_inorder.py`](trees/construct_from_preorder_inorder.py) |
| Count Good Nodes in Binary Tree | ⚪150 | [`count_good_nodes.py`](trees/count_good_nodes.py) |
| Diameter of Binary Tree | ⚪150 | [`diameter_binary_tree.py`](trees/diameter_binary_tree.py) |
| Invert Binary Tree | 🟢50 🔵75 ⚪150 | [`invert_binary_tree.py`](trees/invert_binary_tree.py) |
| Kth Smallest Element in a BST | 🔵75 ⚪150 | [`kth_smallest_bst.py`](trees/kth_smallest_bst.py) |
| Binary Tree Level Order Traversal | 🟢50 🔵75 ⚪150 | [`level_order_traversal.py`](trees/level_order_traversal.py) |
| Lowest Common Ancestor of a BST | 🟢50 🔵75 ⚪150 | [`lowest_common_ancestor_bst.py`](trees/lowest_common_ancestor_bst.py) |
| Maximum Depth of Binary Tree | 🟢50 🔵75 ⚪150 | [`max_depth_binary_tree.py`](trees/max_depth_binary_tree.py) |
| Binary Tree Right Side View | ⚪150 | [`right_side_view.py`](trees/right_side_view.py) |
| Same Tree | 🟢50 🔵75 ⚪150 | [`same_tree.py`](trees/same_tree.py) |
| Serialize and Deserialize Binary Tree | 🔵75 ⚪150 | [`serialize_deserialize.py`](trees/serialize_deserialize.py) |
| Subtree of Another Tree | 🔵75 ⚪150 | [`subtree_of_another_tree.py`](trees/subtree_of_another_tree.py) |
| Validate Binary Search Tree | 🟢50 🔵75 ⚪150 | [`validate_bst.py`](trees/validate_bst.py) |

### Tries (3)

| Problem | Tiers | File |
|---|---|---|
| Design Add and Search Words | 🔵75 ⚪150 | [`design_add_search_words.py`](tries/design_add_search_words.py) |
| Implement Trie (Prefix Tree) | 🟢50 🔵75 ⚪150 | [`implement_trie.py`](tries/implement_trie.py) |
| Word Search II | ⚪150 | [`word_search_ii.py`](tries/word_search_ii.py) |

### Heap (7)

| Problem | Tiers | File |
|---|---|---|
| Design Twitter | ⚪150 | [`design_twitter.py`](heap/design_twitter.py) |
| Find Median from Data Stream | 🔵75 ⚪150 | [`find_median_from_stream.py`](heap/find_median_from_stream.py) |
| K Closest Points to Origin | ⚪150 | [`k_closest_points.py`](heap/k_closest_points.py) |
| Kth Largest Element in an Array | 🟢50 ⚪150 | [`kth_largest_element.py`](heap/kth_largest_element.py) |
| Kth Largest Element in a Stream | ⚪150 | [`kth_largest_in_stream.py`](heap/kth_largest_in_stream.py) |
| Last Stone Weight | ⚪150 | [`last_stone_weight.py`](heap/last_stone_weight.py) |
| Task Scheduler | ⚪150 | [`task_scheduler.py`](heap/task_scheduler.py) |

### Backtracking (9)

| Problem | Tiers | File |
|---|---|---|
| Combination Sum | 🟢50 🔵75 ⚪150 | [`combination_sum.py`](backtracking/combination_sum.py) |
| Combination Sum II | ⚪150 | [`combination_sum_ii.py`](backtracking/combination_sum_ii.py) |
| Letter Combinations of a Phone Number | ⚪150 | [`letter_combinations.py`](backtracking/letter_combinations.py) |
| N-Queens | ⚪150 | [`n_queens.py`](backtracking/n_queens.py) |
| Palindrome Partitioning | ⚪150 | [`palindrome_partitioning.py`](backtracking/palindrome_partitioning.py) |
| Permutations | 🟢50 ⚪150 | [`permutations.py`](backtracking/permutations.py) |
| Subsets | 🟢50 ⚪150 | [`subsets.py`](backtracking/subsets.py) |
| Subsets II | ⚪150 | [`subsets_ii.py`](backtracking/subsets_ii.py) |
| Word Search | 🟢50 🔵75 ⚪150 | [`word_search.py`](backtracking/word_search.py) |

### Graphs (13)

| Problem | Tiers | File |
|---|---|---|
| Clone Graph | 🔵75 ⚪150 | [`clone_graph.py`](graphs/clone_graph.py) |
| Course Schedule | 🟢50 🔵75 ⚪150 | [`course_schedule.py`](graphs/course_schedule.py) |
| Course Schedule II | ⚪150 | [`course_schedule_ii.py`](graphs/course_schedule_ii.py) |
| Graph Valid Tree | 🔵75 ⚪150 | [`graph_valid_tree.py`](graphs/graph_valid_tree.py) |
| Max Area of Island | ⚪150 | [`max_area_of_island.py`](graphs/max_area_of_island.py) |
| Number of Connected Components | 🔵75 ⚪150 | [`number_of_connected_components.py`](graphs/number_of_connected_components.py) |
| Number of Islands | 🟢50 🔵75 ⚪150 | [`number_of_islands.py`](graphs/number_of_islands.py) |
| Pacific Atlantic Water Flow | 🔵75 ⚪150 | [`pacific_atlantic.py`](graphs/pacific_atlantic.py) |
| Redundant Connection | ⚪150 | [`redundant_connection.py`](graphs/redundant_connection.py) |
| Rotting Oranges | ⚪150 | [`rotting_oranges.py`](graphs/rotting_oranges.py) |
| Surrounded Regions | ⚪150 | [`surrounded_regions.py`](graphs/surrounded_regions.py) |
| Walls and Gates | ⚪150 | [`walls_and_gates.py`](graphs/walls_and_gates.py) |
| Word Ladder | ⚪150 | [`word_ladder.py`](graphs/word_ladder.py) |

### Advanced Graphs (6)

| Problem | Tiers | File |
|---|---|---|
| Alien Dictionary | 🔵75 ⚪150 | [`alien_dictionary.py`](advanced_graphs/alien_dictionary.py) |
| Cheapest Flights Within K Stops | ⚪150 | [`cheapest_flights_k_stops.py`](advanced_graphs/cheapest_flights_k_stops.py) |
| Min Cost to Connect All Points | ⚪150 | [`min_cost_connect_points.py`](advanced_graphs/min_cost_connect_points.py) |
| Network Delay Time | ⚪150 | [`network_delay_time.py`](advanced_graphs/network_delay_time.py) |
| Reconstruct Itinerary | ⚪150 | [`reconstruct_itinerary.py`](advanced_graphs/reconstruct_itinerary.py) |
| Swim in Rising Water | ⚪150 | [`swim_in_rising_water.py`](advanced_graphs/swim_in_rising_water.py) |

### 1-D DP (12)

| Problem | Tiers | File |
|---|---|---|
| Climbing Stairs | 🟢50 🔵75 ⚪150 | [`climbing_stairs.py`](dp_1d/climbing_stairs.py) |
| Coin Change | 🟢50 🔵75 ⚪150 | [`coin_change.py`](dp_1d/coin_change.py) |
| Decode Ways | 🔵75 ⚪150 | [`decode_ways.py`](dp_1d/decode_ways.py) |
| House Robber | 🟢50 🔵75 ⚪150 | [`house_robber.py`](dp_1d/house_robber.py) |
| House Robber II | 🔵75 ⚪150 | [`house_robber_ii.py`](dp_1d/house_robber_ii.py) |
| Longest Increasing Subsequence | 🟢50 🔵75 ⚪150 | [`longest_increasing_subsequence.py`](dp_1d/longest_increasing_subsequence.py) |
| Longest Palindromic Substring | 🔵75 ⚪150 | [`longest_palindromic_substring.py`](dp_1d/longest_palindromic_substring.py) |
| Maximum Product Subarray | 🔵75 ⚪150 | [`maximum_product_subarray.py`](dp_1d/maximum_product_subarray.py) |
| Min Cost Climbing Stairs | ⚪150 | [`min_cost_climbing_stairs.py`](dp_1d/min_cost_climbing_stairs.py) |
| Palindromic Substrings | 🔵75 ⚪150 | [`palindromic_substrings.py`](dp_1d/palindromic_substrings.py) |
| Partition Equal Subset Sum | ⚪150 | [`partition_equal_subset_sum.py`](dp_1d/partition_equal_subset_sum.py) |
| Word Break | 🟢50 🔵75 ⚪150 | [`word_break.py`](dp_1d/word_break.py) |

### 2-D DP (11)

| Problem | Tiers | File |
|---|---|---|
| Best Time to Buy/Sell Stock with Cooldown | ⚪150 | [`best_time_buy_sell_cooldown.py`](dp_2d/best_time_buy_sell_cooldown.py) |
| Burst Balloons | ⚪150 | [`burst_balloons.py`](dp_2d/burst_balloons.py) |
| Coin Change II | ⚪150 | [`coin_change_ii.py`](dp_2d/coin_change_ii.py) |
| Distinct Subsequences | ⚪150 | [`distinct_subsequences.py`](dp_2d/distinct_subsequences.py) |
| Edit Distance | 🔵75 ⚪150 | [`edit_distance.py`](dp_2d/edit_distance.py) |
| Interleaving String | ⚪150 | [`interleaving_string.py`](dp_2d/interleaving_string.py) |
| Longest Common Subsequence | 🔵75 ⚪150 | [`longest_common_subsequence.py`](dp_2d/longest_common_subsequence.py) |
| Longest Increasing Path in a Matrix | ⚪150 | [`longest_increasing_path_matrix.py`](dp_2d/longest_increasing_path_matrix.py) |
| Regular Expression Matching | ⚪150 | [`regular_expression_matching.py`](dp_2d/regular_expression_matching.py) |
| Target Sum | ⚪150 | [`target_sum.py`](dp_2d/target_sum.py) |
| Unique Paths | 🔵75 ⚪150 | [`unique_paths.py`](dp_2d/unique_paths.py) |

### Greedy (8)

| Problem | Tiers | File |
|---|---|---|
| Gas Station | ⚪150 | [`gas_station.py`](greedy/gas_station.py) |
| Hand of Straights | ⚪150 | [`hand_of_straights.py`](greedy/hand_of_straights.py) |
| Jump Game | 🟢50 🔵75 ⚪150 | [`jump_game.py`](greedy/jump_game.py) |
| Jump Game II | ⚪150 | [`jump_game_ii.py`](greedy/jump_game_ii.py) |
| Maximum Subarray | 🟢50 🔵75 ⚪150 | [`maximum_subarray.py`](greedy/maximum_subarray.py) |
| Merge Triplets to Form Target | ⚪150 | [`merge_triplets.py`](greedy/merge_triplets.py) |
| Partition Labels | ⚪150 | [`partition_labels.py`](greedy/partition_labels.py) |
| Valid Parenthesis String | ⚪150 | [`valid_parenthesis_string.py`](greedy/valid_parenthesis_string.py) |

### Intervals (6)

| Problem | Tiers | File |
|---|---|---|
| Insert Interval | 🔵75 ⚪150 | [`insert_interval.py`](intervals/insert_interval.py) |
| Meeting Rooms | 🔵75 ⚪150 | [`meeting_rooms.py`](intervals/meeting_rooms.py) |
| Meeting Rooms II | 🔵75 ⚪150 | [`meeting_rooms_ii.py`](intervals/meeting_rooms_ii.py) |
| Merge Intervals | 🟢50 🔵75 ⚪150 | [`merge_intervals.py`](intervals/merge_intervals.py) |
| Minimum Interval to Include Each Query | ⚪150 | [`minimum_interval_query.py`](intervals/minimum_interval_query.py) |
| Non-overlapping Intervals | 🔵75 ⚪150 | [`non_overlapping_intervals.py`](intervals/non_overlapping_intervals.py) |

### Math & Geometry (8)

| Problem | Tiers | File |
|---|---|---|
| Detect Squares | ⚪150 | [`detect_squares.py`](math_geometry/detect_squares.py) |
| Happy Number | ⚪150 | [`happy_number.py`](math_geometry/happy_number.py) |
| Multiply Strings | ⚪150 | [`multiply_strings.py`](math_geometry/multiply_strings.py) |
| Plus One | ⚪150 | [`plus_one.py`](math_geometry/plus_one.py) |
| Pow(x, n) | ⚪150 | [`pow_x_n.py`](math_geometry/pow_x_n.py) |
| Rotate Image | 🔵75 ⚪150 | [`rotate_image.py`](math_geometry/rotate_image.py) |
| Set Matrix Zeroes | 🔵75 ⚪150 | [`set_matrix_zeroes.py`](math_geometry/set_matrix_zeroes.py) |
| Spiral Matrix | 🔵75 ⚪150 | [`spiral_matrix.py`](math_geometry/spiral_matrix.py) |

### Bit Manipulation (7)

| Problem | Tiers | File |
|---|---|---|
| Counting Bits | 🔵75 ⚪150 | [`counting_bits.py`](bit_manipulation/counting_bits.py) |
| Missing Number | 🟢50 🔵75 ⚪150 | [`missing_number.py`](bit_manipulation/missing_number.py) |
| Number of 1 Bits | 🔵75 ⚪150 | [`number_of_1_bits.py`](bit_manipulation/number_of_1_bits.py) |
| Reverse Bits | 🔵75 ⚪150 | [`reverse_bits.py`](bit_manipulation/reverse_bits.py) |
| Reverse Integer | ⚪150 | [`reverse_integer.py`](bit_manipulation/reverse_integer.py) |
| Single Number | 🟢50 🔵75 ⚪150 | [`single_number.py`](bit_manipulation/single_number.py) |
| Sum of Two Integers | 🔵75 ⚪150 | [`sum_of_two_integers.py`](bit_manipulation/sum_of_two_integers.py) |

## Categories

- [Arrays & Hashing](#arrays--hashing)
- [Two Pointers](#two-pointers)
- [Sliding Window](#sliding-window)
- [Stack](#stack)
- [Binary Search](#binary-search)
- [Linked List](#linked-list)
- [Trees](#trees)
- [Tries](#tries)
- [Heap](#heap)
- [Backtracking](#backtracking)
- [Graphs](#graphs)
- [Advanced Graphs](#advanced-graphs)
- [1-D DP](#1-d-dp)
- [2-D DP](#2-d-dp)
- [Greedy](#greedy)
- [Intervals](#intervals)
- [Math & Geometry](#math--geometry)
- [Bit Manipulation](#bit-manipulation)


---

## Arrays & Hashing

### `arrays_hashing/contains_duplicate.py`

```python
"""Contains Duplicate  |  tier: core50, blind75, neetcode150  |  Arrays & Hashing

Given an integer array, return True if any value appears at least twice.

Approach: track seen values in a set; first repeat -> True. A set membership
test is O(1) average, so one pass suffices.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def contains_duplicate(nums: list[int]) -> bool:
    """Return True if any element repeats."""
    seen: set[int] = set()
    for num in nums:
        if num in seen:
            return True
        seen.add(num)
    return False


if __name__ == "__main__":
    assert contains_duplicate([1, 2, 3, 1]) is True
    assert contains_duplicate([1, 2, 3, 4]) is False
    assert contains_duplicate([]) is False
    print("ok")
```

### `arrays_hashing/encode_decode_strings.py`

```python
"""Encode and Decode Strings  |  tier: blind75, neetcode150  |  Arrays & Hashing

Design encode(list[str]) -> str and decode(str) -> list[str] so any list of
strings round-trips, even with delimiters or empty strings inside.

Approach: length-prefix each string as "<len>#<string>". The decoder reads the
length up to '#', then slices exactly that many chars -> content is never
confused with a delimiter.
Time: O(total chars)   Space: O(total chars)
"""
from __future__ import annotations


def encode(strs: list[str]) -> str:
    """Serialize a list of strings to a single string."""
    return "".join(f"{len(string)}#{string}" for string in strs)


def decode(data: str) -> list[str]:
    """Reverse of encode: parse length prefixes to recover the list."""
    result: list[str] = []
    i = 0
    while i < len(data):
        j = i
        while data[j] != "#":
            j += 1
        length = int(data[i:j])
        start = j + 1
        result.append(data[start:start + length])
        i = start + length
    return result


if __name__ == "__main__":
    cases = [["hello", "world"], ["", ""], ["a#b", "3#x", ""], []]
    for case in cases:
        assert decode(encode(case)) == case
    print("ok")
```

### `arrays_hashing/group_anagrams.py`

```python
"""Group Anagrams  |  tier: core50, blind75, neetcode150  |  Arrays & Hashing

Group a list of strings so anagrams land in the same group.

Approach: key each word by its 26-letter count signature (tuple). Anagrams
share a signature. Sorting the word also works but is O(k log k) per word;
the count key is O(k).
Time: O(n * k)   Space: O(n * k)   (n words, k max length)
"""
from __future__ import annotations

from collections import defaultdict


def group_anagrams(strs: list[str]) -> list[list[str]]:
    """Return anagrams grouped together (group order not significant)."""
    groups: defaultdict[tuple[int, ...], list[str]] = defaultdict(list)
    for word in strs:
        count = [0] * 26
        for ch in word:
            count[ord(ch) - ord("a")] += 1
        groups[tuple(count)].append(word)
    return list(groups.values())


if __name__ == "__main__":
    out = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    normalized = sorted(sorted(g) for g in out)
    assert normalized == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]
    print("ok")
```

### `arrays_hashing/longest_consecutive.py`

```python
"""Longest Consecutive Sequence  |  tier: blind75, neetcode150  |  Arrays & Hashing

Return the length of the longest run of consecutive integers, in O(n). Order in
the input does not matter.

Approach: put all values in a set. Only start counting from a sequence START
(a value with no n-1 present). From each start, walk n+1, n+2, ... This makes
each value visited at most twice overall.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def longest_consecutive(nums: list[int]) -> int:
    """Return length of the longest consecutive integer sequence."""
    num_set = set(nums)
    best = 0
    for num in num_set:
        if num - 1 in num_set:
            continue                     # not a sequence start
        length = 1
        while num + length in num_set:
            length += 1
        best = max(best, length)
    return best


if __name__ == "__main__":
    assert longest_consecutive([100, 4, 200, 1, 3, 2]) == 4   # 1,2,3,4
    assert longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1]) == 9
    assert longest_consecutive([]) == 0
    print("ok")
```

### `arrays_hashing/product_except_self.py`

```python
"""Product of Array Except Self  |  tier: blind75, neetcode150  |  Arrays & Hashing

Return an array where output[i] is the product of all elements except nums[i].
No division allowed; must run in O(n).

Approach: two passes. First fills each slot with the prefix product (product of
everything to the left). Second multiplies in the suffix product (everything to
the right) using a running variable.
Time: O(n)   Space: O(1)  (output array not counted)
"""
from __future__ import annotations


def product_except_self(nums: list[int]) -> list[int]:
    """Return products of all other elements, without division."""
    length = len(nums)
    result = [1] * length

    prefix = 1
    for i in range(length):
        result[i] = prefix
        prefix *= nums[i]

    suffix = 1
    for i in range(length - 1, -1, -1):
        result[i] *= suffix
        suffix *= nums[i]

    return result


if __name__ == "__main__":
    assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]
    assert product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]
    print("ok")
```

### `arrays_hashing/top_k_frequent.py`

```python
"""Top K Frequent Elements  |  tier: blind75, neetcode150  |  Arrays & Hashing

Return the k most frequent elements.

Approach: bucket sort by frequency. Index buckets by count (0..n), then walk
from highest count down collecting k elements. Avoids a full sort / heap.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from collections import Counter


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    """Return the k most frequent values (any order)."""
    counts = Counter(nums)
    buckets: list[list[int]] = [[] for _ in range(len(nums) + 1)]
    for value, freq in counts.items():
        buckets[freq].append(value)

    result: list[int] = []
    for freq in range(len(buckets) - 1, 0, -1):
        for value in buckets[freq]:
            result.append(value)
            if len(result) == k:
                return result
    return result


if __name__ == "__main__":
    assert sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert top_k_frequent([1], 1) == [1]
    print("ok")
```

### `arrays_hashing/two_sum.py`

```python
"""Two Sum  |  tier: core50, blind75, neetcode150  |  Arrays & Hashing

Given an array and a target, return indices of the two numbers that add to
target. Exactly one solution; cannot reuse an element.

Approach: one pass with a hash map of value -> index. For each number, check
if its complement (target - num) was already seen.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def two_sum(nums: list[int], target: int) -> list[int]:
    """Return the two indices whose values sum to target."""
    seen: dict[int, int] = {}            # value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []                            # problem guarantees a solution


if __name__ == "__main__":
    assert two_sum([2, 7, 11, 15], 9) == [0, 1]
    assert two_sum([3, 2, 4], 6) == [1, 2]
    assert two_sum([3, 3], 6) == [0, 1]
    print("ok")
```

### `arrays_hashing/valid_anagram.py`

```python
"""Valid Anagram  |  tier: core50, blind75, neetcode150  |  Arrays & Hashing

Given strings word and candidate, return True if candidate is an anagram of word
(same letters, same counts).

Approach: compare character frequency maps. Equal length is a prerequisite;
then equal Counters means anagram.
Time: O(n)   Space: O(1)  (bounded alphabet)
"""
from __future__ import annotations

from collections import Counter


def is_anagram(word: str, candidate: str) -> bool:
    """Return True if candidate is an anagram of word."""
    if len(word) != len(candidate):
        return False
    return Counter(word) == Counter(candidate)


if __name__ == "__main__":
    assert is_anagram("anagram", "nagaram") is True
    assert is_anagram("rat", "car") is False
    assert is_anagram("", "") is True
    print("ok")
```

### `arrays_hashing/valid_sudoku.py`

```python
"""Valid Sudoku  |  tier: neetcode150  |  Arrays & Hashing

Determine if a 9x9 board is valid: no repeated digit within any row, column, or
3x3 box. Empty cells are '.' and are ignored.

Approach: one pass; track seen digits per row, per column, and per box. Box key
is (row // 3, col // 3). Any collision -> invalid.
Time: O(81) = O(1)   Space: O(1)
"""
from __future__ import annotations

from collections import defaultdict


def is_valid_sudoku(board: list[list[str]]) -> bool:
    """Return True if the current board configuration is valid."""
    rows: defaultdict[int, set[str]] = defaultdict(set)
    cols: defaultdict[int, set[str]] = defaultdict(set)
    boxes: defaultdict[tuple[int, int], set[str]] = defaultdict(set)

    for r in range(9):
        for c in range(9):
            val = board[r][c]
            if val == ".":
                continue
            box = (r // 3, c // 3)
            if val in rows[r] or val in cols[c] or val in boxes[box]:
                return False
            rows[r].add(val)
            cols[c].add(val)
            boxes[box].add(val)
    return True


if __name__ == "__main__":
    board = [
        ["5", "3", ".", ".", "7", ".", ".", ".", "."],
        ["6", ".", ".", "1", "9", "5", ".", ".", "."],
        [".", "9", "8", ".", ".", ".", ".", "6", "."],
        ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
        ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
        ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
        [".", "6", ".", ".", ".", ".", "2", "8", "."],
        [".", ".", ".", "4", "1", "9", ".", ".", "5"],
        [".", ".", ".", ".", "8", ".", ".", "7", "9"],
    ]
    assert is_valid_sudoku(board) is True
    board[0][0] = "8"          # collides with the 8 in column 0
    assert is_valid_sudoku(board) is False
    print("ok")
```


---

## Two Pointers

### `two_pointers/container_with_most_water.py`

```python
"""Container With Most Water  |  tier: core50, blind75, neetcode150  |  Two Pointers

Given heights, pick two lines forming a container holding the most water:
area = min(h[l], h[r]) * (r - l). Maximize it.

Approach: widest container first (both ends), then move the SHORTER wall inward.
Moving the taller wall can never help -- width shrinks and height is still
capped by the shorter wall.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_area(height: list[int]) -> int:
    """Return the maximum water a container can hold."""
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        width = right - left
        best = max(best, width * min(height[left], height[right]))
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return best


if __name__ == "__main__":
    assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert max_area([1, 1]) == 1
    print("ok")
```

### `two_pointers/three_sum.py`

```python
"""3Sum  |  tier: core50, blind75, neetcode150  |  Two Pointers

Return all unique triplets that sum to zero. No duplicate triplets.

Approach: sort, then fix each i and two-pointer scan the remainder for pairs
summing to -nums[i]. Skip duplicate anchors and duplicate pair values to keep
triplets unique. Early break once nums[i] > 0.
Time: O(n^2)   Space: O(1)  (excluding output / sort)
"""
from __future__ import annotations


def three_sum(nums: list[int]) -> list[list[int]]:
    """Return all unique zero-sum triplets."""
    nums.sort()
    result: list[list[int]] = []
    for i in range(len(nums)):
        if nums[i] > 0:
            break                        # sorted: no zero-sum past here
        if i > 0 and nums[i] == nums[i - 1]:
            continue                     # skip duplicate anchor
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                result.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1            # skip duplicate pair value
    return result


if __name__ == "__main__":
    assert three_sum([-1, 0, 1, 2, -1, -4]) == [[-1, -1, 2], [-1, 0, 1]]
    assert three_sum([0, 1, 1]) == []
    assert three_sum([0, 0, 0]) == [[0, 0, 0]]
    print("ok")
```

### `two_pointers/trapping_rain_water.py`

```python
"""Trapping Rain Water  |  tier: core50, neetcode150  |  Two Pointers

Given an elevation map, compute how much rain water it traps.

Approach: two pointers tracking left_max and right_max. Water over a bar is
min(left_max, right_max) - height[i]. Always advance the side with the smaller
max -- that side's max is the true bound there, so the trapped amount is fixed.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def trap(height: list[int]) -> int:
    """Return total trapped rain water."""
    if not height:
        return 0
    left, right = 0, len(height) - 1
    left_max, right_max = height[left], height[right]
    water = 0
    while left < right:
        if left_max < right_max:
            left += 1
            left_max = max(left_max, height[left])
            water += left_max - height[left]
        else:
            right -= 1
            right_max = max(right_max, height[right])
            water += right_max - height[right]
    return water


if __name__ == "__main__":
    assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6
    assert trap([4, 2, 0, 3, 2, 5]) == 9
    assert trap([]) == 0
    print("ok")
```

### `two_pointers/two_sum_ii_sorted.py`

```python
"""Two Sum II (Input Sorted)  |  tier: neetcode150  |  Two Pointers

Given a 1-indexed sorted array, return the 1-based indices of the two numbers
adding to target. O(1) extra space required.

Approach: two pointers from both ends. Sum too small -> move left up; too big ->
move right down. Sortedness guarantees this converges.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def two_sum_sorted(numbers: list[int], target: int) -> list[int]:
    """Return 1-based indices of the pair summing to target."""
    left, right = 0, len(numbers) - 1
    while left < right:
        total = numbers[left] + numbers[right]
        if total == target:
            return [left + 1, right + 1]
        if total < target:
            left += 1
        else:
            right -= 1
    return []


if __name__ == "__main__":
    assert two_sum_sorted([2, 7, 11, 15], 9) == [1, 2]
    assert two_sum_sorted([2, 3, 4], 6) == [1, 3]
    assert two_sum_sorted([-1, 0], -1) == [1, 2]
    print("ok")
```

### `two_pointers/valid_palindrome.py`

```python
"""Valid Palindrome  |  tier: core50, blind75, neetcode150  |  Two Pointers

Return True if the string reads the same forwards and backwards, considering
only alphanumeric characters and ignoring case.

Approach: two pointers from both ends move inward, skipping non-alphanumerics,
comparing lowercased chars. O(1) extra space (no cleaned copy).
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def is_palindrome(text: str) -> bool:
    """Return True if text is a palindrome over alphanumeric chars, case-insensitive."""
    left, right = 0, len(text) - 1
    while left < right:
        while left < right and not text[left].isalnum():
            left += 1
        while left < right and not text[right].isalnum():
            right -= 1
        if text[left].lower() != text[right].lower():
            return False
        left += 1
        right -= 1
    return True


if __name__ == "__main__":
    assert is_palindrome("A man, a plan, a canal: Panama") is True
    assert is_palindrome("race a car") is False
    assert is_palindrome(" ") is True
    print("ok")
```


---

## Sliding Window

### `sliding_window/best_time_buy_sell_stock.py`

```python
"""Best Time to Buy and Sell Stock  |  tier: core50, blind75, neetcode150  |  Sliding Window

Given daily prices, maximize profit from one buy then one later sell. If no
profit is possible, return 0.

Approach: track the minimum price seen so far (best buy day); at each day the
best profit is price - min_so_far. Keep the running maximum.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_profit(prices: list[int]) -> int:
    """Return the max profit from a single buy/sell, or 0."""
    min_price = float("inf")
    best = 0
    for price in prices:
        min_price = min(min_price, price)
        best = max(best, price - min_price)
    return best


if __name__ == "__main__":
    assert max_profit([7, 1, 5, 3, 6, 4]) == 5     # buy 1, sell 6
    assert max_profit([7, 6, 4, 3, 1]) == 0        # only losses
    assert max_profit([]) == 0
    print("ok")
```

### `sliding_window/longest_repeating_char_replacement.py`

```python
"""Longest Repeating Character Replacement  |  tier: core50, blind75, neetcode150  |  Sliding Window

You may replace at most k characters. Return the length of the longest substring
of a single repeated letter achievable after replacements.

Approach: sliding window tracking counts. A window is valid when
(window_len - count_of_most_frequent_char) <= k -- the non-majority chars are
the ones to replace. Grow right; shrink left when invalid.
Time: O(n)   Space: O(1)  (26 letters)
"""
from __future__ import annotations

from collections import defaultdict


def character_replacement(text: str, k: int) -> int:
    """Return longest single-char run achievable with <=k replacements."""
    counts: defaultdict[str, int] = defaultdict(int)
    left = 0
    max_freq = 0
    best = 0
    for right, ch in enumerate(text):
        counts[ch] += 1
        max_freq = max(max_freq, counts[ch])
        while (right - left + 1) - max_freq > k:
            counts[text[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    assert character_replacement("ABAB", 2) == 4
    assert character_replacement("AABABBA", 1) == 4
    assert character_replacement("", 0) == 0
    print("ok")
```

### `sliding_window/longest_substring_without_repeating.py`

```python
"""Longest Substring Without Repeating Characters  |  tier: core50, blind75, neetcode150  |  Sliding Window

Return the length of the longest substring with all distinct characters.

Approach: sliding window with a map of char -> last index. When a repeat falls
inside the window, jump the left edge past its previous position. Window always
holds distinct chars.
Time: O(n)   Space: O(min(n, alphabet))
"""
from __future__ import annotations


def length_of_longest_substring(text: str) -> int:
    """Return length of the longest substring without repeating characters."""
    last_seen: dict[str, int] = {}
    left = 0
    best = 0
    for right, ch in enumerate(text):
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1
        last_seen[ch] = right
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    assert length_of_longest_substring("abcabcbb") == 3   # "abc"
    assert length_of_longest_substring("bbbbb") == 1      # "b"
    assert length_of_longest_substring("pwwkew") == 3     # "wke"
    assert length_of_longest_substring("") == 0
    print("ok")
```

### `sliding_window/minimum_window_substring.py`

```python
"""Minimum Window Substring  |  tier: blind75, neetcode150  |  Sliding Window

Return the smallest substring of text containing every character of pattern (with
multiplicity). Empty string if none.

Approach: grow the right edge until the window covers pattern (track how many required
chars are satisfied via a 'have/need' counter). Then shrink from the left while
still valid, recording the smallest window.
Time: O(n)   Space: O(unique chars in t)
"""
from __future__ import annotations

from collections import Counter


def min_window(text: str, pattern: str) -> str:
    """Return the minimum window in text covering all chars of pattern."""
    if not pattern or not text:
        return ""
    need = Counter(pattern)
    required = len(need)
    have = 0
    window: dict[str, int] = {}
    best_len = float("inf")
    best = (0, 0)
    left = 0
    for right, ch in enumerate(text):
        window[ch] = window.get(ch, 0) + 1
        if ch in need and window[ch] == need[ch]:
            have += 1
        while have == required:
            if right - left + 1 < best_len:
                best_len = right - left + 1
                best = (left, right)
            window[text[left]] -= 1
            if text[left] in need and window[text[left]] < need[text[left]]:
                have -= 1
            left += 1
    start, end = best
    return text[start:end + 1] if best_len != float("inf") else ""


if __name__ == "__main__":
    assert min_window("ADOBECODEBANC", "ABC") == "BANC"
    assert min_window("a", "a") == "a"
    assert min_window("a", "aa") == ""
    print("ok")
```

### `sliding_window/permutation_in_string.py`

```python
"""Permutation in String  |  tier: neetcode150  |  Sliding Window

Return True if text contains any permutation of pattern as a substring.

Approach: fixed-size sliding window of len(pattern) over text, comparing character
counts. Slide by adding the entering char and removing the leaving char; match
when the window's counts equal pattern's counts.
Time: O(n)   Space: O(1)  (26 letters)
"""
from __future__ import annotations

from collections import Counter


def check_inclusion(pattern: str, text: str) -> bool:
    """Return True if some permutation of pattern is a substring of text."""
    if len(pattern) > len(text):
        return False
    need = Counter(pattern)
    window = Counter(text[:len(pattern)])
    if window == need:
        return True
    for i in range(len(pattern), len(text)):
        window[text[i]] += 1             # add entering char
        left = text[i - len(pattern)]
        window[left] -= 1                # remove leaving char
        if window[left] == 0:
            del window[left]
        if window == need:
            return True
    return False


if __name__ == "__main__":
    assert check_inclusion("ab", "eidbaooo") is True     # "ba"
    assert check_inclusion("ab", "eidboaoo") is False
    assert check_inclusion("a", "a") is True
    print("ok")
```

### `sliding_window/sliding_window_maximum.py`

```python
"""Sliding Window Maximum  |  tier: neetcode150  |  Sliding Window

Return the maximum of each contiguous window of size k as it slides across nums.

Approach: monotonic decreasing deque of indices. Front always holds the current
window's max. Pop smaller values from the back before appending (they can never
be a future max), and drop the front when it slides out of the window.
Time: O(n)   Space: O(k)
"""
from __future__ import annotations

from collections import deque


def max_sliding_window(nums: list[int], k: int) -> list[int]:
    """Return the max of every size-k window."""
    dq: deque[int] = deque()             # indices, values decreasing
    result: list[int] = []
    for i, num in enumerate(nums):
        while dq and nums[dq[-1]] < num:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:               # front slid out of window
            dq.popleft()
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result


if __name__ == "__main__":
    assert max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert max_sliding_window([1], 1) == [1]
    print("ok")
```


---

## Stack

### `stack/car_fleet.py`

```python
"""Car Fleet  |  tier: neetcode150  |  Stack

Cars head to a target at given positions and speeds. A faster car catching a
slower one forms a fleet moving at the slower speed (no passing). Return the
number of fleets that arrive.

Approach: sort cars by position descending (closest to target first). Compute
each car's arrival time = (target - pos) / speed. Scan: a car forms a new fleet
only if it arrives strictly later than the fleet ahead; otherwise it merges.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations


def car_fleet(target: int, position: list[int], speed: list[int]) -> int:
    """Return the number of car fleets that reach the target."""
    cars = sorted(zip(position, speed), reverse=True)
    fleets = 0
    lead_time = 0.0
    for pos, spd in cars:
        time = (target - pos) / spd
        if time > lead_time:             # cannot catch the fleet ahead
            fleets += 1
            lead_time = time
    return fleets


if __name__ == "__main__":
    assert car_fleet(12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3]) == 3
    assert car_fleet(10, [3], [3]) == 1
    assert car_fleet(100, [0, 2, 4], [4, 2, 1]) == 1
    print("ok")
```

### `stack/daily_temperatures.py`

```python
"""Daily Temperatures  |  tier: core50, neetcode150  |  Stack

For each day, how many days until a warmer temperature? 0 if none.

Approach: monotonic decreasing stack of indices waiting for a warmer day. When a
warmer temp arrives, pop every colder index and record the day gap.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def daily_temperatures(temperatures: list[int]) -> list[int]:
    """Return days-until-warmer for each day."""
    result = [0] * len(temperatures)
    stack: list[int] = []                # indices of unresolved days
    for i, temp in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < temp:
            prev = stack.pop()
            result[prev] = i - prev
        stack.append(i)
    return result


if __name__ == "__main__":
    assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert daily_temperatures([30, 40, 50, 60]) == [1, 1, 1, 0]
    assert daily_temperatures([30, 20, 10]) == [0, 0, 0]
    print("ok")
```

### `stack/eval_reverse_polish.py`

```python
"""Evaluate Reverse Polish Notation  |  tier: core50, neetcode150  |  Stack

Evaluate an arithmetic expression in postfix (RPN) form. Operators: + - * /.
Division truncates toward zero.

Approach: scan tokens; push numbers; on an operator pop the two operands, apply,
push the result. Final stack value is the answer.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def eval_rpn(tokens: list[str]) -> int:
    """Evaluate a reverse Polish notation expression."""
    ops = {"+", "-", "*", "/"}
    stack: list[int] = []
    for tok in tokens:
        if tok in ops:
            right = stack.pop()
            left = stack.pop()
            if tok == "+":
                stack.append(left + right)
            elif tok == "-":
                stack.append(left - right)
            elif tok == "*":
                stack.append(left * right)
            else:
                stack.append(int(left / right))  # truncate toward zero
        else:
            stack.append(int(tok))
    return stack[0]


if __name__ == "__main__":
    assert eval_rpn(["2", "1", "+", "3", "*"]) == 9        # (2+1)*3
    assert eval_rpn(["4", "13", "5", "/", "+"]) == 6       # 4 + 13//5
    assert eval_rpn(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]) == 22
    print("ok")
```

### `stack/generate_parentheses.py`

```python
"""Generate Parentheses  |  tier: neetcode150  |  Stack

Generate all combinations of n well-formed pairs of parentheses.

Approach: backtracking with two counters. Add '(' while opens < n; add ')' only
while closes < opens (keeps every prefix valid). Record when length == 2n.
Time: O(4^n / sqrt(n))  (Catalan number)   Space: O(n) recursion depth
"""
from __future__ import annotations


def generate_parenthesis(n: int) -> list[str]:
    """Return all valid combinations of n pairs of parentheses."""
    result: list[str] = []
    stack: list[str] = []

    def backtrack(opens: int, closes: int) -> None:
        if len(stack) == 2 * n:
            result.append("".join(stack))
            return
        if opens < n:
            stack.append("(")
            backtrack(opens + 1, closes)
            stack.pop()
        if closes < opens:
            stack.append(")")
            backtrack(opens, closes + 1)
            stack.pop()

    backtrack(0, 0)
    return result


if __name__ == "__main__":
    assert sorted(generate_parenthesis(3)) == sorted(
        ["((()))", "(()())", "(())()", "()(())", "()()()"]
    )
    assert generate_parenthesis(1) == ["()"]
    print("ok")
```

### `stack/largest_rectangle_histogram.py`

```python
"""Largest Rectangle in Histogram  |  tier: neetcode150  |  Stack

Given bar heights of width 1, return the area of the largest axis-aligned
rectangle that fits inside the histogram.

Approach: monotonic increasing stack of (start_index, height). When a shorter
bar appears, pop taller bars and compute their area extending from their start
to the current index. Popped bars can extend the new bar's start leftward.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def largest_rectangle_area(heights: list[int]) -> int:
    """Return the largest rectangle area in the histogram."""
    stack: list[tuple[int, int]] = []    # (start index, height)
    best = 0
    for i, current_height in enumerate(heights):
        start = i
        while stack and stack[-1][1] > current_height:
            idx, height = stack.pop()
            best = max(best, height * (i - idx))
            start = idx                  # this bar can extend back to idx
        stack.append((start, current_height))
    n = len(heights)
    for idx, height in stack:            # bars running to the end
        best = max(best, height * (n - idx))
    return best


if __name__ == "__main__":
    assert largest_rectangle_area([2, 1, 5, 6, 2, 3]) == 10
    assert largest_rectangle_area([2, 4]) == 4
    assert largest_rectangle_area([1]) == 1
    print("ok")
```

### `stack/min_stack.py`

```python
"""Min Stack  |  tier: blind75, neetcode150  |  Stack

Design a stack supporting push, pop, top, and getMin all in O(1).

Approach: alongside the main stack, keep a 'min stack' whose top is always the
minimum of the current contents. On push, store min(new, current_min).
Time: O(1) per op   Space: O(n)
"""
from __future__ import annotations


class MinStack:
    """Stack with O(1) minimum retrieval."""

    def __init__(self) -> None:
        self._stack: list[int] = []
        self._mins: list[int] = []

    def push(self, val: int) -> None:
        """Push val and update the running minimum."""
        self._stack.append(val)
        self._mins.append(val if not self._mins else min(val, self._mins[-1]))

    def pop(self) -> None:
        """Remove the top element."""
        self._stack.pop()
        self._mins.pop()

    def top(self) -> int:
        """Return the top element."""
        return self._stack[-1]

    def get_min(self) -> int:
        """Return the current minimum in O(1)."""
        return self._mins[-1]


if __name__ == "__main__":
    st = MinStack()
    st.push(-2); st.push(0); st.push(-3)
    assert st.get_min() == -3
    st.pop()
    assert st.top() == 0
    assert st.get_min() == -2
    print("ok")
```

### `stack/valid_parentheses.py`

```python
"""Valid Parentheses  |  tier: core50, blind75, neetcode150  |  Stack

Given a string of (), [], {}, return True if every bracket is closed by the
matching type in the correct order.

Approach: push opens onto a stack; on a close, the stack top must be the
matching open. Valid iff every close matches and the stack ends empty.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def is_valid(brackets: str) -> bool:
    """Return True if brackets are balanced and correctly nested."""
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for ch in brackets:
        if ch in pairs:                  # closing bracket
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:                            # opening bracket
            stack.append(ch)
    return not stack


if __name__ == "__main__":
    assert is_valid("()[]{}") is True
    assert is_valid("(]") is False
    assert is_valid("([{}])") is True
    assert is_valid("(") is False
    print("ok")
```


---

## Binary Search

### `binary_search/binary_search.py`

```python
"""Binary Search  |  tier: core50, neetcode150  |  Binary Search

Return the index of target in a sorted array, or -1 if absent.

Approach: maintain [left, right]; compare the midpoint to target and discard
half each step. Use left + (right - left) // 2 to avoid overflow in other
languages.
Time: O(log n)   Space: O(1)
"""
from __future__ import annotations


def search(nums: list[int], target: int) -> int:
    """Return index of target, or -1."""
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


if __name__ == "__main__":
    assert search([-1, 0, 3, 5, 9, 12], 9) == 4
    assert search([-1, 0, 3, 5, 9, 12], 2) == -1
    assert search([], 1) == -1
    print("ok")
```

### `binary_search/find_min_rotated.py`

```python
"""Find Minimum in Rotated Sorted Array  |  tier: core50, blind75, neetcode150  |  Binary Search

A sorted array of distinct values was rotated. Return the minimum element in
O(log n).

Approach: binary search. If nums[mid] > nums[right], the minimum lies to the
right of mid; otherwise it is at mid or to its left. Converge to the pivot.
Time: O(log n)   Space: O(1)
"""
from __future__ import annotations


def find_min(nums: list[int]) -> int:
    """Return the minimum of the rotated sorted array."""
    left, right = 0, len(nums) - 1
    while left < right:
        mid = left + (right - left) // 2
        if nums[mid] > nums[right]:
            left = mid + 1               # min is right of mid
        else:
            right = mid                  # min is mid or left
    return nums[left]


if __name__ == "__main__":
    assert find_min([3, 4, 5, 1, 2]) == 1
    assert find_min([4, 5, 6, 7, 0, 1, 2]) == 0
    assert find_min([11, 13, 15, 17]) == 11      # not rotated
    print("ok")
```

### `binary_search/koko_eating_bananas.py`

```python
"""Koko Eating Bananas  |  tier: core50, neetcode150  |  Binary Search

Koko eats at speed k bananas/hour, one pile per hour (rounding up). Return the
minimum k that finishes all piles within h hours.

Approach: binary search on the ANSWER (speed) in [1, max(piles)]. hours(k) is
monotonic decreasing in k, so search for the smallest feasible k.
Time: O(n log(max_pile))   Space: O(1)
"""
from __future__ import annotations

import math


def min_eating_speed(piles: list[int], h: int) -> int:
    """Return the minimum eating speed to finish within h hours."""
    def hours_needed(speed: int) -> int:
        return sum(math.ceil(pile / speed) for pile in piles)

    left, right = 1, max(piles)
    while left < right:
        mid = left + (right - left) // 2
        if hours_needed(mid) <= h:
            right = mid                  # feasible -> try slower
        else:
            left = mid + 1
    return left


if __name__ == "__main__":
    assert min_eating_speed([3, 6, 7, 11], 8) == 4
    assert min_eating_speed([30, 11, 23, 4, 20], 5) == 30
    assert min_eating_speed([30, 11, 23, 4, 20], 6) == 23
    print("ok")
```

### `binary_search/median_two_sorted_arrays.py`

```python
"""Median of Two Sorted Arrays  |  tier: neetcode150  |  Binary Search

Return the median of two sorted arrays in O(log(min(m, n))).

Approach: binary search a partition of the SMALLER array. Choose cuts in both
arrays so the left side holds exactly half the elements and every left value <=
every right value (left_smaller <= right_larger and left_larger <=
right_smaller). The median comes from the boundary values.
Time: O(log(min(m, n)))   Space: O(1)
"""
from __future__ import annotations


def find_median_sorted_arrays(nums1: list[int], nums2: list[int]) -> float:
    """Return the median of the two sorted arrays combined."""
    smaller, larger = nums1, nums2
    if len(smaller) > len(larger):
        smaller, larger = larger, smaller
    total = len(smaller) + len(larger)
    half = total // 2
    left, right = 0, len(smaller)
    while left <= right:
        i = (left + right) // 2          # cut in smaller
        j = half - i                     # cut in larger
        left_smaller = smaller[i - 1] if i > 0 else float("-inf")
        right_smaller = smaller[i] if i < len(smaller) else float("inf")
        left_larger = larger[j - 1] if j > 0 else float("-inf")
        right_larger = larger[j] if j < len(larger) else float("inf")
        if left_smaller <= right_larger and left_larger <= right_smaller:
            if total % 2:
                return float(min(right_smaller, right_larger))
            return (max(left_smaller, left_larger) + min(right_smaller, right_larger)) / 2
        if left_smaller > right_larger:
            right = i - 1
        else:
            left = i + 1
    raise ValueError("inputs not sorted")


if __name__ == "__main__":
    assert find_median_sorted_arrays([1, 3], [2]) == 2.0
    assert find_median_sorted_arrays([1, 2], [3, 4]) == 2.5
    assert find_median_sorted_arrays([], [1]) == 1.0
    print("ok")
```

### `binary_search/search_2d_matrix.py`

```python
"""Search a 2D Matrix  |  tier: neetcode150  |  Binary Search

Each row is sorted, and the first value of each row exceeds the last value of
the previous row. Return True if target is present.

Approach: treat the m x n matrix as one sorted array of length m*n and binary
search it, mapping a flat index to (index // n, index % n).
Time: O(log(m*n))   Space: O(1)
"""
from __future__ import annotations


def search_matrix(matrix: list[list[int]], target: int) -> bool:
    """Return True if target is in the row/col-sorted matrix."""
    if not matrix or not matrix[0]:
        return False
    rows, cols = len(matrix), len(matrix[0])
    left, right = 0, rows * cols - 1
    while left <= right:
        mid = left + (right - left) // 2
        val = matrix[mid // cols][mid % cols]
        if val == target:
            return True
        if val < target:
            left = mid + 1
        else:
            right = mid - 1
    return False


if __name__ == "__main__":
    mat = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
    assert search_matrix(mat, 3) is True
    assert search_matrix(mat, 13) is False
    print("ok")
```

### `binary_search/search_rotated.py`

```python
"""Search in Rotated Sorted Array  |  tier: core50, blind75, neetcode150  |  Binary Search

A sorted array of distinct values was rotated. Return the index of target, or -1,
in O(log n).

Approach: binary search. At each step one half [left, mid] or [mid, right] is
sorted. Decide which half is sorted, then check whether target lies within that
sorted range to pick the side to keep.
Time: O(log n)   Space: O(1)
"""
from __future__ import annotations


def search(nums: list[int], target: int) -> int:
    """Return index of target in the rotated array, or -1."""
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            return mid
        if nums[left] <= nums[mid]:      # left half sorted
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:                            # right half sorted
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1


if __name__ == "__main__":
    assert search([4, 5, 6, 7, 0, 1, 2], 0) == 4
    assert search([4, 5, 6, 7, 0, 1, 2], 3) == -1
    assert search([1], 1) == 0
    print("ok")
```

### `binary_search/time_based_kv_store.py`

```python
"""Time Based Key-Value Store  |  tier: neetcode150  |  Binary Search

Design a store: set(key, value, timestamp), and get(key, timestamp) returning the
value with the largest stored timestamp <= the query (or "" if none). Timestamps
for a key are strictly increasing.

Approach: per key, append (timestamp, value) -> the list is sorted by timestamp.
get binary-searches for the rightmost timestamp <= query.
Time: set O(1), get O(log n)   Space: O(n)
"""
from __future__ import annotations

from collections import defaultdict


class TimeMap:
    """Key -> time-ordered (timestamp, value) history."""

    def __init__(self) -> None:
        self._store: defaultdict[str, list[tuple[int, str]]] = defaultdict(list)

    def set(self, key: str, value: str, timestamp: int) -> None:
        """Append a value with its timestamp (timestamps increase per key)."""
        self._store[key].append((timestamp, value))

    def get(self, key: str, timestamp: int) -> str:
        """Return the value at the greatest timestamp <= the query."""
        history = self._store[key]
        left, right = 0, len(history) - 1
        result = ""
        while left <= right:
            mid = left + (right - left) // 2
            if history[mid][0] <= timestamp:
                result = history[mid][1]
                left = mid + 1           # search for a later valid time
            else:
                right = mid - 1
        return result


if __name__ == "__main__":
    tm = TimeMap()
    tm.set("foo", "bar", 1)
    assert tm.get("foo", 1) == "bar"
    assert tm.get("foo", 3) == "bar"
    tm.set("foo", "bar2", 4)
    assert tm.get("foo", 4) == "bar2"
    assert tm.get("foo", 5) == "bar2"
    assert tm.get("foo", 0) == ""
    print("ok")
```


---

## Linked List

### `linked_list/add_two_numbers.py`

```python
"""Add Two Numbers  |  tier: neetcode150  |  Linked List

Two numbers stored as linked lists of digits in reverse order. Return their sum
as a linked list, also reverse order.

Approach: walk both lists in lockstep adding digit + carry, emitting digit % 10
and carrying digit // 10. Continue while either list or the carry remains.
Time: O(max(n, m))   Space: O(max(n, m))
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def add_two_numbers(
    list1: Optional[ListNode], list2: Optional[ListNode]
) -> Optional[ListNode]:
    """Sum two reverse-order digit lists, returning a reverse-order list."""
    dummy = ListNode()
    tail = dummy
    carry = 0
    while list1 or list2 or carry:
        total = carry
        if list1:
            total += list1.val
            list1 = list1.next
        if list2:
            total += list2.val
            list2 = list2.next
        carry, digit = divmod(total, 10)
        tail.next = ListNode(digit)
        tail = tail.next
    return dummy.next


def _build(values: list[int]) -> Optional[ListNode]:
    head: Optional[ListNode] = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def _to_list(head: Optional[ListNode]) -> list[int]:
    out: list[int] = []
    while head:
        out.append(head.val)
        head = head.next
    return out


if __name__ == "__main__":
    # 342 + 465 = 807
    assert _to_list(add_two_numbers(_build([2, 4, 3]), _build([5, 6, 4]))) == [7, 0, 8]
    assert _to_list(add_two_numbers(_build([9, 9]), _build([1]))) == [0, 0, 1]
    print("ok")
```

### `linked_list/copy_list_random_pointer.py`

```python
"""Copy List with Random Pointer  |  tier: neetcode150  |  Linked List

Deep-copy a linked list where each node also has a random pointer to any node or
None.

Approach: hash map from original node -> its clone. First pass creates all
clones; second pass wires next and random using the map.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from typing import Optional


class Node:
    """List node with next and random pointers."""

    def __init__(self, val: int) -> None:
        self.val = val
        self.next: Optional[Node] = None
        self.random: Optional[Node] = None


def copy_random_list(head: Optional[Node]) -> Optional[Node]:
    """Return a deep copy of the list including random pointers."""
    clones: dict[Optional[Node], Optional[Node]] = {None: None}
    curr = head
    while curr:                          # pass 1: clone nodes
        clones[curr] = Node(curr.val)
        curr = curr.next
    curr = head
    while curr:                          # pass 2: wire pointers
        clones[curr].next = clones[curr.next]      # type: ignore[union-attr]
        clones[curr].random = clones[curr.random]  # type: ignore[union-attr]
        curr = curr.next
    return clones[head]


if __name__ == "__main__":
    node1, node2, node3 = Node(7), Node(13), Node(11)
    node1.next, node2.next = node2, node3
    node1.random, node2.random, node3.random = None, node1, node1
    copy = copy_random_list(node1)
    assert copy is not node1 and copy.val == 7        # type: ignore[union-attr]
    assert copy.next.val == 13                        # type: ignore[union-attr]
    assert copy.next.random is copy                   # type: ignore[union-attr]
    print("ok")
```

### `linked_list/find_duplicate_number.py`

```python
"""Find the Duplicate Number  |  tier: neetcode150  |  Linked List

An array of n+1 integers in [1, n] has exactly one repeated value. Find it
without modifying the array and in O(1) space.

Approach: treat indices as a linked list where i -> nums[i]. A duplicate creates
a cycle; Floyd's algorithm finds the cycle entrance, which is the duplicate.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def find_duplicate(nums: list[int]) -> int:
    """Return the single duplicated value using cycle detection."""
    slow, fast = nums[0], nums[0]
    while True:                          # phase 1: find a meeting point
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    slow = nums[0]                       # phase 2: find cycle entrance
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow


if __name__ == "__main__":
    assert find_duplicate([1, 3, 4, 2, 2]) == 2
    assert find_duplicate([3, 1, 3, 4, 2]) == 3
    assert find_duplicate([2, 2, 2, 2, 2]) == 2
    print("ok")
```

### `linked_list/linked_list_cycle.py`

```python
"""Linked List Cycle  |  tier: core50, blind75, neetcode150  |  Linked List

Return True if the linked list contains a cycle.

Approach: Floyd's tortoise and hare. A slow pointer (1 step) and fast pointer
(2 steps) meet inside any cycle; if fast reaches the end, there is no cycle.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def has_cycle(head: Optional[ListNode]) -> bool:
    """Return True if the list has a cycle (Floyd's algorithm)."""
    slow, fast = head, head
    while fast and fast.next:
        slow = slow.next                 # type: ignore[union-attr]
        fast = fast.next.next
        if slow is fast:
            return True
    return False


if __name__ == "__main__":
    node1, node2, node3 = ListNode(3), ListNode(2), ListNode(0)
    node1.next, node2.next, node3.next = node2, node3, node2  # cycle: node3 -> node2
    assert has_cycle(node1) is True
    head, tail = ListNode(1), ListNode(2)
    head.next = tail
    assert has_cycle(head) is False
    print("ok")
```

### `linked_list/lru_cache.py`

```python
"""LRU Cache  |  tier: core50, blind75, neetcode150  |  Linked List

Design a cache with O(1) get and put that evicts the least-recently-used key
when capacity is exceeded.

Approach: an OrderedDict keeps insertion/use order. On access, move the key to
the most-recent end; on overflow, pop the least-recent (front). (A manual
hashmap + doubly linked list achieves the same; OrderedDict encapsulates it.)
Time: O(1) per op   Space: O(capacity)
"""
from __future__ import annotations

from collections import OrderedDict


class LRUCache:
    """Fixed-capacity least-recently-used cache."""

    def __init__(self, capacity: int) -> None:
        self._cap = capacity
        self._data: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        """Return the value and mark key most-recently-used, or -1 if absent."""
        if key not in self._data:
            return -1
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: int, value: int) -> None:
        """Insert/update, evicting the LRU entry if over capacity."""
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self._cap:
            self._data.popitem(last=False)   # evict least recent


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1          # 1 now most recent
    cache.put(3, 3)                  # evicts 2
    assert cache.get(2) == -1
    cache.put(4, 4)                  # evicts 1
    assert cache.get(1) == -1
    assert cache.get(3) == 3
    assert cache.get(4) == 4
    print("ok")
```

### `linked_list/merge_k_sorted_lists.py`

```python
"""Merge K Sorted Lists  |  tier: blind75, neetcode150  |  Linked List

Merge k sorted linked lists into one sorted list.

Approach: iteratively merge lists in pairs (divide and conquer). Each round
halves the number of lists, so each node is touched O(log k) times.
Time: O(n log k)   Space: O(1)  (in-place merges)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def _merge_two(
    list1: Optional[ListNode], list2: Optional[ListNode]
) -> Optional[ListNode]:
    dummy = ListNode()
    tail = dummy
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next, list1 = list1, list1.next
        else:
            tail.next, list2 = list2, list2.next
        tail = tail.next
    tail.next = list1 or list2
    return dummy.next


def merge_k_lists(lists: list[Optional[ListNode]]) -> Optional[ListNode]:
    """Merge k sorted lists via pairwise divide-and-conquer."""
    if not lists:
        return None
    while len(lists) > 1:
        merged: list[Optional[ListNode]] = []
        for i in range(0, len(lists), 2):
            list1 = lists[i]
            list2 = lists[i + 1] if i + 1 < len(lists) else None
            merged.append(_merge_two(list1, list2))
        lists = merged
    return lists[0]


def _build(values: list[int]) -> Optional[ListNode]:
    head: Optional[ListNode] = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def _to_list(head: Optional[ListNode]) -> list[int]:
    out: list[int] = []
    while head:
        out.append(head.val)
        head = head.next
    return out


if __name__ == "__main__":
    out = merge_k_lists([_build([1, 4, 5]), _build([1, 3, 4]), _build([2, 6])])
    assert _to_list(out) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert merge_k_lists([]) is None
    assert _to_list(merge_k_lists([None, _build([1])])) == [1]
    print("ok")
```

### `linked_list/merge_two_sorted_lists.py`

```python
"""Merge Two Sorted Lists  |  tier: core50, blind75, neetcode150  |  Linked List

Merge two sorted linked lists into one sorted list and return its head.

Approach: dummy head + tail pointer. Repeatedly attach the smaller of the two
front nodes, advancing that list. Append the remaining tail at the end.
Time: O(n + m)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def merge_two_lists(
    list1: Optional[ListNode], list2: Optional[ListNode]
) -> Optional[ListNode]:
    """Merge two sorted lists into one sorted list."""
    dummy = ListNode()
    tail = dummy
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next, list1 = list1, list1.next
        else:
            tail.next, list2 = list2, list2.next
        tail = tail.next
    tail.next = list1 or list2
    return dummy.next


def _build(values: list[int]) -> Optional[ListNode]:
    head: Optional[ListNode] = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def _to_list(head: Optional[ListNode]) -> list[int]:
    out: list[int] = []
    while head:
        out.append(head.val)
        head = head.next
    return out


if __name__ == "__main__":
    merged = merge_two_lists(_build([1, 2, 4]), _build([1, 3, 4]))
    assert _to_list(merged) == [1, 1, 2, 3, 4, 4]
    assert _to_list(merge_two_lists(None, _build([0]))) == [0]
    print("ok")
```

### `linked_list/remove_nth_from_end.py`

```python
"""Remove Nth Node From End of List  |  tier: core50, blind75, neetcode150  |  Linked List

Remove the n-th node from the end in one pass and return the head.

Approach: two pointers off a dummy node. Advance 'fast' n+1 steps ahead, then
move both until fast falls off the end -- 'slow' now sits just before the target.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def remove_nth_from_end(head: Optional[ListNode], n: int) -> Optional[ListNode]:
    """Remove the n-th node from the end and return the new head."""
    dummy = ListNode(0, head)
    fast: Optional[ListNode] = dummy
    slow: Optional[ListNode] = dummy
    for _ in range(n + 1):
        fast = fast.next                 # type: ignore[union-attr]
    while fast:
        fast = fast.next
        slow = slow.next                 # type: ignore[union-attr]
    slow.next = slow.next.next           # type: ignore[union-attr]
    return dummy.next


def _build(values: list[int]) -> Optional[ListNode]:
    head: Optional[ListNode] = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def _to_list(head: Optional[ListNode]) -> list[int]:
    out: list[int] = []
    while head:
        out.append(head.val)
        head = head.next
    return out


if __name__ == "__main__":
    assert _to_list(remove_nth_from_end(_build([1, 2, 3, 4, 5]), 2)) == [1, 2, 3, 5]
    assert _to_list(remove_nth_from_end(_build([1]), 1)) == []
    assert _to_list(remove_nth_from_end(_build([1, 2]), 1)) == [1]
    print("ok")
```

### `linked_list/reorder_list.py`

```python
"""Reorder List  |  tier: blind75, neetcode150  |  Linked List

Reorder L0->L1->...->Ln to L0->Ln->L1->Ln-1->... in place (values not moved,
pointers rewired).

Approach: (1) find the middle with slow/fast pointers; (2) reverse the second
half; (3) merge the two halves alternately.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def reorder_list(head: Optional[ListNode]) -> None:
    """Reorder the list in place."""
    if not head or not head.next:
        return
    slow, fast = head, head
    while fast.next and fast.next.next:      # slow -> middle
        slow = slow.next
        fast = fast.next.next

    second: Optional[ListNode] = slow.next   # reverse second half
    slow.next = None
    prev: Optional[ListNode] = None
    while second:
        nxt = second.next
        second.next = prev
        prev = second
        second = nxt

    first: Optional[ListNode] = head         # merge alternately
    second = prev
    while second:
        first.next, first = second, first.next
        second.next, second = first, second.next


def _build(values: list[int]) -> Optional[ListNode]:
    head: Optional[ListNode] = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def _to_list(head: Optional[ListNode]) -> list[int]:
    out: list[int] = []
    while head:
        out.append(head.val)
        head = head.next
    return out


if __name__ == "__main__":
    even_list = _build([1, 2, 3, 4])
    reorder_list(even_list)
    assert _to_list(even_list) == [1, 4, 2, 3]
    odd_list = _build([1, 2, 3, 4, 5])
    reorder_list(odd_list)
    assert _to_list(odd_list) == [1, 5, 2, 4, 3]
    print("ok")
```

### `linked_list/reverse_linked_list.py`

```python
"""Reverse Linked List  |  tier: core50, blind75, neetcode150  |  Linked List

Reverse a singly linked list and return the new head.

Approach: iterate, re-pointing each node's next to the previous node. Three
variables: prev, curr, and the saved next.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def reverse_list(head: Optional[ListNode]) -> Optional[ListNode]:
    """Return the head of the reversed list."""
    prev: Optional[ListNode] = None
    curr = head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev


def _build(values: list[int]) -> Optional[ListNode]:
    head: Optional[ListNode] = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def _to_list(head: Optional[ListNode]) -> list[int]:
    out: list[int] = []
    while head:
        out.append(head.val)
        head = head.next
    return out


if __name__ == "__main__":
    assert _to_list(reverse_list(_build([1, 2, 3, 4, 5]))) == [5, 4, 3, 2, 1]
    assert _to_list(reverse_list(_build([]))) == []
    print("ok")
```

### `linked_list/reverse_nodes_k_group.py`

```python
"""Reverse Nodes in K-Group  |  tier: neetcode150  |  Linked List

Reverse the list in groups of k nodes. A trailing group smaller than k is left
as-is.

Approach: for each group, first check that k nodes remain; if so, reverse those
k nodes and connect the reversed segment to the previous and next groups via a
dummy/group-prev pointer.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def reverse_k_group(head: Optional[ListNode], k: int) -> Optional[ListNode]:
    """Reverse every consecutive group of k nodes."""
    dummy = ListNode(0, head)
    group_prev = dummy

    while True:
        kth = group_prev                 # find the k-th node from group_prev
        for _ in range(k):
            kth = kth.next               # type: ignore[assignment]
            if not kth:
                return dummy.next
        group_next = kth.next

        prev, curr = group_next, group_prev.next     # reverse the group
        while curr is not group_next:
            nxt = curr.next              # type: ignore[union-attr]
            curr.next = prev             # type: ignore[union-attr]
            prev = curr
            curr = nxt

        new_group_prev = group_prev.next
        group_prev.next = kth
        group_prev = new_group_prev      # type: ignore[assignment]


def _build(values: list[int]) -> Optional[ListNode]:
    head: Optional[ListNode] = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def _to_list(head: Optional[ListNode]) -> list[int]:
    out: list[int] = []
    while head:
        out.append(head.val)
        head = head.next
    return out


if __name__ == "__main__":
    assert _to_list(reverse_k_group(_build([1, 2, 3, 4, 5]), 2)) == [2, 1, 4, 3, 5]
    assert _to_list(reverse_k_group(_build([1, 2, 3, 4, 5]), 3)) == [3, 2, 1, 4, 5]
    assert _to_list(reverse_k_group(_build([1, 2, 3, 4, 5]), 1)) == [1, 2, 3, 4, 5]
    print("ok")
```


---

## Trees

### `trees/balanced_binary_tree.py`

```python
"""Balanced Binary Tree  |  tier: neetcode150  |  Trees

Return True if the tree is height-balanced: every node's two subtrees differ in
height by at most 1.

Approach: DFS returning height, but propagate -1 as a sentinel once any subtree
is found unbalanced -- short-circuits the whole tree in one pass.
Time: O(n)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def is_balanced(root: Optional[TreeNode]) -> bool:
    """Return True if the tree is height-balanced."""
    def height(node: Optional[TreeNode]) -> int:
        if node is None:
            return 0
        left = height(node.left)
        if left == -1:
            return -1
        right = height(node.right)
        if right == -1 or abs(left - right) > 1:
            return -1
        return 1 + max(left, right)

    return height(root) != -1


if __name__ == "__main__":
    balanced = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
    assert is_balanced(balanced) is True
    small = TreeNode(1, TreeNode(2, TreeNode(3)))
    assert is_balanced(small) is False               # root: left height 2, right 0
    leaf_pair = TreeNode(1, TreeNode(2), TreeNode(3))
    assert is_balanced(leaf_pair) is True
    assert is_balanced(None) is True
    print("ok")
```

### `trees/binary_tree_max_path_sum.py`

```python
"""Binary Tree Maximum Path Sum  |  tier: blind75, neetcode150  |  Trees

Return the maximum sum of any path. A path is a sequence of connected nodes; it
need not pass through the root and cannot reuse a node.

Approach: DFS returning the best DOWNWARD gain from a node (value + max(0, best
child)). At each node the best path THROUGH it is value + left_gain + right_gain;
track the global max. Negative gains are clamped to 0.
Time: O(n)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def max_path_sum(root: Optional[TreeNode]) -> int:
    """Return the maximum path sum in the tree."""
    best = float("-inf")

    def gain(node: Optional[TreeNode]) -> int:
        nonlocal best
        if node is None:
            return 0
        left = max(gain(node.left), 0)
        right = max(gain(node.right), 0)
        best = max(best, node.val + left + right)    # path through node
        return node.val + max(left, right)           # best single branch

    gain(root)
    return int(best)


if __name__ == "__main__":
    assert max_path_sum(TreeNode(1, TreeNode(2), TreeNode(3))) == 6
    # -10 with children 9 and (15,7): best path 15-20-7 = 42
    root = TreeNode(-10, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
    assert max_path_sum(root) == 42
    assert max_path_sum(TreeNode(-3)) == -3
    print("ok")
```

### `trees/construct_from_preorder_inorder.py`

```python
"""Construct Binary Tree from Preorder and Inorder  |  tier: blind75, neetcode150  |  Trees

Rebuild a binary tree from its preorder and inorder traversals (unique values).

Approach: preorder[0] is the root. Its position in inorder splits left/right
subtrees by size. Recurse, consuming preorder left to right via an index. An
index map of value -> inorder position avoids repeated scans.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def build_tree(preorder: list[int], inorder: list[int]) -> Optional[TreeNode]:
    """Reconstruct the tree from preorder + inorder traversals."""
    index = {val: i for i, val in enumerate(inorder)}
    pre_idx = 0

    def build(left: int, right: int) -> Optional[TreeNode]:
        nonlocal pre_idx
        if left > right:
            return None
        root_val = preorder[pre_idx]
        pre_idx += 1
        node = TreeNode(root_val)
        mid = index[root_val]
        node.left = build(left, mid - 1)
        node.right = build(mid + 1, right)
        return node

    return build(0, len(inorder) - 1)


def _preorder(node: Optional[TreeNode]) -> list[int]:
    if node is None:
        return []
    return [node.val] + _preorder(node.left) + _preorder(node.right)


if __name__ == "__main__":
    pre = [3, 9, 20, 15, 7]
    ino = [9, 3, 15, 20, 7]
    tree = build_tree(pre, ino)
    assert _preorder(tree) == pre
    print("ok")
```

### `trees/count_good_nodes.py`

```python
"""Count Good Nodes in Binary Tree  |  tier: neetcode150  |  Trees

A node is "good" if no node on the path from the root to it has a greater value.
Count the good nodes.

Approach: DFS carrying the maximum value seen on the path so far. A node is good
when its value >= that running max; recurse with the updated max.
Time: O(n)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def good_nodes(root: TreeNode) -> int:
    """Return the count of good nodes."""
    def dfs(node: Optional[TreeNode], path_max: int) -> int:
        if node is None:
            return 0
        good = 1 if node.val >= path_max else 0
        new_max = max(path_max, node.val)
        return good + dfs(node.left, new_max) + dfs(node.right, new_max)

    return dfs(root, root.val)


if __name__ == "__main__":
    #        3
    #      1   4
    #     3   1 5
    root = TreeNode(3,
                    TreeNode(1, TreeNode(3)),
                    TreeNode(4, TreeNode(1), TreeNode(5)))
    assert good_nodes(root) == 4
    assert good_nodes(TreeNode(1)) == 1
    print("ok")
```

### `trees/diameter_binary_tree.py`

```python
"""Diameter of Binary Tree  |  tier: neetcode150  |  Trees

Return the length (in edges) of the longest path between any two nodes. The path
need not pass through the root.

Approach: DFS returning subtree height. At each node the longest path THROUGH it
is left_height + right_height; track the global max while computing heights.
Time: O(n)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def diameter_of_binary_tree(root: Optional[TreeNode]) -> int:
    """Return the diameter (longest path in edges)."""
    best = 0

    def height(node: Optional[TreeNode]) -> int:
        nonlocal best
        if node is None:
            return 0
        left = height(node.left)
        right = height(node.right)
        best = max(best, left + right)       # path through this node
        return 1 + max(left, right)

    height(root)
    return best


if __name__ == "__main__":
    root = TreeNode(1, TreeNode(2, TreeNode(4), TreeNode(5)), TreeNode(3))
    assert diameter_of_binary_tree(root) == 3        # 4-2-5 ... 4-2-1-3 = 3
    assert diameter_of_binary_tree(TreeNode(1)) == 0
    print("ok")
```

### `trees/invert_binary_tree.py`

```python
"""Invert Binary Tree  |  tier: core50, blind75, neetcode150  |  Trees

Mirror a binary tree: swap every node's left and right subtrees.

Approach: recurse, swapping children at each node. (A BFS/DFS with a queue/stack
works identically.)
Time: O(n)   Space: O(h)  recursion depth
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def invert_tree(root: Optional[TreeNode]) -> Optional[TreeNode]:
    """Return the root of the mirrored tree."""
    if root is None:
        return None
    root.left, root.right = invert_tree(root.right), invert_tree(root.left)
    return root


def _inorder(root: Optional[TreeNode]) -> list[int]:
    if root is None:
        return []
    return _inorder(root.left) + [root.val] + _inorder(root.right)


if __name__ == "__main__":
    #        4
    #      2   7
    #     1 3 6 9
    root = TreeNode(4,
                    TreeNode(2, TreeNode(1), TreeNode(3)),
                    TreeNode(7, TreeNode(6), TreeNode(9)))
    assert _inorder(invert_tree(root)) == [9, 7, 6, 4, 3, 2, 1]
    assert invert_tree(None) is None
    print("ok")
```

### `trees/kth_smallest_bst.py`

```python
"""Kth Smallest Element in a BST  |  tier: blind75, neetcode150  |  Trees

Return the k-th smallest value (1-indexed) in a BST.

Approach: an in-order traversal of a BST yields values in sorted order. Walk
iteratively with a stack and stop at the k-th visited node.
Time: O(h + k)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary search tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def kth_smallest(root: Optional[TreeNode], k: int) -> int:
    """Return the k-th smallest value via in-order traversal."""
    stack: list[TreeNode] = []
    node = root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        k -= 1
        if k == 0:
            return node.val
        node = node.right
    raise ValueError("k larger than tree size")


if __name__ == "__main__":
    #      3
    #    1   4
    #     2
    root = TreeNode(3, TreeNode(1, None, TreeNode(2)), TreeNode(4))
    assert kth_smallest(root, 1) == 1
    assert kth_smallest(root, 2) == 2
    assert kth_smallest(root, 4) == 4
    print("ok")
```

### `trees/level_order_traversal.py`

```python
"""Binary Tree Level Order Traversal  |  tier: core50, blind75, neetcode150  |  Trees

Return node values level by level, top to bottom, left to right.

Approach: BFS with a queue. Process the queue one full level at a time using its
current length, collecting each level's values into its own list.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from collections import deque
from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def level_order(root: Optional[TreeNode]) -> list[list[int]]:
    """Return values grouped by level (BFS)."""
    if root is None:
        return []
    result: list[list[int]] = []
    queue: deque[TreeNode] = deque([root])
    while queue:
        level: list[int] = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result


if __name__ == "__main__":
    root = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
    assert level_order(root) == [[3], [9, 20], [15, 7]]
    assert level_order(None) == []
    print("ok")
```

### `trees/lowest_common_ancestor_bst.py`

```python
"""Lowest Common Ancestor of a BST  |  tier: core50, blind75, neetcode150  |  Trees

Return the lowest common ancestor of two nodes node_p and node_q in a binary SEARCH tree.

Approach: exploit BST ordering. If both values are less than the node, go left;
if both greater, go right; otherwise the paths split here -> this node is the LCA.
Time: O(h)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary search tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def lowest_common_ancestor(
    root: TreeNode, node_p: TreeNode, node_q: TreeNode
) -> TreeNode:
    """Return the LCA node of node_p and node_q in the BST."""
    node: Optional[TreeNode] = root
    while node:
        if node_p.val < node.val and node_q.val < node.val:
            node = node.left
        elif node_p.val > node.val and node_q.val > node.val:
            node = node.right
        else:
            return node
    raise ValueError("nodes not found")


if __name__ == "__main__":
    #        6
    #     2     8
    #   0  4  7   9
    n0, n4, n7, n9 = TreeNode(0), TreeNode(4), TreeNode(7), TreeNode(9)
    n2 = TreeNode(2, n0, n4)
    n8 = TreeNode(8, n7, n9)
    root = TreeNode(6, n2, n8)
    assert lowest_common_ancestor(root, n2, n8).val == 6
    assert lowest_common_ancestor(root, n2, n4).val == 2
    print("ok")
```

### `trees/max_depth_binary_tree.py`

```python
"""Maximum Depth of Binary Tree  |  tier: core50, blind75, neetcode150  |  Trees

Return the number of nodes along the longest root-to-leaf path.

Approach: depth(node) = 1 + max(depth(left), depth(right)); empty subtree is 0.
Time: O(n)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def max_depth(root: Optional[TreeNode]) -> int:
    """Return the maximum depth of the tree."""
    if root is None:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))


if __name__ == "__main__":
    root = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
    assert max_depth(root) == 3
    assert max_depth(None) == 0
    assert max_depth(TreeNode(1)) == 1
    print("ok")
```

### `trees/right_side_view.py`

```python
"""Binary Tree Right Side View  |  tier: neetcode150  |  Trees

Return the values visible from the right side, top to bottom (the last node of
each level).

Approach: BFS level by level; the last node dequeued in each level is the one
visible from the right.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from collections import deque
from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def right_side_view(root: Optional[TreeNode]) -> list[int]:
    """Return the rightmost value at each level."""
    if root is None:
        return []
    result: list[int] = []
    queue: deque[TreeNode] = deque([root])
    while queue:
        size = len(queue)
        for i in range(size):
            node = queue.popleft()
            if i == size - 1:            # last node of this level
                result.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
    return result


if __name__ == "__main__":
    root = TreeNode(1, TreeNode(2, None, TreeNode(5)), TreeNode(3, None, TreeNode(4)))
    assert right_side_view(root) == [1, 3, 4]
    assert right_side_view(None) == []
    print("ok")
```

### `trees/same_tree.py`

```python
"""Same Tree  |  tier: core50, blind75, neetcode150  |  Trees

Return True if two binary trees are structurally identical with equal values.

Approach: recurse in lockstep. Both None -> equal; one None or values differ ->
not equal; else compare left and right subtrees.
Time: O(n)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def is_same_tree(tree1: Optional[TreeNode], tree2: Optional[TreeNode]) -> bool:
    """Return True if both trees are identical."""
    if tree1 is None and tree2 is None:
        return True
    if tree1 is None or tree2 is None or tree1.val != tree2.val:
        return False
    return is_same_tree(tree1.left, tree2.left) and is_same_tree(tree1.right, tree2.right)


if __name__ == "__main__":
    tree1 = TreeNode(1, TreeNode(2), TreeNode(3))
    tree2 = TreeNode(1, TreeNode(2), TreeNode(3))
    tree3 = TreeNode(1, TreeNode(2), TreeNode(4))
    assert is_same_tree(tree1, tree2) is True
    assert is_same_tree(tree1, tree3) is False
    assert is_same_tree(None, None) is True
    print("ok")
```

### `trees/serialize_deserialize.py`

```python
"""Serialize and Deserialize Binary Tree  |  tier: blind75, neetcode150  |  Trees

Encode a binary tree to a string and decode it back to the same structure.

Approach: preorder DFS. Emit each value, using a sentinel ('#') for None.
Deserialize consumes the tokens in the same preorder, rebuilding recursively.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from collections import deque
from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def serialize(root: Optional[TreeNode]) -> str:
    """Encode the tree to a comma-separated preorder string."""
    parts: list[str] = []

    def dfs(node: Optional[TreeNode]) -> None:
        if node is None:
            parts.append("#")
            return
        parts.append(str(node.val))
        dfs(node.left)
        dfs(node.right)

    dfs(root)
    return ",".join(parts)


def deserialize(data: str) -> Optional[TreeNode]:
    """Decode the preorder string back into a tree."""
    tokens = deque(data.split(","))

    def build() -> Optional[TreeNode]:
        tok = tokens.popleft()
        if tok == "#":
            return None
        node = TreeNode(int(tok))
        node.left = build()
        node.right = build()
        return node

    return build()


def _inorder(node: Optional[TreeNode]) -> list[int]:
    if node is None:
        return []
    return _inorder(node.left) + [node.val] + _inorder(node.right)


if __name__ == "__main__":
    root = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4), TreeNode(5)))
    restored = deserialize(serialize(root))
    assert _inorder(restored) == _inorder(root)
    assert serialize(None) == "#"
    assert deserialize(serialize(None)) is None
    print("ok")
```

### `trees/subtree_of_another_tree.py`

```python
"""Subtree of Another Tree  |  tier: blind75, neetcode150  |  Trees

Return True if subRoot is a subtree of root (a node in root whose subtree is
identical to subRoot).

Approach: at every node of root, test same-tree against subRoot. An empty
subRoot is always a subtree.
Time: O(n * m)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def _same(tree1: Optional[TreeNode], tree2: Optional[TreeNode]) -> bool:
    if tree1 is None and tree2 is None:
        return True
    if tree1 is None or tree2 is None or tree1.val != tree2.val:
        return False
    return _same(tree1.left, tree2.left) and _same(tree1.right, tree2.right)


def is_subtree(root: Optional[TreeNode], sub_root: Optional[TreeNode]) -> bool:
    """Return True if sub_root is a subtree of root."""
    if sub_root is None:
        return True
    if root is None:
        return False
    if _same(root, sub_root):
        return True
    return is_subtree(root.left, sub_root) or is_subtree(root.right, sub_root)


if __name__ == "__main__":
    root = TreeNode(3, TreeNode(4, TreeNode(1), TreeNode(2)), TreeNode(5))
    sub = TreeNode(4, TreeNode(1), TreeNode(2))
    assert is_subtree(root, sub) is True
    assert is_subtree(root, TreeNode(4, TreeNode(1), TreeNode(2, TreeNode(0)))) is False
    print("ok")
```

### `trees/validate_bst.py`

```python
"""Validate Binary Search Tree  |  tier: core50, blind75, neetcode150  |  Trees

Return True if the tree is a valid BST: every left subtree value < node <
every right subtree value (strictly).

Approach: DFS carrying an open (low, high) bound. Each node must lie strictly
inside; recurse tightening the bound for each child. Bounds (not just the parent)
catch violations several levels apart.
Time: O(n)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None,
                 right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def is_valid_bst(root: Optional[TreeNode]) -> bool:
    """Return True if the tree is a valid binary search tree."""
    def valid(node: Optional[TreeNode], low: float, high: float) -> bool:
        if node is None:
            return True
        if not (low < node.val < high):
            return False
        return (valid(node.left, low, node.val)
                and valid(node.right, node.val, high))

    return valid(root, float("-inf"), float("inf"))


if __name__ == "__main__":
    assert is_valid_bst(TreeNode(2, TreeNode(1), TreeNode(3))) is True
    # 5 with right child 4 -> invalid even though 4 < 6
    bad = TreeNode(5, TreeNode(1), TreeNode(6, TreeNode(4), TreeNode(7)))
    assert is_valid_bst(bad) is False
    print("ok")
```


---

## Tries

### `tries/design_add_search_words.py`

```python
"""Design Add and Search Words  |  tier: blind75, neetcode150  |  Tries

Support addWord(word) and search(word) where '.' in a search matches any single
character.

Approach: a trie. Search is a DFS; on a '.', recurse into every child, otherwise
follow the single matching child.
Time: add O(len); search O(len) typical, O(26^len) worst with many dots
Space: O(total chars)
"""
from __future__ import annotations


class TrieNode:
    """Trie node with children and end-of-word flag."""

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_word = False


class WordDictionary:
    """Word store supporting '.' wildcard search."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def add_word(self, word: str) -> None:
        """Insert a word."""
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_word = True

    def search(self, word: str) -> bool:
        """Return True if word matches a stored word ('.' = any char)."""
        def dfs(node: TrieNode, i: int) -> bool:
            if i == len(word):
                return node.is_word
            char = word[i]
            if char == ".":
                return any(dfs(child, i + 1) for child in node.children.values())
            return char in node.children and dfs(node.children[char], i + 1)

        return dfs(self.root, 0)


if __name__ == "__main__":
    wd = WordDictionary()
    for word in ["bad", "dad", "mad"]:
        wd.add_word(word)
    assert wd.search("pad") is False
    assert wd.search("bad") is True
    assert wd.search(".ad") is True
    assert wd.search("b..") is True
    print("ok")
```

### `tries/implement_trie.py`

```python
"""Implement Trie (Prefix Tree)  |  tier: core50, blind75, neetcode150  |  Tries

Support insert(word), search(word), and startsWith(prefix).

Approach: a tree where each node has children keyed by character and an
end-of-word flag. Each operation walks one node per character.
Time: O(len) per op   Space: O(total chars inserted)
"""
from __future__ import annotations


class TrieNode:
    """A single trie node: child links + end-of-word marker."""

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_word = False


class Trie:
    """Prefix tree over lowercase words."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        """Add a word to the trie."""
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_word = True

    def search(self, word: str) -> bool:
        """Return True if the exact word was inserted."""
        node = self._walk(word)
        return node is not None and node.is_word

    def starts_with(self, prefix: str) -> bool:
        """Return True if any inserted word has this prefix."""
        return self._walk(prefix) is not None

    def _walk(self, key: str) -> TrieNode | None:
        node = self.root
        for char in key:
            if char not in node.children:
                return None
            node = node.children[char]
        return node


if __name__ == "__main__":
    trie = Trie()
    trie.insert("apple")
    assert trie.search("apple") is True
    assert trie.search("app") is False
    assert trie.starts_with("app") is True
    trie.insert("app")
    assert trie.search("app") is True
    print("ok")
```

### `tries/word_search_ii.py`

```python
"""Word Search II  |  tier: neetcode150  |  Tries

Given a grid of letters and a word list, return all words that can be formed by
sequentially adjacent cells (no cell reused per word).

Approach: build a trie of the words, then DFS the grid following trie edges. The
trie prunes dead branches early (vs searching each word separately) and dedups
shared prefixes. Mark found words to avoid duplicates.
Time: O(cells * 4^maxlen) worst   Space: O(total chars)
"""
from __future__ import annotations


class TrieNode:
    """Trie node storing children and the complete word at its end."""

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.word: str | None = None


def find_words(board: list[list[str]], words: list[str]) -> list[str]:
    """Return all board-formable words from the list."""
    root = TrieNode()
    for word in words:
        node = root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.word = word

    rows, cols = len(board), len(board[0])
    found: list[str] = []

    def dfs(r: int, c: int, node: TrieNode) -> None:
        char = board[r][c]
        if char == "#" or char not in node.children:
            return
        nxt = node.children[char]
        if nxt.word is not None:
            found.append(nxt.word)
            nxt.word = None              # dedupe
        board[r][c] = "#"                # mark visited
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                dfs(nr, nc, nxt)
        board[r][c] = char               # restore

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, root)
    return found


if __name__ == "__main__":
    board = [
        ["o", "a", "a", "n"],
        ["e", "t", "a", "e"],
        ["i", "h", "k", "r"],
        ["i", "f", "l", "v"],
    ]
    assert sorted(find_words(board, ["oath", "pea", "eat", "rain"])) == ["eat", "oath"]
    print("ok")
```


---

## Heap

### `heap/design_twitter.py`

```python
"""Design Twitter  |  tier: neetcode150  |  Heap

Support postTweet, getNewsFeed (10 most recent tweets from the user and everyone
they follow), follow, and unfollow.

Approach: per-user tweet lists with a global timestamp for ordering. getNewsFeed
merges the relevant users' recent tweets with a max-heap keyed by timestamp,
pulling the 10 newest.
Time: getNewsFeed O(f + 10 log f)   Space: O(total tweets + follows)
"""
from __future__ import annotations

import heapq
from collections import defaultdict


class Twitter:
    """Minimal Twitter feed backed by per-user tweet logs."""

    def __init__(self) -> None:
        self._time = 0
        self._tweets: defaultdict[int, list[tuple[int, int]]] = defaultdict(list)
        self._following: defaultdict[int, set[int]] = defaultdict(set)

    def post_tweet(self, user_id: int, tweet_id: int) -> None:
        """Record a tweet with a monotonically increasing timestamp."""
        self._tweets[user_id].append((self._time, tweet_id))
        self._time += 1

    def get_news_feed(self, user_id: int) -> list[int]:
        """Return the 10 most recent tweet ids from self + followees."""
        users = self._following[user_id] | {user_id}
        heap: list[tuple[int, int]] = []
        for uid in users:
            for ts, tid in self._tweets[uid][-10:]:
                heap.append((ts, tid))
        return [tid for _, tid in heapq.nlargest(10, heap)]

    def follow(self, follower_id: int, followee_id: int) -> None:
        """follower starts following followee."""
        self._following[follower_id].add(followee_id)

    def unfollow(self, follower_id: int, followee_id: int) -> None:
        """follower stops following followee."""
        self._following[follower_id].discard(followee_id)


if __name__ == "__main__":
    tw = Twitter()
    tw.post_tweet(1, 5)
    assert tw.get_news_feed(1) == [5]
    tw.follow(1, 2)
    tw.post_tweet(2, 6)
    assert tw.get_news_feed(1) == [6, 5]
    tw.unfollow(1, 2)
    assert tw.get_news_feed(1) == [5]
    print("ok")
```

### `heap/find_median_from_stream.py`

```python
"""Find Median from Data Stream  |  tier: blind75, neetcode150  |  Heap

Support addNum(num) and findMedian() over a growing stream.

Approach: two heaps. A max-heap 'low' holds the smaller half, a min-heap 'high'
holds the larger half. Keep their sizes balanced (differ by <= 1). The median is
the top of the larger heap, or the average of both tops when sizes are equal.
Time: add O(log n), median O(1)   Space: O(n)
"""
from __future__ import annotations

import heapq


class MedianFinder:
    """Streaming median via two balanced heaps."""

    def __init__(self) -> None:
        self._low: list[int] = []        # max-heap (negated)
        self._high: list[int] = []       # min-heap

    def add_num(self, num: int) -> None:
        """Add a number, keeping the two halves balanced and ordered."""
        heapq.heappush(self._low, -num)
        heapq.heappush(self._high, -heapq.heappop(self._low))   # move max over
        if len(self._high) > len(self._low):                    # rebalance
            heapq.heappush(self._low, -heapq.heappop(self._high))

    def find_median(self) -> float:
        """Return the current median."""
        if len(self._low) > len(self._high):
            return float(-self._low[0])
        return (-self._low[0] + self._high[0]) / 2


if __name__ == "__main__":
    mf = MedianFinder()
    mf.add_num(1)
    mf.add_num(2)
    assert mf.find_median() == 1.5
    mf.add_num(3)
    assert mf.find_median() == 2.0
    print("ok")
```

### `heap/k_closest_points.py`

```python
"""K Closest Points to Origin  |  tier: neetcode150  |  Heap

Return the k points closest to the origin (Euclidean distance).

Approach: max-heap of size k keyed by squared distance (no sqrt needed -- it is
monotonic). Keep only the k smallest distances by evicting the largest.
Time: O(n log k)   Space: O(k)
"""
from __future__ import annotations

import heapq


def k_closest(points: list[list[int]], k: int) -> list[list[int]]:
    """Return the k points nearest the origin (any order)."""
    heap: list[tuple[int, list[int]]] = []
    for x, y in points:
        dist = -(x * x + y * y)          # negate -> max-heap behavior
        if len(heap) < k:
            heapq.heappush(heap, (dist, [x, y]))
        elif dist > heap[0][0]:
            heapq.heapreplace(heap, (dist, [x, y]))
    return [point for _, point in heap]


if __name__ == "__main__":
    out = k_closest([[1, 3], [-2, 2]], 1)
    assert out == [[-2, 2]]
    out2 = sorted(k_closest([[3, 3], [5, -1], [-2, 4]], 2))
    assert out2 == [[-2, 4], [3, 3]]
    print("ok")
```

### `heap/kth_largest_element.py`

```python
"""Kth Largest Element in an Array  |  tier: core50, neetcode150  |  Heap

Return the k-th largest element (k-th in sorted-descending order).

Approach: a min-heap of size k. After processing all elements, the heap holds
the k largest and its root is the answer. (Quickselect gives O(n) average; the
heap is simpler and O(n log k).)
Time: O(n log k)   Space: O(k)
"""
from __future__ import annotations

import heapq


def find_kth_largest(nums: list[int], k: int) -> int:
    """Return the k-th largest element."""
    heap: list[int] = []
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0]


if __name__ == "__main__":
    assert find_kth_largest([3, 2, 1, 5, 6, 4], 2) == 5
    assert find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert find_kth_largest([1], 1) == 1
    print("ok")
```

### `heap/kth_largest_in_stream.py`

```python
"""Kth Largest Element in a Stream  |  tier: neetcode150  |  Heap

Design a class that, given k, returns the k-th largest value seen so far after
each add().

Approach: a min-heap of size k holds the k largest values; its root is the
k-th largest. On add, push and pop the smallest if size exceeds k.
Time: O(log k) per add   Space: O(k)
"""
from __future__ import annotations

import heapq


class KthLargest:
    """Maintains the k-th largest element of a stream."""

    def __init__(self, k: int, nums: list[int]) -> None:
        self.k = k
        self.heap = nums[:]
        heapq.heapify(self.heap)
        while len(self.heap) > k:
            heapq.heappop(self.heap)

    def add(self, val: int) -> int:
        """Add a value and return the current k-th largest."""
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]


if __name__ == "__main__":
    kth = KthLargest(3, [4, 5, 8, 2])
    assert kth.add(3) == 4
    assert kth.add(5) == 5
    assert kth.add(10) == 5
    assert kth.add(9) == 8
    assert kth.add(4) == 8
    print("ok")
```

### `heap/last_stone_weight.py`

```python
"""Last Stone Weight  |  tier: neetcode150  |  Heap

Repeatedly smash the two heaviest stones; if unequal, the difference returns to
the pile. Return the weight of the last remaining stone (0 if none).

Approach: max-heap (negate values for Python's min-heap). Pop the two largest,
push back their difference if non-zero.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations

import heapq


def last_stone_weight(stones: list[int]) -> int:
    """Return the weight of the last stone after all smashes."""
    heap = [-stone for stone in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        first = -heapq.heappop(heap)
        second = -heapq.heappop(heap)
        if first != second:
            heapq.heappush(heap, -(first - second))
    return -heap[0] if heap else 0


if __name__ == "__main__":
    assert last_stone_weight([2, 7, 4, 1, 8, 1]) == 1
    assert last_stone_weight([1]) == 1
    assert last_stone_weight([2, 2]) == 0
    print("ok")
```

### `heap/task_scheduler.py`

```python
"""Task Scheduler  |  tier: neetcode150  |  Heap

Given task labels and a cooldown (same task must be >= cooldown slots apart),
return the minimum number of CPU intervals (including idles) to finish all tasks.

Approach: the most frequent task dictates the skeleton. With max_freq copies and
gaps of size cooldown, the frame is (max_freq - 1) * (cooldown + 1) + (count of
tasks tied at max_freq). The answer is max(total_tasks, that frame) -- if there
are enough distinct tasks, no idling is needed.
Time: O(n)   Space: O(1)  (26 labels)
"""
from __future__ import annotations

from collections import Counter


def least_interval(tasks: list[str], cooldown: int) -> int:
    """Return the minimum number of intervals to run all tasks."""
    counts = Counter(tasks)
    max_freq = max(counts.values())
    num_max = sum(1 for count in counts.values() if count == max_freq)
    frame = (max_freq - 1) * (cooldown + 1) + num_max
    return max(len(tasks), frame)


if __name__ == "__main__":
    assert least_interval(["A", "A", "A", "B", "B", "B"], 2) == 8
    assert least_interval(["A", "A", "A", "B", "B", "B"], 0) == 6
    assert least_interval(["A", "B", "C", "D"], 2) == 4
    print("ok")
```


---

## Backtracking

### `backtracking/combination_sum.py`

```python
"""Combination Sum  |  tier: core50, blind75, neetcode150  |  Backtracking

Given distinct candidates and a target, return all unique combinations summing to
target. Each candidate may be reused unlimited times.

Approach: backtracking. At each step either reuse the current candidate (stay on
the same index) or advance. Prune when the remaining target goes negative.
Time: exponential in target/candidates   Space: O(target) depth
"""
from __future__ import annotations


def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    """Return all combinations summing to target (reuse allowed)."""
    result: list[list[int]] = []
    current: list[int] = []

    def backtrack(start: int, remaining: int) -> None:
        if remaining == 0:
            result.append(current[:])
            return
        if remaining < 0:
            return
        for i in range(start, len(candidates)):
            current.append(candidates[i])
            backtrack(i, remaining - candidates[i])   # i, not i+1 -> reuse
            current.pop()

    backtrack(0, target)
    return result


if __name__ == "__main__":
    assert sorted(combination_sum([2, 3, 6, 7], 7)) == sorted([[2, 2, 3], [7]])
    assert sorted(combination_sum([2, 3, 5], 8)) == sorted(
        [[2, 2, 2, 2], [2, 3, 3], [3, 5]]
    )
    assert combination_sum([2], 1) == []
    print("ok")
```

### `backtracking/combination_sum_ii.py`

```python
"""Combination Sum II  |  tier: neetcode150  |  Backtracking

Given candidates (with duplicates) and a target, return unique combinations
summing to target. Each candidate may be used at most once.

Approach: sort, then backtrack advancing the index each pick (no reuse). Skip a
duplicate candidate at the same level to avoid duplicate combinations. Prune when
remaining < 0.
Time: O(2^n)   Space: O(n)
"""
from __future__ import annotations


def combination_sum2(candidates: list[int], target: int) -> list[list[int]]:
    """Return unique combinations summing to target (each used once)."""
    candidates.sort()
    result: list[list[int]] = []
    current: list[int] = []

    def backtrack(start: int, remaining: int) -> None:
        if remaining == 0:
            result.append(current[:])
            return
        for i in range(start, len(candidates)):
            if i > start and candidates[i] == candidates[i - 1]:
                continue                 # skip duplicate at this level
            if candidates[i] > remaining:
                break                    # sorted: no further candidate fits
            current.append(candidates[i])
            backtrack(i + 1, remaining - candidates[i])
            current.pop()

    backtrack(0, target)
    return result


if __name__ == "__main__":
    assert sorted(combination_sum2([10, 1, 2, 7, 6, 1, 5], 8)) == sorted(
        [[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]]
    )
    assert sorted(combination_sum2([2, 5, 2, 1, 2], 5)) == sorted([[1, 2, 2], [5]])
    print("ok")
```

### `backtracking/letter_combinations.py`

```python
"""Letter Combinations of a Phone Number  |  tier: neetcode150  |  Backtracking

Given digits 2-9, return all letter combinations the number could spell (phone
keypad mapping).

Approach: backtracking. For each digit, try every mapped letter, building the
string position by position until all digits are consumed.
Time: O(4^n * n)   Space: O(n)
"""
from __future__ import annotations


def letter_combinations(digits: str) -> list[str]:
    """Return all keypad letter combinations for the digit string."""
    if not digits:
        return []
    keypad = {
        "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
        "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz",
    }
    result: list[str] = []
    current: list[str] = []

    def backtrack(i: int) -> None:
        if i == len(digits):
            result.append("".join(current))
            return
        for letter in keypad[digits[i]]:
            current.append(letter)
            backtrack(i + 1)
            current.pop()

    backtrack(0)
    return result


if __name__ == "__main__":
    assert sorted(letter_combinations("23")) == sorted(
        ["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]
    )
    assert letter_combinations("") == []
    assert letter_combinations("2") == ["a", "b", "c"]
    print("ok")
```

### `backtracking/n_queens.py`

```python
"""N-Queens  |  tier: neetcode150  |  Backtracking

Place n queens on an n x n board so none attack each other; return the number of
distinct solutions.

Approach: place one queen per row, backtracking. Track occupied columns and both
diagonal directions (r + c and r - c) in sets for O(1) conflict checks.
Time: O(n!)   Space: O(n)
"""
from __future__ import annotations


def total_n_queens(n: int) -> int:
    """Return the number of distinct N-Queens placements."""
    cols: set[int] = set()
    diag: set[int] = set()               # r + c
    anti: set[int] = set()               # r - c
    count = 0

    def backtrack(row: int) -> None:
        nonlocal count
        if row == n:
            count += 1
            return
        for col in range(n):
            if col in cols or (row + col) in diag or (row - col) in anti:
                continue
            cols.add(col); diag.add(row + col); anti.add(row - col)
            backtrack(row + 1)
            cols.remove(col); diag.remove(row + col); anti.remove(row - col)

    backtrack(0)
    return count


if __name__ == "__main__":
    assert total_n_queens(4) == 2
    assert total_n_queens(1) == 1
    assert total_n_queens(8) == 92
    print("ok")
```

### `backtracking/palindrome_partitioning.py`

```python
"""Palindrome Partitioning  |  tier: neetcode150  |  Backtracking

Partition a string so every substring is a palindrome; return all such
partitionings.

Approach: backtracking over cut positions. For each prefix that is a palindrome,
fix it as the next part and recurse on the remainder.
Time: O(n * 2^n)   Space: O(n)
"""
from __future__ import annotations


def partition(text: str) -> list[list[str]]:
    """Return all palindrome partitionings of text."""
    result: list[list[str]] = []
    current: list[str] = []

    def is_palindrome(sub: str) -> bool:
        return sub == sub[::-1]

    def backtrack(start: int) -> None:
        if start == len(text):
            result.append(current[:])
            return
        for end in range(start + 1, len(text) + 1):
            prefix = text[start:end]
            if is_palindrome(prefix):
                current.append(prefix)
                backtrack(end)
                current.pop()

    backtrack(0)
    return result


if __name__ == "__main__":
    assert sorted(partition("aab")) == sorted([["a", "a", "b"], ["aa", "b"]])
    assert partition("a") == [["a"]]
    print("ok")
```

### `backtracking/permutations.py`

```python
"""Permutations  |  tier: core50, neetcode150  |  Backtracking

Return all permutations of a list of distinct integers.

Approach: backtracking with a used set (or in-place swaps). Build a permutation
one position at a time, marking elements used to avoid reuse.
Time: O(n * n!)   Space: O(n) recursion
"""
from __future__ import annotations


def permute(nums: list[int]) -> list[list[int]]:
    """Return all permutations of nums."""
    result: list[list[int]] = []
    current: list[int] = []
    used = [False] * len(nums)

    def backtrack() -> None:
        if len(current) == len(nums):
            result.append(current[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            current.append(nums[i])
            backtrack()
            current.pop()
            used[i] = False

    backtrack()
    return result


if __name__ == "__main__":
    out = permute([1, 2, 3])
    assert len(out) == 6
    assert sorted(out) == sorted(
        [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
    )
    print("ok")
```

### `backtracking/subsets.py`

```python
"""Subsets  |  tier: core50, neetcode150  |  Backtracking

Return all subsets (the power set) of a list of distinct integers.

Approach: backtracking. At each index choose to include or skip the element,
recording the current partial subset at every leaf. 2^n subsets.
Time: O(n * 2^n)   Space: O(n) recursion
"""
from __future__ import annotations


def subsets(nums: list[int]) -> list[list[int]]:
    """Return the power set of nums."""
    result: list[list[int]] = []
    current: list[int] = []

    def backtrack(start: int) -> None:
        result.append(current[:])
        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1)
            current.pop()

    backtrack(0)
    return result


if __name__ == "__main__":
    out = subsets([1, 2, 3])
    assert len(out) == 8
    assert sorted(out) == sorted(
        [[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]
    )
    print("ok")
```

### `backtracking/subsets_ii.py`

```python
"""Subsets II  |  tier: neetcode150  |  Backtracking

Return all unique subsets when the input may contain duplicates.

Approach: sort first so duplicates are adjacent. During backtracking, skip a
candidate that equals the previous one at the SAME recursion level -- this avoids
generating duplicate subsets.
Time: O(n * 2^n)   Space: O(n)
"""
from __future__ import annotations


def subsets_with_dup(nums: list[int]) -> list[list[int]]:
    """Return all unique subsets (input may have duplicates)."""
    nums.sort()
    result: list[list[int]] = []
    current: list[int] = []

    def backtrack(start: int) -> None:
        result.append(current[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:
                continue                 # skip duplicate at this level
            current.append(nums[i])
            backtrack(i + 1)
            current.pop()

    backtrack(0)
    return result


if __name__ == "__main__":
    out = subsets_with_dup([1, 2, 2])
    assert sorted(out) == sorted([[], [1], [1, 2], [1, 2, 2], [2], [2, 2]])
    print("ok")
```

### `backtracking/word_search.py`

```python
"""Word Search  |  tier: core50, blind75, neetcode150  |  Backtracking

Return True if a word can be formed from sequentially adjacent cells in a grid
(no cell reused).

Approach: DFS from each cell matching the word char by char. Mark visited cells
in place (temporary sentinel), recurse to four neighbors, then restore.
Time: O(cells * 4^len)   Space: O(len) recursion
"""
from __future__ import annotations


def exist(board: list[list[str]], word: str) -> bool:
    """Return True if word exists as an adjacent path in the grid."""
    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int, i: int) -> bool:
        if i == len(word):
            return True
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[i]:
            return False
        board[r][c] = "#"                # mark visited
        found = (dfs(r + 1, c, i + 1) or dfs(r - 1, c, i + 1)
                 or dfs(r, c + 1, i + 1) or dfs(r, c - 1, i + 1))
        board[r][c] = word[i]            # restore
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


if __name__ == "__main__":
    board = [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]
    assert exist(board, "ABCCED") is True
    assert exist(board, "SEE") is True
    assert exist(board, "ABCB") is False
    print("ok")
```


---

## Graphs

### `graphs/clone_graph.py`

```python
"""Clone Graph  |  tier: blind75, neetcode150  |  Graphs

Deep-copy a connected undirected graph given a node reference.

Approach: DFS (or BFS) with a map from original node -> its clone. Create a
clone on first visit, then recurse to clone and link neighbors. The map prevents
infinite loops on cycles.
Time: O(V + E)   Space: O(V)
"""
from __future__ import annotations

from typing import Optional


class Node:
    """Undirected graph node with a neighbor list."""

    def __init__(self, val: int = 0, neighbors: "Optional[list[Node]]" = None) -> None:
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


def clone_graph(node: Optional[Node]) -> Optional[Node]:
    """Return a deep copy of the graph."""
    if node is None:
        return None
    clones: dict[Node, Node] = {}

    def dfs(original: Node) -> Node:
        if original in clones:
            return clones[original]
        copy = Node(original.val)
        clones[original] = copy
        for neighbor in original.neighbors:
            copy.neighbors.append(dfs(neighbor))
        return copy

    return dfs(node)


if __name__ == "__main__":
    node1, node2, node3, node4 = Node(1), Node(2), Node(3), Node(4)
    node1.neighbors = [node2, node4]
    node2.neighbors = [node1, node3]
    node3.neighbors = [node2, node4]
    node4.neighbors = [node1, node3]
    copy = clone_graph(node1)
    assert copy is not node1 and copy.val == 1  # type: ignore[union-attr]
    assert sorted(neighbor.val for neighbor in copy.neighbors) == [2, 4]  # type: ignore[union-attr]
    assert copy.neighbors[0] is not node2  # type: ignore[union-attr]
    print("ok")
```

### `graphs/course_schedule.py`

```python
"""Course Schedule  |  tier: core50, blind75, neetcode150  |  Graphs

Given numCourses and prerequisite pairs [course, prereq] (prereq before course),
return True if all courses can be finished -- i.e. the dependency graph has no
cycle.

Approach: DFS cycle detection with three states (unvisited / in-progress /
done). Hitting an in-progress node means a back edge -> cycle.
Time: O(V + E)   Space: O(V + E)
"""
from __future__ import annotations

from collections import defaultdict


def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    """Return True if the course dependency graph is acyclic."""
    graph: defaultdict[int, list[int]] = defaultdict(list)
    for course, prereq in prerequisites:
        graph[course].append(prereq)

    state = [0] * num_courses            # 0=unseen, 1=in-progress, 2=done

    def has_cycle(node: int) -> bool:
        if state[node] == 1:
            return True
        if state[node] == 2:
            return False
        state[node] = 1
        for neighbor in graph[node]:
            if has_cycle(neighbor):
                return True
        state[node] = 2
        return False

    return not any(has_cycle(course) for course in range(num_courses))


if __name__ == "__main__":
    assert can_finish(2, [[1, 0]]) is True
    assert can_finish(2, [[1, 0], [0, 1]]) is False
    assert can_finish(1, []) is True
    print("ok")
```

### `graphs/course_schedule_ii.py`

```python
"""Course Schedule II  |  tier: neetcode150  |  Graphs

Return an order to take all courses given prerequisites, or [] if impossible.

Approach: Kahn's algorithm (BFS topological sort). Repeatedly take nodes with
in-degree 0, append to the order, and decrement neighbors. If the order covers
every course, it is valid; otherwise a cycle exists.
Time: O(V + E)   Space: O(V + E)
"""
from __future__ import annotations

from collections import defaultdict, deque


def find_order(num_courses: int, prerequisites: list[list[int]]) -> list[int]:
    """Return a valid course order, or [] if a cycle exists."""
    graph: defaultdict[int, list[int]] = defaultdict(list)
    indegree = [0] * num_courses
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        indegree[course] += 1

    queue: deque[int] = deque(
        course for course in range(num_courses) if indegree[course] == 0
    )
    order: list[int] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    return order if len(order) == num_courses else []


if __name__ == "__main__":
    assert find_order(2, [[1, 0]]) == [0, 1]
    order = find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]])
    assert order[0] == 0 and order[-1] == 3 and len(order) == 4
    assert find_order(2, [[0, 1], [1, 0]]) == []
    print("ok")
```

### `graphs/graph_valid_tree.py`

```python
"""Graph Valid Tree  |  tier: blind75, neetcode150  |  Graphs

Given num_nodes nodes and an undirected edge list, return True if they form a
valid tree: fully connected and acyclic.

Approach: a tree on num_nodes nodes has exactly num_nodes - 1 edges and is
connected. Check the edge count, then union-find: if any edge joins two
already-connected nodes, there is a cycle.
Time: O(n + e)   Space: O(n)
"""
from __future__ import annotations


def valid_tree(num_nodes: int, edges: list[list[int]]) -> bool:
    """Return True if the graph is a valid tree."""
    if len(edges) != num_nodes - 1:      # tree must have exactly num_nodes - 1 edges
        return False
    parent = list(range(num_nodes))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for node_a, node_b in edges:
        root_a, root_b = find(node_a), find(node_b)
        if root_a == root_b:
            return False                 # cycle
        parent[root_a] = root_b
    return True                          # num_nodes - 1 edges + no cycle => connected


if __name__ == "__main__":
    assert valid_tree(5, [[0, 1], [0, 2], [0, 3], [1, 4]]) is True
    assert valid_tree(5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]) is False
    assert valid_tree(1, []) is True
    print("ok")
```

### `graphs/max_area_of_island.py`

```python
"""Max Area of Island  |  tier: neetcode150  |  Graphs

Return the area of the largest island (1s connected 4-directionally); 0 if none.

Approach: flood-fill DFS from each unvisited land cell, summing the cells
reached, and track the maximum.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations


def max_area_of_island(grid: list[list[int]]) -> int:
    """Return the maximum island area."""
    rows, cols = len(grid), len(grid[0])

    def area(r: int, c: int) -> int:
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] == 0:
            return 0
        grid[r][c] = 0                   # mark visited
        return 1 + area(r + 1, c) + area(r - 1, c) + area(r, c + 1) + area(r, c - 1)

    best = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                best = max(best, area(r, c))
    return best


if __name__ == "__main__":
    grid = [
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 1, 1],
    ]
    assert max_area_of_island(grid) == 3
    assert max_area_of_island([[0, 0], [0, 0]]) == 0
    print("ok")
```

### `graphs/number_of_connected_components.py`

```python
"""Number of Connected Components  |  tier: blind75, neetcode150  |  Graphs

Given num_nodes nodes (0..num_nodes-1) and an undirected edge list, return the
number of connected components.

Approach: union-find. Start with num_nodes components; each edge that joins two
distinct sets reduces the count by one.
Time: O(n + e * alpha(n))   Space: O(n)
"""
from __future__ import annotations


def count_components(num_nodes: int, edges: list[list[int]]) -> int:
    """Return the number of connected components."""
    parent = list(range(num_nodes))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    components = num_nodes
    for node_a, node_b in edges:
        root_a, root_b = find(node_a), find(node_b)
        if root_a != root_b:
            parent[root_a] = root_b
            components -= 1
    return components


if __name__ == "__main__":
    assert count_components(5, [[0, 1], [1, 2], [3, 4]]) == 2
    assert count_components(5, [[0, 1], [1, 2], [2, 3], [3, 4]]) == 1
    assert count_components(4, []) == 4
    print("ok")
```

### `graphs/number_of_islands.py`

```python
"""Number of Islands  |  tier: core50, blind75, neetcode150  |  Graphs

Count islands ('1' land connected 4-directionally) in a grid of '1'/'0'.

Approach: scan cells; on each unvisited land cell, flood-fill (DFS) the whole
island marking cells visited, and increment the count.
Time: O(rows * cols)   Space: O(rows * cols) recursion worst case
"""
from __future__ import annotations


def num_islands(grid: list[list[str]]) -> int:
    """Return the number of islands in the grid."""
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])

    def sink(r: int, c: int) -> None:
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] != "1":
            return
        grid[r][c] = "0"                 # mark visited
        sink(r + 1, c); sink(r - 1, c); sink(r, c + 1); sink(r, c - 1)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                sink(r, c)
                count += 1
    return count


if __name__ == "__main__":
    grid = [
        ["1", "1", "0", "0", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "1", "0", "0"],
        ["0", "0", "0", "1", "1"],
    ]
    assert num_islands(grid) == 3
    assert num_islands([["0"]]) == 0
    print("ok")
```

### `graphs/pacific_atlantic.py`

```python
"""Pacific Atlantic Water Flow  |  tier: blind75, neetcode150  |  Graphs

Water flows from a cell to neighbors of equal or lower height. The Pacific
touches the top/left edges, the Atlantic the bottom/right. Return cells that can
reach both oceans.

Approach: instead of searching from each cell, DFS INWARD from each ocean's
border, marking cells that can reach that ocean (climbing to >= height). The
answer is the intersection of the two reachable sets.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations


def pacific_atlantic(heights: list[list[int]]) -> list[list[int]]:
    """Return cells from which water reaches both oceans."""
    if not heights:
        return []
    rows, cols = len(heights), len(heights[0])
    pacific: set[tuple[int, int]] = set()
    atlantic: set[tuple[int, int]] = set()

    def dfs(r: int, c: int, seen: set[tuple[int, int]], prev: int) -> None:
        if (not (0 <= r < rows and 0 <= c < cols) or (r, c) in seen
                or heights[r][c] < prev):
            return
        seen.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            dfs(r + dr, c + dc, seen, heights[r][c])

    for c in range(cols):
        dfs(0, c, pacific, heights[0][c])
        dfs(rows - 1, c, atlantic, heights[rows - 1][c])
    for r in range(rows):
        dfs(r, 0, pacific, heights[r][0])
        dfs(r, cols - 1, atlantic, heights[r][cols - 1])

    return [[r, c] for r, c in pacific & atlantic]


if __name__ == "__main__":
    heights = [
        [1, 2, 2, 3, 5],
        [3, 2, 3, 4, 4],
        [2, 4, 5, 3, 1],
        [6, 7, 1, 4, 5],
        [5, 1, 1, 2, 4],
    ]
    result = {tuple(cell) for cell in pacific_atlantic(heights)}
    expected = {(0, 4), (1, 3), (1, 4), (2, 2), (3, 0), (3, 1), (4, 0)}
    assert result == expected
    print("ok")
```

### `graphs/redundant_connection.py`

```python
"""Redundant Connection  |  tier: neetcode150  |  Graphs

A tree had one extra edge added, forming exactly one cycle. Return the edge that
can be removed (the last one in input order that closes a cycle).

Approach: union-find. Process edges; for each, if both endpoints already share a
root, that edge closes the cycle -> return it. Otherwise union them.
Time: O(n * alpha(n))   Space: O(n)
"""
from __future__ import annotations


def find_redundant_connection(edges: list[list[int]]) -> list[int]:
    """Return the redundant edge forming a cycle."""
    parent = list(range(len(edges) + 1))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]    # path compression
            node = parent[node]
        return node

    for node_a, node_b in edges:
        root_a, root_b = find(node_a), find(node_b)
        if root_a == root_b:
            return [node_a, node_b]      # already connected -> cycle edge
        parent[root_a] = root_b
    return []


if __name__ == "__main__":
    assert find_redundant_connection([[1, 2], [1, 3], [2, 3]]) == [2, 3]
    assert find_redundant_connection(
        [[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]
    ) == [1, 4]
    print("ok")
```

### `graphs/rotting_oranges.py`

```python
"""Rotting Oranges  |  tier: neetcode150  |  Graphs

Each minute, rotten oranges (2) rot their fresh (1) 4-directional neighbors.
Return minutes until none are fresh, or -1 if impossible.

Approach: multi-source BFS. Start with all rotten cells in the queue, spread
level by level counting minutes. If fresh oranges remain afterward, return -1.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations

from collections import deque


def oranges_rotting(grid: list[list[int]]) -> int:
    """Return minutes until all oranges rot, or -1."""
    rows, cols = len(grid), len(grid[0])
    queue: deque[tuple[int, int]] = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c))
            elif grid[r][c] == 1:
                fresh += 1

    minutes = 0
    while queue and fresh:
        minutes += 1
        for _ in range(len(queue)):
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    fresh -= 1
                    queue.append((nr, nc))
    return -1 if fresh else minutes


if __name__ == "__main__":
    assert oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]) == 4
    assert oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]]) == -1
    assert oranges_rotting([[0, 2]]) == 0
    print("ok")
```

### `graphs/surrounded_regions.py`

```python
"""Surrounded Regions  |  tier: neetcode150  |  Graphs

Capture all regions of 'O' fully surrounded by 'X' by flipping them to 'X'. An
'O' connected to a border is NOT captured.

Approach: DFS from every border 'O', marking the whole connected region as safe
(temporary '#'). Then flip all remaining 'O' (captured) to 'X' and restore '#'
back to 'O'.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations


def solve(board: list[list[str]]) -> None:
    """Flip surrounded 'O' regions to 'X' in place."""
    if not board:
        return
    rows, cols = len(board), len(board[0])

    def mark_safe(r: int, c: int) -> None:
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != "O":
            return
        board[r][c] = "#"
        mark_safe(r + 1, c); mark_safe(r - 1, c)
        mark_safe(r, c + 1); mark_safe(r, c - 1)

    for r in range(rows):
        mark_safe(r, 0); mark_safe(r, cols - 1)
    for c in range(cols):
        mark_safe(0, c); mark_safe(rows - 1, c)

    for r in range(rows):
        for c in range(cols):
            if board[r][c] == "O":
                board[r][c] = "X"        # captured
            elif board[r][c] == "#":
                board[r][c] = "O"        # restore safe


if __name__ == "__main__":
    board = [
        ["X", "X", "X", "X"],
        ["X", "O", "O", "X"],
        ["X", "X", "O", "X"],
        ["X", "O", "X", "X"],
    ]
    solve(board)
    assert board == [
        ["X", "X", "X", "X"],
        ["X", "X", "X", "X"],
        ["X", "X", "X", "X"],
        ["X", "O", "X", "X"],
    ]
    print("ok")
```

### `graphs/walls_and_gates.py`

```python
"""Walls and Gates  |  tier: neetcode150  |  Graphs

Fill each empty room (2^31 - 1) with the distance to its nearest gate (0). Walls
are -1. Unreachable rooms keep their large value. Modify the grid in place.

Approach: multi-source BFS from all gates simultaneously. The first time BFS
reaches a room is its shortest distance to any gate.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations

from collections import deque

INF = 2 ** 31 - 1


def walls_and_gates(rooms: list[list[int]]) -> None:
    """Fill rooms with distance to nearest gate, in place."""
    if not rooms:
        return
    rows, cols = len(rooms), len(rooms[0])
    queue: deque[tuple[int, int]] = deque(
        (r, c) for r in range(rows) for c in range(cols) if rooms[r][c] == 0
    )
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and rooms[nr][nc] == INF:
                rooms[nr][nc] = rooms[r][c] + 1
                queue.append((nr, nc))


if __name__ == "__main__":
    rooms = [
        [INF, -1, 0, INF],
        [INF, INF, INF, -1],
        [INF, -1, INF, -1],
        [0, -1, INF, INF],
    ]
    walls_and_gates(rooms)
    assert rooms == [
        [3, -1, 0, 1],
        [2, 2, 1, -1],
        [1, -1, 2, -1],
        [0, -1, 3, 4],
    ]
    print("ok")
```

### `graphs/word_ladder.py`

```python
"""Word Ladder  |  tier: neetcode150  |  Graphs

Return the length of the shortest transformation sequence from beginWord to
endWord, changing one letter at a time, with each intermediate in wordList.
0 if impossible.

Approach: BFS over words (shortest path = fewest steps). Generate neighbors via
wildcard patterns ("h*t") grouping words that differ by one letter, so each
word's neighbors are found in O(L) instead of scanning the whole list.
Time: O(N * L^2)   Space: O(N * L)
"""
from __future__ import annotations

from collections import defaultdict, deque


def ladder_length(begin_word: str, end_word: str, word_list: list[str]) -> int:
    """Return the shortest transformation length, or 0."""
    words = set(word_list)
    if end_word not in words:
        return 0

    patterns: defaultdict[str, list[str]] = defaultdict(list)
    for word in words | {begin_word}:
        for i in range(len(word)):
            patterns[word[:i] + "*" + word[i + 1:]].append(word)

    queue: deque[tuple[str, int]] = deque([(begin_word, 1)])
    seen = {begin_word}
    while queue:
        word, steps = queue.popleft()
        if word == end_word:
            return steps
        for i in range(len(word)):
            for neighbor in patterns[word[:i] + "*" + word[i + 1:]]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, steps + 1))
    return 0


if __name__ == "__main__":
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]) == 5
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log"]) == 0
    print("ok")
```


---

## Advanced Graphs

### `advanced_graphs/alien_dictionary.py`

```python
"""Alien Dictionary  |  tier: blind75, neetcode150  |  Advanced Graphs

Given words sorted by the rules of an alien language, return any valid ordering
of its letters, or "" if the ordering is invalid.

Approach: build a graph of letter precedences from each adjacent word pair (first
differing char gives an edge). Topologically sort the letters; a cycle or a
prefix-violation (longer word before its prefix) means no valid order.
Time: O(total chars)   Space: O(unique letters)
"""
from __future__ import annotations

from collections import defaultdict, deque


def alien_order(words: list[str]) -> str:
    """Return a valid letter ordering for the alien language, or ''."""
    graph: defaultdict[str, set[str]] = defaultdict(set)
    indegree = {ch: 0 for word in words for ch in word}

    for first, second in zip(words, words[1:]):
        min_len = min(len(first), len(second))
        if first[:min_len] == second[:min_len] and len(first) > len(second):
            return ""                    # prefix appears after longer word
        for char_first, char_second in zip(first, second):
            if char_first != char_second:
                if char_second not in graph[char_first]:
                    graph[char_first].add(char_second)
                    indegree[char_second] += 1
                break

    queue: deque[str] = deque(ch for ch in indegree if indegree[ch] == 0)
    order: list[str] = []
    while queue:
        ch = queue.popleft()
        order.append(ch)
        for nxt in graph[ch]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return "".join(order) if len(order) == len(indegree) else ""


if __name__ == "__main__":
    assert alien_order(["wrt", "wrf", "er", "ett", "rftt"]) == "wertf"
    assert alien_order(["z", "x"]) == "zx"
    assert alien_order(["abc", "ab"]) == ""          # invalid: prefix after word
    print("ok")
```

### `advanced_graphs/cheapest_flights_k_stops.py`

```python
"""Cheapest Flights Within K Stops  |  tier: neetcode150  |  Advanced Graphs

Find the cheapest price from src to dst using at most k stops (k+1 edges), or -1.

Approach: Bellman-Ford limited to k+1 relaxation rounds. Each round relaxes all
edges using a SNAPSHOT of the previous round's costs, so no path uses more than
the allowed number of edges.
Time: O(k * E)   Space: O(V)
"""
from __future__ import annotations


def find_cheapest_price(
    n: int, flights: list[list[int]], src: int, dst: int, k: int
) -> int:
    """Return the cheapest price within k stops, or -1."""
    cost = [float("inf")] * n
    cost[src] = 0
    for _ in range(k + 1):
        snapshot = cost[:]               # use last round's values only
        for u, v, price in flights:
            if snapshot[u] + price < cost[v]:
                cost[v] = snapshot[u] + price
    return -1 if cost[dst] == float("inf") else int(cost[dst])


if __name__ == "__main__":
    flights = [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]]
    assert find_cheapest_price(4, flights, 0, 3, 1) == 700
    flights2 = [[0, 1, 100], [1, 2, 100], [0, 2, 500]]
    assert find_cheapest_price(3, flights2, 0, 2, 1) == 200
    assert find_cheapest_price(3, flights2, 0, 2, 0) == 500
    print("ok")
```

### `advanced_graphs/min_cost_connect_points.py`

```python
"""Min Cost to Connect All Points  |  tier: neetcode150  |  Advanced Graphs

Connect all points with minimum total Manhattan-distance edge cost (a minimum
spanning tree).

Approach: Prim's algorithm with a min-heap. Start from any point; repeatedly add
the cheapest edge to an unvisited point, then push that point's edges.
Time: O(n^2 log n)   Space: O(n^2)
"""
from __future__ import annotations

import heapq


def min_cost_connect_points(points: list[list[int]]) -> int:
    """Return the minimum cost to connect all points (MST)."""
    n = len(points)
    visited: set[int] = set()
    heap: list[tuple[int, int]] = [(0, 0)]    # (cost, point index)
    total = 0
    while len(visited) < n:
        cost, i = heapq.heappop(heap)
        if i in visited:
            continue
        visited.add(i)
        total += cost
        xi, yi = points[i]
        for j in range(n):
            if j not in visited:
                xj, yj = points[j]
                dist = abs(xi - xj) + abs(yi - yj)
                heapq.heappush(heap, (dist, j))
    return total


if __name__ == "__main__":
    assert min_cost_connect_points(
        [[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]
    ) == 20
    assert min_cost_connect_points([[0, 0]]) == 0
    print("ok")
```

### `advanced_graphs/network_delay_time.py`

```python
"""Network Delay Time  |  tier: neetcode150  |  Advanced Graphs

Signals travel along directed weighted edges from node k. Return the time for all
n nodes to receive the signal, or -1 if some node is unreachable.

Approach: Dijkstra's shortest path from k. The answer is the maximum shortest
distance among all nodes (the last to be reached).
Time: O(E log V)   Space: O(V + E)
"""
from __future__ import annotations

import heapq
from collections import defaultdict


def network_delay_time(times: list[list[int]], n: int, k: int) -> int:
    """Return the time for all nodes to receive the signal, or -1."""
    graph: defaultdict[int, list[tuple[int, int]]] = defaultdict(list)
    for src, dst, weight in times:
        graph[src].append((dst, weight))

    dist: dict[int, int] = {}
    heap: list[tuple[int, int]] = [(0, k)]
    while heap:
        delay, node = heapq.heappop(heap)
        if node in dist:
            continue
        dist[node] = delay
        for neighbor, weight in graph[node]:
            if neighbor not in dist:
                heapq.heappush(heap, (delay + weight, neighbor))

    return max(dist.values()) if len(dist) == n else -1


if __name__ == "__main__":
    assert network_delay_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2) == 2
    assert network_delay_time([[1, 2, 1]], 2, 1) == 1
    assert network_delay_time([[1, 2, 1]], 2, 2) == -1
    print("ok")
```

### `advanced_graphs/reconstruct_itinerary.py`

```python
"""Reconstruct Itinerary  |  tier: neetcode150  |  Advanced Graphs

Given airline tickets [from, to], reconstruct the itinerary starting at "JFK",
using every ticket exactly once. If multiple are valid, return the
lexicographically smallest.

Approach: Hierholzer's algorithm for an Eulerian path. Sort each node's
destinations (visit smallest first). DFS, and append a node to the route only
after its edges are exhausted; reverse the route at the end.
Time: O(E log E)   Space: O(E)
"""
from __future__ import annotations

from collections import defaultdict


def find_itinerary(tickets: list[list[str]]) -> list[str]:
    """Return the lexicographically smallest valid itinerary from JFK."""
    graph: defaultdict[str, list[str]] = defaultdict(list)
    for src, dst in sorted(tickets, reverse=True):
        graph[src].append(dst)           # reverse-sorted -> pop() gives smallest

    route: list[str] = []
    stack = ["JFK"]
    while stack:
        while graph[stack[-1]]:
            stack.append(graph[stack[-1]].pop())
        route.append(stack.pop())
    return route[::-1]


if __name__ == "__main__":
    assert find_itinerary(
        [["MUC", "LHR"], ["JFK", "MUC"], ["SFO", "SJC"], ["LHR", "SFO"]]
    ) == ["JFK", "MUC", "LHR", "SFO", "SJC"]
    assert find_itinerary(
        [["JFK", "SFO"], ["JFK", "ATL"], ["SFO", "ATL"], ["ATL", "JFK"], ["ATL", "SFO"]]
    ) == ["JFK", "ATL", "JFK", "SFO", "ATL", "SFO"]
    print("ok")
```

### `advanced_graphs/swim_in_rising_water.py`

```python
"""Swim in Rising Water  |  tier: neetcode150  |  Advanced Graphs

At time t, water depth is t everywhere. You can move 4-directionally between
cells whose height <= t. Return the least time to reach the bottom-right from the
top-left.

Approach: Dijkstra-like greedy with a min-heap keyed by the max height seen on
the path so far. Always expand the cell reachable with the lowest "max height";
the first time the target pops, that value is the answer.
Time: O(n^2 log n)   Space: O(n^2)
"""
from __future__ import annotations

import heapq


def swim_in_water(grid: list[list[int]]) -> int:
    """Return the minimum time to reach the bottom-right cell."""
    n = len(grid)
    visited: set[tuple[int, int]] = set()
    heap: list[tuple[int, int, int]] = [(grid[0][0], 0, 0)]   # (max_height, r, c)
    while heap:
        height, r, c = heapq.heappop(heap)
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if r == n - 1 and c == n - 1:
            return height
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in visited:
                heapq.heappush(heap, (max(height, grid[nr][nc]), nr, nc))
    return -1


if __name__ == "__main__":
    assert swim_in_water([[0, 2], [1, 3]]) == 3
    assert swim_in_water(
        [[0, 1, 2, 3, 4], [24, 23, 22, 21, 5], [12, 13, 14, 15, 16],
         [11, 17, 18, 19, 20], [10, 9, 8, 7, 6]]
    ) == 16
    print("ok")
```


---

## 1-D DP

### `dp_1d/climbing_stairs.py`

```python
"""Climbing Stairs  |  tier: core50, blind75, neetcode150  |  1-D DP

You can climb 1 or 2 steps at a time. Return the number of distinct ways to reach
step n.

Approach: ways(n) = ways(n-1) + ways(n-2) -- it is the Fibonacci recurrence. Roll
two variables instead of an array.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def climb_stairs(n: int) -> int:
    """Return the number of distinct ways to climb n stairs."""
    prev, curr = 1, 1                    # ways to reach step 0 and 1
    for _ in range(n - 1):
        prev, curr = curr, prev + curr
    return curr


if __name__ == "__main__":
    assert climb_stairs(2) == 2          # 1+1, 2
    assert climb_stairs(3) == 3          # 1+1+1, 1+2, 2+1
    assert climb_stairs(5) == 8
    print("ok")
```

### `dp_1d/coin_change.py`

```python
"""Coin Change  |  tier: core50, blind75, neetcode150  |  1-D DP

Return the fewest coins summing to amount, or -1 if impossible. Unlimited coins
of each denomination.

Approach: bottom-up DP. dp[current_amount] = min coins to make that amount. For
each amount, try each coin: dp[current_amount] = min(dp[current_amount],
dp[current_amount - coin] + 1).
Time: O(amount * coins)   Space: O(amount)
"""
from __future__ import annotations


def coin_change(coins: list[int], amount: int) -> int:
    """Return the minimum number of coins to make amount, or -1."""
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for current_amount in range(1, amount + 1):
        for coin in coins:
            if coin <= current_amount:
                dp[current_amount] = min(dp[current_amount], dp[current_amount - coin] + 1)
    return -1 if dp[amount] == float("inf") else int(dp[amount])


if __name__ == "__main__":
    assert coin_change([1, 2, 5], 11) == 3      # 5 + 5 + 1
    assert coin_change([2], 3) == -1
    assert coin_change([1], 0) == 0
    print("ok")
```

### `dp_1d/decode_ways.py`

```python
"""Decode Ways  |  tier: blind75, neetcode150  |  1-D DP

Digits map to letters: '1'->'A' ... '26'->'Z'. Return the number of ways to
decode the string. Leading '0' digits cannot start a valid code.

Approach: dp[i] = ways to decode the suffix from i. Add dp[i+1] if the single
digit is valid (not '0'), plus dp[i+2] if the two-digit number is 10..26. Roll
two variables.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def num_decodings(digits: str) -> int:
    """Return the number of ways to decode the digit string."""
    if not digits or digits[0] == "0":
        return 0
    two_ahead, one_ahead = 1, 1          # dp[i+2], dp[i+1]
    for i in range(len(digits) - 1, -1, -1):
        current = 0 if digits[i] == "0" else one_ahead
        if i + 1 < len(digits) and 10 <= int(digits[i:i + 2]) <= 26:
            current += two_ahead
        two_ahead, one_ahead = one_ahead, current
    return one_ahead


if __name__ == "__main__":
    assert num_decodings("12") == 2      # "AB", "L"
    assert num_decodings("226") == 3     # "BZ", "VF", "BBF"
    assert num_decodings("06") == 0
    print("ok")
```

### `dp_1d/house_robber.py`

```python
"""House Robber  |  tier: core50, blind75, neetcode150  |  1-D DP

Maximize loot from houses in a row without robbing two adjacent houses.

Approach: dp[i] = max(dp[i-1], dp[i-2] + nums[i]) -- either skip house i or rob
it plus the best up to i-2. Roll two variables.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def rob(nums: list[int]) -> int:
    """Return the maximum loot without robbing adjacent houses."""
    prev, curr = 0, 0                    # best up to i-2 and i-1
    for num in nums:
        prev, curr = curr, max(curr, prev + num)
    return curr


if __name__ == "__main__":
    assert rob([1, 2, 3, 1]) == 4        # rob 1 and 3
    assert rob([2, 7, 9, 3, 1]) == 12    # rob 2, 9, 1
    assert rob([]) == 0
    print("ok")
```

### `dp_1d/house_robber_ii.py`

```python
"""House Robber II  |  tier: blind75, neetcode150  |  1-D DP

Houses are arranged in a CIRCLE, so the first and last are adjacent. Maximize
loot without robbing two adjacent houses.

Approach: the circular constraint means house 0 and house n-1 can't both be
robbed. Run the linear House Robber twice -- on houses [0..n-2] and [1..n-1] --
and take the better. Handle the single-house case directly.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def _rob_linear(nums: list[int]) -> int:
    prev, curr = 0, 0
    for num in nums:
        prev, curr = curr, max(curr, prev + num)
    return curr


def rob(nums: list[int]) -> int:
    """Return max loot for houses in a circle."""
    if len(nums) == 1:
        return nums[0]
    return max(_rob_linear(nums[:-1]), _rob_linear(nums[1:]))


if __name__ == "__main__":
    assert rob([2, 3, 2]) == 3           # can't rob both ends
    assert rob([1, 2, 3, 1]) == 4
    assert rob([1, 2, 3]) == 3
    assert rob([5]) == 5
    print("ok")
```

### `dp_1d/longest_increasing_subsequence.py`

```python
"""Longest Increasing Subsequence  |  tier: core50, blind75, neetcode150  |  1-D DP

Return the length of the longest strictly increasing subsequence.

Approach: patience sorting. Maintain 'tails', where tails[i] is the smallest
possible tail of an increasing subsequence of length i+1. For each number,
binary-search its insertion point; the length of tails is the answer.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations

from bisect import bisect_left


def length_of_lis(nums: list[int]) -> int:
    """Return the length of the longest strictly increasing subsequence."""
    tails: list[int] = []
    for num in nums:
        i = bisect_left(tails, num)      # first tail >= num
        if i == len(tails):
            tails.append(num)            # extends the longest subsequence
        else:
            tails[i] = num               # lowers a tail -> more room later
    return len(tails)


if __name__ == "__main__":
    assert length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4    # 2,3,7,101
    assert length_of_lis([0, 1, 0, 3, 2, 3]) == 4
    assert length_of_lis([7, 7, 7, 7]) == 1
    print("ok")
```

### `dp_1d/longest_palindromic_substring.py`

```python
"""Longest Palindromic Substring  |  tier: blind75, neetcode150  |  1-D DP

Return the longest substring that is a palindrome.

Approach: expand around centers. Each index (and each gap between indices) is a
potential palindrome center; expand outward while characters match. Track the
longest span found. 2n-1 centers.
Time: O(n^2)   Space: O(1)
"""
from __future__ import annotations


def longest_palindrome(text: str) -> str:
    """Return the longest palindromic substring."""
    if not text:
        return ""
    start, end = 0, 0

    def expand(left: int, right: int) -> tuple[int, int]:
        while left >= 0 and right < len(text) and text[left] == text[right]:
            left -= 1
            right += 1
        return left + 1, right - 1       # last valid bounds

    for i in range(len(text)):
        for left, right in (expand(i, i), expand(i, i + 1)):   # odd, even centers
            if right - left > end - start:
                start, end = left, right
    return text[start:end + 1]


if __name__ == "__main__":
    assert longest_palindrome("babad") in {"bab", "aba"}
    assert longest_palindrome("cbbd") == "bb"
    assert longest_palindrome("a") == "a"
    print("ok")
```

### `dp_1d/maximum_product_subarray.py`

```python
"""Maximum Product Subarray  |  tier: blind75, neetcode150  |  1-D DP

Return the largest product of any contiguous subarray.

Approach: track BOTH the running max and min products ending here -- a negative
number flips them, so today's min can become tomorrow's max. Reset on the current
element to allow starting fresh.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_product(nums: list[int]) -> int:
    """Return the maximum product of a contiguous subarray."""
    best = cur_max = cur_min = nums[0]
    for num in nums[1:]:
        candidates = (num, cur_max * num, cur_min * num)
        cur_max = max(candidates)
        cur_min = min(candidates)
        best = max(best, cur_max)
    return best


if __name__ == "__main__":
    assert max_product([2, 3, -2, 4]) == 6        # [2, 3]
    assert max_product([-2, 0, -1]) == 0
    assert max_product([-2, 3, -4]) == 24         # all three
    print("ok")
```

### `dp_1d/min_cost_climbing_stairs.py`

```python
"""Min Cost Climbing Stairs  |  tier: neetcode150  |  1-D DP

Each step has a cost; from a step you climb 1 or 2 steps. You may start at index
0 or 1. Return the minimum cost to reach the top (past the last step).

Approach: dp[i] = min cost to STAND on step i = cost[i] + min(dp[i-1], dp[i-2]).
The answer is min(dp[last], dp[second-last]). Roll two variables.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def min_cost_climbing_stairs(cost: list[int]) -> int:
    """Return the minimum cost to reach the top of the stairs."""
    n = len(cost)
    prev2, prev1 = 0, 0                  # dp[i-2], dp[i-1]: cost to ARRIVE at step
    for i in range(2, n + 1):           # step n is the top (past last index)
        cur = min(prev1 + cost[i - 1], prev2 + cost[i - 2])
        prev2, prev1 = prev1, cur
    return prev1


if __name__ == "__main__":
    assert min_cost_climbing_stairs([10, 15, 20]) == 15
    assert min_cost_climbing_stairs([1, 100, 1, 1, 1, 100, 1, 1, 100, 1]) == 6
    print("ok")
```

### `dp_1d/palindromic_substrings.py`

```python
"""Palindromic Substrings  |  tier: blind75, neetcode150  |  1-D DP

Count how many substrings are palindromes (different positions count separately).

Approach: expand around each of the 2n-1 centers, counting every palindrome found
while expanding outward.
Time: O(n^2)   Space: O(1)
"""
from __future__ import annotations


def count_substrings(text: str) -> int:
    """Return the number of palindromic substrings."""
    total = 0

    def expand(left: int, right: int) -> int:
        count = 0
        while left >= 0 and right < len(text) and text[left] == text[right]:
            count += 1
            left -= 1
            right += 1
        return count

    for i in range(len(text)):
        total += expand(i, i)            # odd-length centers
        total += expand(i, i + 1)        # even-length centers
    return total


if __name__ == "__main__":
    assert count_substrings("abc") == 3          # a, b, c
    assert count_substrings("aaa") == 6          # a,a,a, aa,aa, aaa
    print("ok")
```

### `dp_1d/partition_equal_subset_sum.py`

```python
"""Partition Equal Subset Sum  |  tier: neetcode150  |  1-D DP

Return True if the array can be split into two subsets with equal sum.

Approach: this is a 0/1 subset-sum for target = total / 2. Use a boolean set of
reachable sums; for each number, add it to every previously reachable sum. An odd
total is immediately impossible.
Time: O(n * sum)   Space: O(sum)
"""
from __future__ import annotations


def can_partition(nums: list[int]) -> bool:
    """Return True if nums splits into two equal-sum subsets."""
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    reachable: set[int] = {0}
    for num in nums:
        reachable |= {partial_sum + num for partial_sum in reachable if partial_sum + num <= target}
        if target in reachable:
            return True
    return target in reachable


if __name__ == "__main__":
    assert can_partition([1, 5, 11, 5]) is True      # [1,5,5] and [11]
    assert can_partition([1, 2, 3, 5]) is False
    assert can_partition([1, 1]) is True
    print("ok")
```

### `dp_1d/word_break.py`

```python
"""Word Break  |  tier: core50, blind75, neetcode150  |  1-D DP

Return True if text can be segmented into a space-separated sequence of dictionary
words (words reusable).

Approach: dp[i] = True if text[:i] is segmentable. For each end i, check every
split j: if dp[j] and text[j:i] is a word, then dp[i] is True.
Time: O(n^2 * wordlen)   Space: O(n)
"""
from __future__ import annotations


def word_break(text: str, word_dict: list[str]) -> bool:
    """Return True if text can be segmented into dictionary words."""
    words = set(word_dict)
    dp = [False] * (len(text) + 1)
    dp[0] = True                         # empty prefix is segmentable
    for i in range(1, len(text) + 1):
        for j in range(i):
            if dp[j] and text[j:i] in words:
                dp[i] = True
                break
    return dp[len(text)]


if __name__ == "__main__":
    assert word_break("leetcode", ["leet", "code"]) is True
    assert word_break("applepenapple", ["apple", "pen"]) is True
    assert word_break("catsandog", ["cats", "dog", "sand", "and", "cat"]) is False
    print("ok")
```


---

## 2-D DP

### `dp_2d/best_time_buy_sell_cooldown.py`

```python
"""Best Time to Buy/Sell Stock with Cooldown  |  tier: neetcode150  |  2-D DP

Maximize profit with unlimited transactions, but after selling you must cool down
one day before buying again.

Approach: state machine over three states per day: hold (own a share), sold (just
sold, cooling down), rest (idle, free to buy). Transition each day and roll the
values.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_profit(prices: list[int]) -> int:
    """Return the max profit with a one-day cooldown after each sale."""
    hold = float("-inf")                 # best profit while holding a share
    sold = 0                             # best profit having just sold today
    rest = 0                             # best profit idle (can buy)
    for price in prices:
        prev_sold = sold
        sold = hold + price              # sell today
        hold = max(hold, rest - price)   # keep holding or buy from rest
        rest = max(rest, prev_sold)      # stay idle or finish cooldown
    return int(max(sold, rest))


if __name__ == "__main__":
    assert max_profit([1, 2, 3, 0, 2]) == 3      # buy,sell,cooldown,buy,sell
    assert max_profit([1]) == 0
    assert max_profit([2, 1]) == 0
    print("ok")
```

### `dp_2d/burst_balloons.py`

```python
"""Burst Balloons  |  tier: neetcode150  |  2-D DP

Bursting balloon i yields nums[i-1] * nums[i] * nums[i+1] coins (out-of-range = 1).
Return the maximum coins from bursting all balloons.

Approach: interval DP. Pad with 1s at both ends. dp[l][r] = best coins for the
open interval (l, r), choosing balloon k as the LAST to burst there, so its
neighbors are the fixed boundaries l and r. Build over increasing interval width.
Time: O(n^3)   Space: O(n^2)
"""
from __future__ import annotations


def max_coins(nums: list[int]) -> int:
    """Return the maximum coins obtainable by bursting all balloons."""
    balloons = [1] + nums + [1]
    n = len(balloons)
    dp = [[0] * n for _ in range(n)]
    for width in range(2, n):
        for left in range(n - width):
            right = left + width
            for k in range(left + 1, right):     # k = last balloon burst in (left,right)
                coins = balloons[left] * balloons[k] * balloons[right]
                dp[left][right] = max(
                    dp[left][right], dp[left][k] + coins + dp[k][right]
                )
    return dp[0][n - 1]


if __name__ == "__main__":
    assert max_coins([3, 1, 5, 8]) == 167
    assert max_coins([1, 5]) == 10
    print("ok")
```

### `dp_2d/coin_change_ii.py`

```python
"""Coin Change II  |  tier: neetcode150  |  2-D DP

Return the number of distinct combinations of coins that sum to amount (unlimited
coins; order does not matter).

Approach: dp[sub_amount] = ways to make sub_amount. Iterate coins in the OUTER
loop so each combination is counted once (order-independent); for each coin add
dp[sub_amount - coin].
Time: O(amount * coins)   Space: O(amount)
"""
from __future__ import annotations


def change(amount: int, coins: list[int]) -> int:
    """Return the number of coin combinations summing to amount."""
    dp = [0] * (amount + 1)
    dp[0] = 1                            # one way to make 0: use nothing
    for coin in coins:                   # coin outer -> combinations, not perms
        for sub_amount in range(coin, amount + 1):
            dp[sub_amount] += dp[sub_amount - coin]
    return dp[amount]


if __name__ == "__main__":
    assert change(5, [1, 2, 5]) == 4     # 5; 2+2+1; 2+1+1+1; 1x5
    assert change(3, [2]) == 0
    assert change(10, [10]) == 1
    print("ok")
```

### `dp_2d/distinct_subsequences.py`

```python
"""Distinct Subsequences  |  tier: neetcode150  |  2-D DP

Return the number of distinct subsequences of source that equal target.

Approach: dp[j] = ways to form target[:j]. Iterate source; update j from high to
low so each source-char is used once per position. When source[i] == target[j-1],
dp[j] += dp[j-1].
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def num_distinct(source: str, target: str) -> int:
    """Return the count of subsequences of source equal to target."""
    dp = [1] + [0] * len(target)         # dp[0] = 1: empty target matches once
    for ch in source:
        for j in range(len(target), 0, -1):   # reverse -> don't reuse this char
            if ch == target[j - 1]:
                dp[j] += dp[j - 1]
    return dp[len(target)]


if __name__ == "__main__":
    assert num_distinct("rabbbit", "rabbit") == 3
    assert num_distinct("babgbag", "bag") == 5
    assert num_distinct("abc", "") == 1
    print("ok")
```

### `dp_2d/edit_distance.py`

```python
"""Edit Distance  |  tier: blind75, neetcode150  |  2-D DP

Return the minimum number of insert/delete/replace operations to convert word1
into word2 (Levenshtein distance).

Approach: dp[i][j] = edits to turn word1[:i] into word2[:j]. If chars match, carry
the diagonal; else 1 + min(delete, insert, replace). Roll one row.
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def min_distance(word1: str, word2: str) -> int:
    """Return the edit distance between word1 and word2."""
    prev = list(range(len(word2) + 1))   # transform "" -> word2[:j] = j inserts
    for i in range(1, len(word1) + 1):
        curr = [i] + [0] * len(word2)    # transform word1[:i] -> "" = i deletes
        for j in range(1, len(word2) + 1):
            if word1[i - 1] == word2[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[len(word2)]


if __name__ == "__main__":
    assert min_distance("horse", "ros") == 3
    assert min_distance("intention", "execution") == 5
    assert min_distance("", "abc") == 3
    print("ok")
```

### `dp_2d/interleaving_string.py`

```python
"""Interleaving String  |  tier: neetcode150  |  2-D DP

Return True if s3 is formed by interleaving s1 and s2 (preserving each one's
character order).

Approach: dp[i][j] = can s3[:i+j] be formed from s1[:i] and s2[:j]. Each step
takes the next char from s1 (if it matches) or from s2. Roll one row.
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def is_interleave(s1: str, s2: str, s3: str) -> bool:
    """Return True if s3 is an interleaving of s1 and s2."""
    m, n = len(s1), len(s2)
    if m + n != len(s3):
        return False
    dp = [False] * (n + 1)
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 and j == 0:
                dp[j] = True
            elif i == 0:
                dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
            elif j == 0:
                dp[j] = dp[j] and s1[i - 1] == s3[i - 1]
            else:
                dp[j] = ((dp[j] and s1[i - 1] == s3[i + j - 1])
                         or (dp[j - 1] and s2[j - 1] == s3[i + j - 1]))
    return dp[n]


if __name__ == "__main__":
    assert is_interleave("aabcc", "dbbca", "aadbbcbcac") is True
    assert is_interleave("aabcc", "dbbca", "aadbbbaccc") is False
    assert is_interleave("", "", "") is True
    print("ok")
```

### `dp_2d/longest_common_subsequence.py`

```python
"""Longest Common Subsequence  |  tier: blind75, neetcode150  |  2-D DP

Return the length of the longest subsequence common to both strings (characters
in order, not necessarily contiguous).

Approach: dp[i][j] = LCS of text1[i:] and text2[j:]. If chars match, 1 + diagonal;
else max of skipping one char from either string. Use two rolling rows.
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def longest_common_subsequence(text1: str, text2: str) -> int:
    """Return the length of the longest common subsequence."""
    prev = [0] * (len(text2) + 1)
    for i in range(len(text1) - 1, -1, -1):
        curr = [0] * (len(text2) + 1)
        for j in range(len(text2) - 1, -1, -1):
            if text1[i] == text2[j]:
                curr[j] = 1 + prev[j + 1]
            else:
                curr[j] = max(prev[j], curr[j + 1])
        prev = curr
    return prev[0]


if __name__ == "__main__":
    assert longest_common_subsequence("abcde", "ace") == 3      # "ace"
    assert longest_common_subsequence("abc", "abc") == 3
    assert longest_common_subsequence("abc", "def") == 0
    print("ok")
```

### `dp_2d/longest_increasing_path_matrix.py`

```python
"""Longest Increasing Path in a Matrix  |  tier: neetcode150  |  2-D DP

Return the length of the longest strictly increasing path (moving 4-directionally)
in a matrix.

Approach: DFS with memoization. The longest path from a cell only depends on the
cell, so cache it. Strictly increasing moves mean no cycles, so no visited set is
needed.
Time: O(m * n)   Space: O(m * n)
"""
from __future__ import annotations

from functools import lru_cache


def longest_increasing_path(matrix: list[list[int]]) -> int:
    """Return the length of the longest strictly increasing path."""
    if not matrix:
        return 0
    rows, cols = len(matrix), len(matrix[0])

    @lru_cache(maxsize=None)
    def dfs(r: int, c: int) -> int:
        best = 1
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and matrix[nr][nc] > matrix[r][c]:
                best = max(best, 1 + dfs(nr, nc))
        return best

    return max(dfs(r, c) for r in range(rows) for c in range(cols))


if __name__ == "__main__":
    assert longest_increasing_path([[9, 9, 4], [6, 6, 8], [2, 1, 1]]) == 4   # 1,2,6,9
    assert longest_increasing_path([[3, 4, 5], [3, 2, 6], [2, 2, 1]]) == 4
    assert longest_increasing_path([[1]]) == 1
    print("ok")
```

### `dp_2d/regular_expression_matching.py`

```python
"""Regular Expression Matching  |  tier: neetcode150  |  2-D DP

Implement matching with '.' (any single char) and '*' (zero or more of the
preceding element), covering the ENTIRE string.

Approach: dp over (i, j) into text and pattern. '*' either skips the pattern pair
(zero occurrences) or, if the preceding element matches text[i], consumes one
text char and stays on the same pattern position. Memoize.
Time: O(m * n)   Space: O(m * n)
"""
from __future__ import annotations

from functools import lru_cache


def is_match(text: str, pattern: str) -> bool:
    """Return True if the pattern matches the whole text."""
    @lru_cache(maxsize=None)
    def dp(i: int, j: int) -> bool:
        if j == len(pattern):
            return i == len(text)
        first = i < len(text) and pattern[j] in (text[i], ".")
        if j + 1 < len(pattern) and pattern[j + 1] == "*":
            return dp(i, j + 2) or (first and dp(i + 1, j))   # zero, or one more
        return first and dp(i + 1, j + 1)

    return dp(0, 0)


if __name__ == "__main__":
    assert is_match("aa", "a") is False
    assert is_match("aa", "a*") is True
    assert is_match("ab", ".*") is True
    assert is_match("mississippi", "mis*is*p*.") is False
    print("ok")
```

### `dp_2d/target_sum.py`

```python
"""Target Sum  |  tier: neetcode150  |  2-D DP

Assign '+' or '-' to each number so the signed sum equals target. Return the
number of ways.

Approach: DP over running sums. Map each reachable sum to its number of ways;
each number branches every current sum into +num and -num.
Time: O(n * range)   Space: O(range)
"""
from __future__ import annotations

from collections import defaultdict


def find_target_sum_ways(nums: list[int], target: int) -> int:
    """Return the number of sign assignments yielding target."""
    ways: dict[int, int] = {0: 1}
    for num in nums:
        nxt: defaultdict[int, int] = defaultdict(int)
        for total, count in ways.items():
            nxt[total + num] += count
            nxt[total - num] += count
        ways = nxt
    return ways.get(target, 0)


if __name__ == "__main__":
    assert find_target_sum_ways([1, 1, 1, 1, 1], 3) == 5
    assert find_target_sum_ways([1], 1) == 1
    assert find_target_sum_ways([1], 2) == 0
    print("ok")
```

### `dp_2d/unique_paths.py`

```python
"""Unique Paths  |  tier: blind75, neetcode150  |  2-D DP

A robot at the top-left of an m x n grid moves only right or down. Count distinct
paths to the bottom-right.

Approach: paths to a cell = paths from above + paths from the left. Keep a single
row, updating in place; row[c] += row[c-1].
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def unique_paths(m: int, n: int) -> int:
    """Return the number of unique top-left to bottom-right paths."""
    row = [1] * n
    for _ in range(1, m):
        for c in range(1, n):
            row[c] += row[c - 1]
    return row[-1]


if __name__ == "__main__":
    assert unique_paths(3, 7) == 28
    assert unique_paths(3, 2) == 3
    assert unique_paths(1, 1) == 1
    print("ok")
```


---

## Greedy

### `greedy/gas_station.py`

```python
"""Gas Station  |  tier: neetcode150  |  Greedy

gas[i] is fuel at station i; cost[i] is fuel to reach the next. Return the
starting index to complete the circuit once, or -1.

Approach: a solution exists iff total gas >= total cost. Greedily, if the running
tank goes negative at station i, no start in [start..i] works -- restart from
i+1.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def can_complete_circuit(gas: list[int], cost: list[int]) -> int:
    """Return a valid starting station index, or -1."""
    if sum(gas) < sum(cost):
        return -1
    start = 0
    tank = 0
    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0:                     # can't reach i+1 from current start
            start = i + 1
            tank = 0
    return start


if __name__ == "__main__":
    assert can_complete_circuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3
    assert can_complete_circuit([2, 3, 4], [3, 4, 3]) == -1
    print("ok")
```

### `greedy/hand_of_straights.py`

```python
"""Hand of Straights  |  tier: neetcode150  |  Greedy

Can the hand be rearranged into groups of size groupSize, each group being
consecutive integers? Return True/False.

Approach: count cards. Repeatedly start a group at the smallest remaining card and
remove the next groupSize-1 consecutive values; if any is missing, fail. A min-heap
(or sorted counts) finds the smallest efficiently.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations

from collections import Counter


def is_n_straight_hand(hand: list[int], group_size: int) -> bool:
    """Return True if the hand splits into consecutive groups of group_size."""
    if len(hand) % group_size != 0:
        return False
    counts = Counter(hand)
    for start in sorted(counts):
        need = counts[start]
        if need <= 0:
            continue
        for card in range(start, start + group_size):
            if counts[card] < need:
                return False
            counts[card] -= need
    return True


if __name__ == "__main__":
    assert is_n_straight_hand([1, 2, 3, 6, 2, 3, 4, 7, 8], 3) is True
    assert is_n_straight_hand([1, 2, 3, 4, 5], 4) is False
    print("ok")
```

### `greedy/jump_game.py`

```python
"""Jump Game  |  tier: core50, blind75, neetcode150  |  Greedy

Each value is the max jump length from that index. Return True if you can reach
the last index from index 0.

Approach: greedy. Track the farthest reachable index while scanning. If the
current index ever exceeds it, you are stuck.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def can_jump(nums: list[int]) -> bool:
    """Return True if the last index is reachable."""
    farthest = 0
    for i, jump in enumerate(nums):
        if i > farthest:
            return False                 # cannot even reach index i
        farthest = max(farthest, i + jump)
    return True


if __name__ == "__main__":
    assert can_jump([2, 3, 1, 1, 4]) is True
    assert can_jump([3, 2, 1, 0, 4]) is False
    assert can_jump([0]) is True
    print("ok")
```

### `greedy/jump_game_ii.py`

```python
"""Jump Game II  |  tier: neetcode150  |  Greedy

Each value is the max jump length. Return the minimum number of jumps to reach the
last index (always reachable).

Approach: greedy BFS by "levels". Track the end of the current jump's reach; when
the scan passes it, take another jump and extend the reach to the farthest seen.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def jump(nums: list[int]) -> int:
    """Return the minimum number of jumps to reach the last index."""
    jumps = 0
    current_end = 0                      # boundary of the current jump
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:             # must jump now
            jumps += 1
            current_end = farthest
    return jumps


if __name__ == "__main__":
    assert jump([2, 3, 1, 1, 4]) == 2
    assert jump([2, 3, 0, 1, 4]) == 2
    assert jump([0]) == 0
    print("ok")
```

### `greedy/maximum_subarray.py`

```python
"""Maximum Subarray  |  tier: core50, blind75, neetcode150  |  Greedy

Return the largest sum of any contiguous subarray.

Approach: Kadane's algorithm. Track the best sum ending here: extend the previous
run or restart at the current element (whichever is larger). Keep the global max.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_sub_array(nums: list[int]) -> int:
    """Return the maximum contiguous subarray sum."""
    best = current = nums[0]
    for num in nums[1:]:
        current = max(num, current + num)    # restart vs extend
        best = max(best, current)
    return best


if __name__ == "__main__":
    assert max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6     # [4,-1,2,1]
    assert max_sub_array([1]) == 1
    assert max_sub_array([-3, -2, -1]) == -1
    print("ok")
```

### `greedy/merge_triplets.py`

```python
"""Merge Triplets to Form Target  |  tier: neetcode150  |  Greedy

You may take the element-wise max of any chosen triplets. Return True if the
target triplet can be formed.

Approach: a triplet is usable only if no component exceeds the target (else it
would overshoot). Among usable triplets, collect which positions already equal the
target value; success needs all three positions covered.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def merge_triplets(triplets: list[list[int]], target: list[int]) -> bool:
    """Return True if target can be built from element-wise maxes."""
    matched: set[int] = set()
    for triplet in triplets:
        if any(triplet[i] > target[i] for i in range(3)):
            continue                     # would overshoot -> unusable
        for i in range(3):
            if triplet[i] == target[i]:
                matched.add(i)
    return len(matched) == 3


if __name__ == "__main__":
    assert merge_triplets(
        [[2, 5, 3], [1, 8, 4], [1, 7, 5]], [2, 7, 5]
    ) is True
    assert merge_triplets([[3, 4, 5], [4, 5, 6]], [3, 2, 5]) is False
    print("ok")
```

### `greedy/partition_labels.py`

```python
"""Partition Labels  |  tier: neetcode150  |  Greedy

Partition the string into as many parts as possible so each letter appears in at
most one part. Return the sizes of the parts in order.

Approach: record each letter's last index. Scan, extending the current part's end
to the farthest last-index of any letter seen. When the scan reaches that end, cut
a partition.
Time: O(n)   Space: O(1)  (26 letters)
"""
from __future__ import annotations


def partition_labels(text: str) -> list[int]:
    """Return the sizes of the maximal non-overlapping letter partitions."""
    last = {ch: i for i, ch in enumerate(text)}
    sizes: list[int] = []
    start = end = 0
    for i, ch in enumerate(text):
        end = max(end, last[ch])
        if i == end:                     # every letter so far ends by here
            sizes.append(end - start + 1)
            start = i + 1
    return sizes


if __name__ == "__main__":
    assert partition_labels("ababcbacadefegdehijhklij") == [9, 7, 8]
    assert partition_labels("eccbbbbdec") == [10]
    print("ok")
```

### `greedy/valid_parenthesis_string.py`

```python
"""Valid Parenthesis String  |  tier: neetcode150  |  Greedy

'*' can be '(', ')', or empty. Return True if the string can be a valid sequence
of parentheses.

Approach: track the RANGE of possible open-paren counts [low, high]. '(' bumps
both; ')' drops both; '*' widens (low-1, high+1). Clamp low at 0; if high goes
negative there are too many ')'. Valid iff low can reach 0 at the end.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def check_valid_string(text: str) -> bool:
    """Return True if text can form a valid parenthesis sequence."""
    low = high = 0                       # min/max possible unmatched '('
    for ch in text:
        if ch == "(":
            low += 1
            high += 1
        elif ch == ")":
            low -= 1
            high -= 1
        else:                            # '*'
            low -= 1
            high += 1
        if high < 0:                     # too many ')'
            return False
        low = max(low, 0)
    return low == 0


if __name__ == "__main__":
    assert check_valid_string("()") is True
    assert check_valid_string("(*)") is True
    assert check_valid_string("(*))") is True
    assert check_valid_string(")(") is False
    print("ok")
```


---

## Intervals

### `intervals/insert_interval.py`

```python
"""Insert Interval  |  tier: blind75, neetcode150  |  Intervals

Insert a new interval into a sorted, non-overlapping list and merge as needed.

Approach: three phases -- append all intervals ending before the new one, merge
all that overlap it (expanding the new interval), then append the rest.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def insert(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    """Insert new_interval and return the merged interval list."""
    result: list[list[int]] = []
    i, n = 0, len(intervals)

    while i < n and intervals[i][1] < new_interval[0]:
        result.append(intervals[i])      # ends before new starts
        i += 1
    while i < n and intervals[i][0] <= new_interval[1]:
        new_interval[0] = min(new_interval[0], intervals[i][0])
        new_interval[1] = max(new_interval[1], intervals[i][1])
        i += 1
    result.append(new_interval)
    while i < n:
        result.append(intervals[i])
        i += 1
    return result


if __name__ == "__main__":
    assert insert([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
    assert insert([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]) == \
        [[1, 2], [3, 10], [12, 16]]
    assert insert([], [5, 7]) == [[5, 7]]
    print("ok")
```

### `intervals/meeting_rooms.py`

```python
"""Meeting Rooms  |  tier: blind75, neetcode150  |  Intervals

Given meeting intervals, return True if one person could attend all of them (no
two overlap).

Approach: sort by start; if any meeting begins before the previous one ends,
there is a conflict.
Time: O(n log n)   Space: O(1)
"""
from __future__ import annotations


def can_attend_meetings(intervals: list[list[int]]) -> bool:
    """Return True if no meetings overlap."""
    intervals.sort(key=lambda iv: iv[0])
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i - 1][1]:
            return False
    return True


if __name__ == "__main__":
    assert can_attend_meetings([[0, 30], [5, 10], [15, 20]]) is False
    assert can_attend_meetings([[7, 10], [2, 4]]) is True
    assert can_attend_meetings([]) is True
    print("ok")
```

### `intervals/meeting_rooms_ii.py`

```python
"""Meeting Rooms II  |  tier: blind75, neetcode150  |  Intervals

Return the minimum number of meeting rooms required so no meetings overlap in a
room.

Approach: separate and sort start and end times. Sweep: each start needs a room;
if a meeting has already ended (end <= current start), reuse its room. Track the
peak concurrent meetings.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations


def min_meeting_rooms(intervals: list[list[int]]) -> int:
    """Return the minimum number of rooms needed."""
    starts = sorted(interval[0] for interval in intervals)
    ends = sorted(interval[1] for interval in intervals)
    rooms = 0
    peak = 0
    end_idx = 0
    for start in starts:
        while end_idx < len(ends) and ends[end_idx] <= start:
            rooms -= 1                   # a meeting freed a room
            end_idx += 1
        rooms += 1
        peak = max(peak, rooms)
    return peak


if __name__ == "__main__":
    assert min_meeting_rooms([[0, 30], [5, 10], [15, 20]]) == 2
    assert min_meeting_rooms([[7, 10], [2, 4]]) == 1
    assert min_meeting_rooms([]) == 0
    print("ok")
```

### `intervals/merge_intervals.py`

```python
"""Merge Intervals  |  tier: core50, blind75, neetcode150  |  Intervals

Merge all overlapping intervals.

Approach: sort by start. Walk through; if the current interval overlaps the last
merged one (start <= last end), extend the last end; otherwise append a new
interval.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations


def merge(intervals: list[list[int]]) -> list[list[int]]:
    """Merge overlapping intervals and return the result."""
    intervals.sort(key=lambda iv: iv[0])
    merged: list[list[int]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


if __name__ == "__main__":
    assert merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge([[1, 4], [0, 4]]) == [[0, 4]]
    print("ok")
```

### `intervals/minimum_interval_query.py`

```python
"""Minimum Interval to Include Each Query  |  tier: neetcode150  |  Intervals

For each query, return the size of the smallest interval [start, end] with
start <= query <= end, or -1 if none contains the query.

Approach: sort intervals by start and queries ascending. Sweep queries; push every
interval that has started into a min-heap keyed by size. Pop intervals that have
already ended; the heap top is then the smallest interval covering the query.
Time: O((n + q) log(n + q))   Space: O(n)
"""
from __future__ import annotations

import heapq


def min_interval(intervals: list[list[int]], queries: list[int]) -> list[int]:
    """Return the smallest covering interval size for each query."""
    intervals.sort()
    heap: list[tuple[int, int]] = []     # (size, end)
    answer: dict[int, int] = {}
    i = 0
    for query in sorted(queries):
        while i < len(intervals) and intervals[i][0] <= query:
            start, end = intervals[i]
            heapq.heappush(heap, (end - start + 1, end))
            i += 1
        while heap and heap[0][1] < query:   # interval already ended
            heapq.heappop(heap)
        answer[query] = heap[0][0] if heap else -1
    return [answer[query] for query in queries]


if __name__ == "__main__":
    assert min_interval(
        [[1, 4], [2, 4], [3, 6], [4, 4]], [2, 3, 4, 5]
    ) == [3, 3, 1, 4]
    assert min_interval([[2, 3], [2, 5], [1, 8], [20, 25]], [2, 19, 5, 22]) == [2, -1, 4, 6]
    print("ok")
```

### `intervals/non_overlapping_intervals.py`

```python
"""Non-overlapping Intervals  |  tier: blind75, neetcode150  |  Intervals

Return the minimum number of intervals to remove so the rest do not overlap.

Approach: greedy. Sort by END time; always keep the interval that ends earliest
(leaves the most room). Count any interval whose start lies before the last kept
end as a removal.
Time: O(n log n)   Space: O(1)
"""
from __future__ import annotations


def erase_overlap_intervals(intervals: list[list[int]]) -> int:
    """Return the minimum number of intervals to remove."""
    intervals.sort(key=lambda iv: iv[1])
    removals = 0
    prev_end = float("-inf")
    for start, end in intervals:
        if start >= prev_end:            # no overlap -> keep
            prev_end = end
        else:
            removals += 1                # overlaps -> drop this one
    return removals


if __name__ == "__main__":
    assert erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1
    assert erase_overlap_intervals([[1, 2], [1, 2], [1, 2]]) == 2
    assert erase_overlap_intervals([[1, 2], [2, 3]]) == 0
    print("ok")
```


---

## Math & Geometry

### `math_geometry/detect_squares.py`

```python
"""Detect Squares  |  tier: neetcode150  |  Math & Geometry

Design a structure: add(point) and count(point) returning the number of
axis-aligned squares that can be formed using the query point as one corner plus
three previously added points.

Approach: keep a frequency count of points. For a query, iterate candidate
diagonal points (sharing neither x nor y, forming a square's opposite corner);
multiply the counts of the two remaining corners.
Time: add O(1); count O(n) over distinct points   Space: O(n)
"""
from __future__ import annotations

from collections import Counter


class DetectSquares:
    """Counts axis-aligned squares formed with stored points."""

    def __init__(self) -> None:
        self._counts: Counter[tuple[int, int]] = Counter()

    def add(self, point: list[int]) -> None:
        """Add a point (duplicates allowed)."""
        self._counts[(point[0], point[1])] += 1

    def count(self, point: list[int]) -> int:
        """Count squares using point plus three stored points."""
        px, py = point
        total = 0
        for (x, y), freq in list(self._counts.items()):
            if abs(x - px) == abs(y - py) and x != px and y != py:
                total += freq * self._counts[(px, y)] * self._counts[(x, py)]
        return total


if __name__ == "__main__":
    ds = DetectSquares()
    for point in ([3, 10], [11, 2], [3, 2]):
        ds.add(point)
    assert ds.count([11, 10]) == 1
    assert ds.count([14, 8]) == 0
    ds.add([11, 2])                      # second copy
    assert ds.count([11, 10]) == 2
    print("ok")
```

### `math_geometry/happy_number.py`

```python
"""Happy Number  |  tier: neetcode150  |  Math & Geometry

A number is happy if repeatedly replacing it with the sum of squares of its digits
eventually reaches 1. Return True if n is happy.

Approach: this is cycle detection. Use Floyd's slow/fast pointers over the
digit-square-sum sequence; reaching 1 means happy, meeting elsewhere means a loop.
Time: O(log n) per step   Space: O(1)
"""
from __future__ import annotations


def _next(n: int) -> int:
    total = 0
    while n:
        n, digit = divmod(n, 10)
        total += digit * digit
    return total


def is_happy(n: int) -> bool:
    """Return True if n is a happy number."""
    slow, fast = n, _next(n)
    while fast != 1 and slow != fast:
        slow = _next(slow)
        fast = _next(_next(fast))
    return fast == 1


if __name__ == "__main__":
    assert is_happy(19) is True          # 1+81=82 ... -> 1
    assert is_happy(2) is False
    assert is_happy(1) is True
    print("ok")
```

### `math_geometry/multiply_strings.py`

```python
"""Multiply Strings  |  tier: neetcode150  |  Math & Geometry

Multiply two non-negative integers given as strings, without using built-in big
integer conversion.

Approach: schoolbook multiplication. digit i times digit j contributes to result
positions i+j and i+j+1. Accumulate into an array, then handle carries and strip
leading zeros.
Time: O(m * n)   Space: O(m + n)
"""
from __future__ import annotations


def multiply(num1: str, num2: str) -> str:
    """Return the product of two non-negative integer strings."""
    if num1 == "0" or num2 == "0":
        return "0"
    m, n = len(num1), len(num2)
    product = [0] * (m + n)
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            mul = (ord(num1[i]) - 48) * (ord(num2[j]) - 48)
            low = i + j + 1
            total = mul + product[low]
            product[low] = total % 10
            product[low - 1] += total // 10      # carry up

    result = "".join(map(str, product)).lstrip("0")
    return result or "0"


if __name__ == "__main__":
    assert multiply("2", "3") == "6"
    assert multiply("123", "456") == "56088"
    assert multiply("0", "52") == "0"
    print("ok")
```

### `math_geometry/plus_one.py`

```python
"""Plus One  |  tier: neetcode150  |  Math & Geometry

Given a number as a digit array (most significant first), add one and return the
resulting digits.

Approach: walk from the least significant digit. A digit < 9 increments and we are
done; a 9 becomes 0 and carries. If every digit was 9, prepend a leading 1.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def plus_one(digits: list[int]) -> list[int]:
    """Increment the big-endian digit array by one."""
    for i in range(len(digits) - 1, -1, -1):
        if digits[i] < 9:
            digits[i] += 1
            return digits
        digits[i] = 0                    # carry
    return [1] + digits                  # all nines -> e.g. 999 -> 1000


if __name__ == "__main__":
    assert plus_one([1, 2, 3]) == [1, 2, 4]
    assert plus_one([4, 3, 9]) == [4, 4, 0]
    assert plus_one([9, 9, 9]) == [1, 0, 0, 0]
    print("ok")
```

### `math_geometry/pow_x_n.py`

```python
"""Pow(x, n)  |  tier: neetcode150  |  Math & Geometry

Compute x raised to the integer power n (n may be negative).

Approach: fast exponentiation by squaring. Halve the exponent each step, squaring
the base; multiply in the base on odd exponents. Invert for negative n.
Time: O(log n)   Space: O(1)
"""
from __future__ import annotations


def my_pow(x: float, n: int) -> float:
    """Return x ** n using exponentiation by squaring."""
    if n < 0:
        x = 1 / x
        n = -n
    result = 1.0
    while n:
        if n & 1:
            result *= x
        x *= x
        n >>= 1
    return result


if __name__ == "__main__":
    assert abs(my_pow(2.0, 10) - 1024.0) < 1e-9
    assert abs(my_pow(2.1, 3) - 9.261) < 1e-9
    assert abs(my_pow(2.0, -2) - 0.25) < 1e-9
    print("ok")
```

### `math_geometry/rotate_image.py`

```python
"""Rotate Image  |  tier: blind75, neetcode150  |  Math & Geometry

Rotate an n x n matrix 90 degrees clockwise, in place.

Approach: transpose the matrix (swap across the main diagonal), then reverse each
row. The two operations together produce a clockwise rotation.
Time: O(n^2)   Space: O(1)
"""
from __future__ import annotations


def rotate(matrix: list[list[int]]) -> None:
    """Rotate the matrix 90 degrees clockwise in place."""
    n = len(matrix)
    for r in range(n):                   # transpose
        for c in range(r + 1, n):
            matrix[r][c], matrix[c][r] = matrix[c][r], matrix[r][c]
    for row in matrix:                   # reverse each row
        row.reverse()


if __name__ == "__main__":
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    rotate(matrix)
    assert matrix == [[7, 4, 1], [8, 5, 2], [9, 6, 3]]
    single = [[1]]
    rotate(single)
    assert single == [[1]]
    print("ok")
```

### `math_geometry/set_matrix_zeroes.py`

```python
"""Set Matrix Zeroes  |  tier: blind75, neetcode150  |  Math & Geometry

If an element is 0, set its entire row and column to 0, in place, using O(1) extra
space.

Approach: use the first row and first column as marker storage. A separate flag
tracks whether the first column itself must be zeroed. Mark, then apply from the
inside out so markers are read before being overwritten.
Time: O(m * n)   Space: O(1)
"""
from __future__ import annotations


def set_zeroes(matrix: list[list[int]]) -> None:
    """Zero out rows/columns containing a 0, in place."""
    rows, cols = len(matrix), len(matrix[0])
    first_col_zero = False

    for r in range(rows):
        if matrix[r][0] == 0:
            first_col_zero = True
        for c in range(1, cols):
            if matrix[r][c] == 0:
                matrix[r][0] = 0         # mark row
                matrix[0][c] = 0         # mark column

    for r in range(1, rows):             # apply inner cells
        for c in range(1, cols):
            if matrix[r][0] == 0 or matrix[0][c] == 0:
                matrix[r][c] = 0
    if matrix[0][0] == 0:                # first row
        for c in range(cols):
            matrix[0][c] = 0
    if first_col_zero:                   # first column
        for r in range(rows):
            matrix[r][0] = 0


if __name__ == "__main__":
    matrix = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
    set_zeroes(matrix)
    assert matrix == [[1, 0, 1], [0, 0, 0], [1, 0, 1]]
    matrix2 = [[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]]
    set_zeroes(matrix2)
    assert matrix2 == [[0, 0, 0, 0], [0, 4, 5, 0], [0, 3, 1, 0]]
    print("ok")
```

### `math_geometry/spiral_matrix.py`

```python
"""Spiral Matrix  |  tier: blind75, neetcode150  |  Math & Geometry

Return all elements of an m x n matrix in spiral (clockwise) order.

Approach: maintain four boundaries (top, bottom, left, right). Traverse the top
row, right column, bottom row, left column; shrink the boundary after each and
repeat until they cross.
Time: O(m * n)   Space: O(1)  (excluding output)
"""
from __future__ import annotations


def spiral_order(matrix: list[list[int]]) -> list[int]:
    """Return matrix elements in spiral order."""
    result: list[int] = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            result.append(matrix[top][c])
        top += 1
        for r in range(top, bottom + 1):
            result.append(matrix[r][right])
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                result.append(matrix[bottom][c])
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                result.append(matrix[r][left])
            left += 1
    return result


if __name__ == "__main__":
    assert spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]
    assert spiral_order([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]) == \
        [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]
    print("ok")
```


---

## Bit Manipulation

### `bit_manipulation/counting_bits.py`

```python
"""Counting Bits  |  tier: blind75, neetcode150  |  Bit Manipulation

Return an array where ans[i] is the number of set bits in i, for i in 0..n.

Approach: DP. ans[i] = ans[i >> 1] + (i & 1) -- the bits of i are the bits of i//2
plus its lowest bit. Builds the whole table in one pass.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def count_bits(n: int) -> list[int]:
    """Return set-bit counts for every integer from 0 to n."""
    ans = [0] * (n + 1)
    for i in range(1, n + 1):
        ans[i] = ans[i >> 1] + (i & 1)
    return ans


if __name__ == "__main__":
    assert count_bits(2) == [0, 1, 1]
    assert count_bits(5) == [0, 1, 1, 2, 1, 2]
    assert count_bits(0) == [0]
    print("ok")
```

### `bit_manipulation/missing_number.py`

```python
"""Missing Number  |  tier: core50, blind75, neetcode150  |  Bit Manipulation

An array contains n distinct numbers from the range [0, n]. Return the missing one.

Approach: XOR all indices 0..n with all values. Each present value cancels with its
index; the leftover is the missing number. (Gauss sum n(n+1)/2 minus the array sum
also works.)
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def missing_number(nums: list[int]) -> int:
    """Return the missing number in [0, n]."""
    result = len(nums)                   # start with n (the index with no value)
    for i, num in enumerate(nums):
        result ^= i ^ num
    return result


if __name__ == "__main__":
    assert missing_number([3, 0, 1]) == 2
    assert missing_number([0, 1]) == 2
    assert missing_number([9, 6, 4, 2, 3, 5, 7, 0, 1]) == 8
    print("ok")
```

### `bit_manipulation/number_of_1_bits.py`

```python
"""Number of 1 Bits  |  tier: blind75, neetcode150  |  Bit Manipulation

Return the number of set bits (Hamming weight) of an unsigned integer.

Approach: Brian Kernighan's trick. n & (n - 1) clears the lowest set bit; count
how many times until n becomes 0 -- loops once per set bit, not per total bit.
Time: O(set bits)   Space: O(1)
"""
from __future__ import annotations


def hamming_weight(n: int) -> int:
    """Return the count of set bits in n."""
    count = 0
    while n:
        n &= n - 1                       # drop the lowest set bit
        count += 1
    return count


if __name__ == "__main__":
    assert hamming_weight(0b00000000000000000000000000001011) == 3
    assert hamming_weight(0b10000000000000000000000000000000) == 1
    assert hamming_weight(0) == 0
    print("ok")
```

### `bit_manipulation/reverse_bits.py`

```python
"""Reverse Bits  |  tier: blind75, neetcode150  |  Bit Manipulation

Reverse the bits of a 32-bit unsigned integer.

Approach: shift the result left and OR in the input's lowest bit, 32 times. Each
step peels one bit off the input and appends it to the (reversed) output.
Time: O(32)   Space: O(1)
"""
from __future__ import annotations


def reverse_bits(n: int) -> int:
    """Return the 32-bit reversal of n."""
    result = 0
    for _ in range(32):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result


if __name__ == "__main__":
    assert reverse_bits(0b00000010100101000001111010011100) == 964176192
    assert reverse_bits(0b11111111111111111111111111111101) == 3221225471
    print("ok")
```

### `bit_manipulation/reverse_integer.py`

```python
"""Reverse Integer  |  tier: neetcode150  |  Bit Manipulation

Reverse the digits of a signed 32-bit integer. Return 0 if the result overflows
the signed 32-bit range [-2^31, 2^31 - 1].

Approach: pop digits with divmod and push onto the reversed value, checking the
32-bit bound before it is exceeded. Handle the sign separately.
Time: O(digits)   Space: O(1)
"""
from __future__ import annotations

INT_MIN, INT_MAX = -(2 ** 31), 2 ** 31 - 1


def reverse(x: int) -> int:
    """Return x with its digits reversed, or 0 on 32-bit overflow."""
    sign = -1 if x < 0 else 1
    x = abs(x)
    result = 0
    while x:
        x, digit = divmod(x, 10)
        result = result * 10 + digit
    result *= sign
    return result if INT_MIN <= result <= INT_MAX else 0


if __name__ == "__main__":
    assert reverse(123) == 321
    assert reverse(-123) == -321
    assert reverse(120) == 21
    assert reverse(1534236469) == 0      # overflow
    print("ok")
```

### `bit_manipulation/single_number.py`

```python
"""Single Number  |  tier: core50, blind75, neetcode150  |  Bit Manipulation

Every element appears twice except one. Find the single element in O(n) time and
O(1) space.

Approach: XOR all elements. x ^ x == 0 and x ^ 0 == x, so paired values cancel and
the lone value remains.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from functools import reduce
from operator import xor


def single_number(nums: list[int]) -> int:
    """Return the element that appears exactly once."""
    return reduce(xor, nums)


if __name__ == "__main__":
    assert single_number([2, 2, 1]) == 1
    assert single_number([4, 1, 2, 1, 2]) == 4
    assert single_number([7]) == 7
    print("ok")
```

### `bit_manipulation/sum_of_two_integers.py`

```python
"""Sum of Two Integers  |  tier: blind75, neetcode150  |  Bit Manipulation

Add two integers without using + or -.

Approach: XOR gives the sum without carries; AND << 1 gives the carries. Repeat
until there is no carry. Python ints are unbounded, so mask to 32 bits each step
and reinterpret the sign at the end.
Time: O(1)  (<= 32 iterations)   Space: O(1)
"""
from __future__ import annotations

MASK = 0xFFFFFFFF
INT_MAX = 0x7FFFFFFF


def get_sum(first: int, second: int) -> int:
    """Return first + second using only bitwise operations."""
    while second & MASK:
        carry = (first & second) << 1
        first = first ^ second
        second = carry
    first &= MASK
    # interpret the masked result as a signed 32-bit integer
    return first if first <= INT_MAX else ~(first ^ MASK)


if __name__ == "__main__":
    assert get_sum(1, 2) == 3
    assert get_sum(2, 3) == 5
    assert get_sum(-2, 3) == 1
    assert get_sum(-1, -1) == -2
    print("ok")
```

