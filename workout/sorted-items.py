from collections import defaultdict
from heapq import nlargest
from pprint import pprint

class BookRecommender:
    """Computes reader similarity and generates personalized book recommendations."""
    
    def __init__(self):
        # Maps user_id to set of books they've read
        self.user_books = defaultdict(set)
        # Maps book_id to set of users who've read it
        self.book_readers = defaultdict(set)
    
    def add_reading_history(self, user_id, books):
        """Record the set of books a user has read."""
        self.user_books[user_id] = set(books)
        for book in books:
            self.book_readers[book].add(user_id)
    
    def jaccard_similarity(self, user_a, user_b):
        """Calculate Jaccard similarity between two users' reading histories."""
        books_a = self.user_books[user_a]
        books_b = self.user_books[user_b]
        
        if not books_a or not books_b:
            return 0.0
        
        intersection = len(books_a & books_b)
        union = len(books_a | books_b)
        
        # BUG: using union size in numerator instead of intersection
        similarity = intersection / union if union > 0 else 0.0
        return similarity
    
    def find_similar_readers(self, user_id, min_similarity=0.3):
        """Return set of readers with similarity >= min_similarity to user_id."""
        similar = set()
        for other_user in self.user_books:
            if other_user != user_id:
                sim = self.jaccard_similarity(user_id, other_user)
                if sim >= min_similarity:
                    similar.add(other_user)
        return similar

    def get_recommendations(self, user_id, n):
        """Return the recommendations based on expected similarity."""
        expected_similarity = 0.3  
              
        if user_id not in self.user_books:
            return []
        my_books = self.user_books.get(user_id) 
        counts = defaultdict(int)

        # pprint(self.user_books)
        # print("*"*80)
        pprint(self.book_readers)

        for other_user in self.user_books:
            if other_user == user_id:
                continue
            similarity = self.jaccard_similarity(user_id, other_user)
            if similarity >= expected_similarity:
                for book in self.user_books.get(other_user):
                    if book not in my_books:
                        counts[book] += 1
        recommendations = list(counts.items())
        recommendations.sort(key=lambda x: (-x[1], x[0]))
        return recommendations[:n]

def main():
    # Initialize recommender engine
    engine = BookRecommender()
    
    # User U001: read ["The Great Gatsby", "1984", "To Kill a Mockingbird"]
    engine.add_reading_history('U001', ['The Great Gatsby', '1984', 'To Kill a Mockingbird'])
    
    # User U002: read ["The Great Gatsby", "1984"] — 2/3 overlap with U001
    engine.add_reading_history('U002', ['The Great Gatsby', '1984'])
    
    # User U003: read ["Brave New World", "Fahrenheit 451"] — 0 overlap with U001
    engine.add_reading_history('U003', ['Brave New World', 'Fahrenheit 451'])
    
    # User U004: read ["The Great Gatsby", "1984", "To Kill a Mockingbird", "Pride and Prejudice"] — 3/4 overlap
    engine.add_reading_history('U004', ['The Great Gatsby', '1984', 'To Kill a Mockingbird', 'Pride and Prejudice'])
    
    # Jaccard(U001, U002) = |{Gatsby, 1984}| / |{Gatsby, 1984, Mockingbird}| = 2/3 ≈ 0.667
    assert engine.jaccard_similarity('U001', 'U002') == 2.0 / 3.0, "U001-U002 similarity should be 2/3"
    
    # Jaccard(U001, U003) = |{}| / |{Gatsby, 1984, Mockingbird, Brave New World, Fahrenheit 451}| = 0/5 = 0.0
    assert engine.jaccard_similarity('U001', 'U003') == 0.0, "U001-U003 similarity should be 0"
    
    # Jaccard(U001, U004) = |{Gatsby, 1984, Mockingbird}| / |{Gatsby, 1984, Mockingbird, Pride and Prejudice}| = 3/4 = 0.75
    assert engine.jaccard_similarity('U001', 'U004') == 3.0 / 4.0, "U001-U004 similarity should be 3/4"
    
    # With min_similarity=0.5, only U002 (0.667) and U004 (0.75) should be similar to U001
    similar = engine.find_similar_readers('U001', min_similarity=0.5)
    assert similar == {'U002', 'U004'}, "Readers with similarity >= 0.5 to U001 should be U002 and U004"


    # -------------------------------------------------------------------------------------------------------------
    # Part B
    # re-initialize the engine
    engine = BookRecommender()

    engine.add_reading_history('U001', ['The Great Gatsby', '1984', 'To Kill a Mockingbird'])
    engine.add_reading_history('U002', ['The Great Gatsby', '1984'])
    engine.add_reading_history('U005', ['The Great Gatsby', '1984', 'Dune'])

    recs = engine.get_recommendations('U001', 5)
    assert recs == [('Dune', 1)], "U001 should be recommended Dune from similar readers"

    engine.add_reading_history('U006', ['1984', 'To Kill a Mockingbird', 'Dune', 'Foundation'])
    recs = engine.get_recommendations('U001', 5)
    assert len(recs) == 2, "U001 should have 2 book recommendations"
    assert recs[0][0] == 'Dune', "Dune should be top recommendation (2 readers)"
    assert recs[1][0] == 'Foundation', "Foundation should be second (1 reader)"

    engine.add_reading_history('U003', ['Brave New World'])
    recs = engine.get_recommendations('U003', 5)
    assert recs == [], "User with no similar readers should get empty recommendations"

    recs = engine.get_recommendations('U001', 1)
    assert len(recs) == 1, "Should return at most n recommendations"
    assert recs[0][0] == 'Dune', "Top recommendation should be Dune"

if __name__ == '__main__':
    main()
    print('All tests passed!')