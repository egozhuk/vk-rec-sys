import pickle
from collections import deque
from .recommender import Recommender

class CustomRecommender(Recommender):
    def __init__(self, recommendations_redis, *, fallback: Recommender, memory_size=5):
        self.recommendations_redis = recommendations_redis
        self.fallback = fallback
        self.user_history = {}
        self.memory_size = memory_size

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        data = self.recommendations_redis.get(user)
        if not data:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        recs = pickle.loads(data)
        if not recs:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        try:
            idx = recs.index(prev_track)
        except ValueError:
            idx = 0

        if prev_track_time < 1.0:
            step = 3
        elif prev_track_time < 5.0:
            step = 2
        else:
            step = 1

        history = self.user_history.setdefault(user, deque(maxlen=self.memory_size))
        for offset in range(len(recs)):
            next_idx = (idx + step + offset) % len(recs)
            candidate = recs[next_idx]
            if candidate not in history:
                history.append(candidate)
                return candidate

        return self.fallback.recommend_next(user, prev_track, prev_track_time)