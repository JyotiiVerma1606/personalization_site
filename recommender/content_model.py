from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .items_data import ITEMS


class ContentRecommender:
    def __init__(self, items):
        self.items = items
        self.ids = [item["id"] for item in items]
        self._id_to_index = {item_id: idx for idx, item_id in enumerate(self.ids)}

        corpus = [self._to_document(item) for item in items]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.item_matrix = self.vectorizer.fit_transform(corpus)

    def _to_document(self, item):
        tags = " ".join(item.get("tags", []))
        return f"{item['category']} {item['category']} {tags} {item['title']} {item['body']}"

    def recommend(self, clicked_ids):
        clicked_ids = [i for i in clicked_ids if i in self._id_to_index]
        if not clicked_ids:
            return list(self.ids)

        counts = Counter(clicked_ids)
        idxs = [self._id_to_index[i] for i in counts]
        weights = np.array([counts[self.ids[idx]] for idx in idxs]).reshape(-1, 1)

        clicked_vectors = self.item_matrix[idxs]
        profile_vector = np.asarray(clicked_vectors.multiply(weights).mean(axis=0))

        scores = cosine_similarity(profile_vector, self.item_matrix).flatten()
        ranked = sorted(zip(self.ids, scores), key=lambda pair: pair[1], reverse=True)
        return [item_id for item_id, _score in ranked]


# Ek hi instance banao, poore app mein reuse hoga (baar baar train nahi hoga)
recommender = ContentRecommender(ITEMS)