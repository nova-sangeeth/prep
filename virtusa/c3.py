class StreamingRecommender:
    def __init__(self, viewing_data: dict[str, list]):
        # viewing_data format: {"user1": ["show_A", "show_B"], "user2": ["show_B", "show_C"]}
        self.viewing_data = viewing_data

    def calculate_jaccard_similarity(self, user_a: str, user_b: str) -> float:
        """Calculates Jaccard similarity: size of intersection divided by size of union."""
        shows_a = self.viewing_data.get(user_a, [])
        shows_b = self.viewing_data.get(user_b, [])
        
        set_a = set(shows_a)
        set_b = set(shows_b)
        
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        
        # Calculate similarity score
        similarity = intersection / union
        return similarity

    def add_viewing_history(self, user: str, show_id: str):
        """Adds a newly watched show to a user's history."""
        self.viewing_data[user].append(show_id)