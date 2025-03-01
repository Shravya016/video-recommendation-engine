import tensorflow as tf
import tensorflow_recommenders as tfrs
from app.database import SessionLocal
from app.models import User, Post, Interaction

def train_and_save_model():
    db = SessionLocal()
    
    # Load data
    interactions = db.query(Interaction).all()
    unique_users = [u.id for u in db.query(User.id).distinct()]
    unique_posts = [p.id for p in db.query(Post.id).distinct()]
    db.close()
    
    # Prepare dataset
    user_ids = [i.user_id for i in interactions]
    post_ids = [i.post_id for i in interactions]
    dataset = tf.data.Dataset.from_tensor_slices({
        "user_id": tf.constant(user_ids, dtype=tf.int32),
        "post_id": tf.constant(post_ids, dtype=tf.int32)
    }).shuffle(10000).batch(256).cache()
    
    posts_dataset = tf.data.Dataset.from_tensor_slices(tf.constant(unique_posts, dtype=tf.int32)).batch(128)
    
    # Define models
    class UserModel(tf.keras.Model):
        def __init__(self):
            super().__init__()
            self.embedding = tf.keras.Sequential([
                tf.keras.layers.IntegerLookup(vocabulary=unique_users, mask_token=None),
                tf.keras.layers.Embedding(len(unique_users) + 1, 32)
            ])
        def call(self, inputs):
            return self.embedding(inputs)
    
    class PostModel(tf.keras.Model):
        def __init__(self):
            super().__init__()
            self.embedding = tf.keras.Sequential([
                tf.keras.layers.IntegerLookup(vocabulary=unique_posts, mask_token=None),
                tf.keras.layers.Embedding(len(unique_posts) + 1, 32)
            ])
        def call(self, inputs):
            return self.embedding(inputs)
    
    user_model = UserModel()
    post_model = PostModel()
    
    # Define recommendation model
    class RecModel(tfrs.Model):
        def __init__(self):
            super().__init__()
            self.user_model = user_model
            self.post_model = post_model
            self.task = tfrs.tasks.Retrieval(
                metrics=tfrs.metrics.FactorizedTopK(candidates=posts_dataset.map(post_model))
            )
        def compute_loss(self, features, training=False):
            user_emb = self.user_model(features["user_id"])
            post_emb = self.post_model(features["post_id"])
            return self.task(user_emb, post_emb)
    
    model = RecModel()
    model.compile(optimizer=tf.keras.optimizers.Adagrad(0.1))
    model.fit(dataset, epochs=5)
    
    # Build and save index
    index = tfrs.layers.factorized_top_k.BruteForce(user_model)
    index.index_from_dataset(
        tf.data.Dataset.zip((posts_dataset, posts_dataset.map(post_model)))
    )
    tf.saved_model.save(index, "recommendation_index")

if __name__ == "__main__":
    train_and_save_model()