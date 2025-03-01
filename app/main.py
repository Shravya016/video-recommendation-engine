from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal, get_db
from app.models import User, Post, Interaction
import tensorflow as tf

app = FastAPI()
index = tf.saved_model.load("recommendation_index")

def get_popular_posts(db: Session, category_id: int = None, limit: int = 10):
    query = db.query(Post, func.count(Interaction.id).label("count")) \
              .outerjoin(Interaction) \
              .group_by(Post.id) \
              .order_by(func.count(Interaction.id).desc())
    if category_id is not None:
        query = query.filter(Post.category_id == category_id)
    return query.limit(limit).all()

@app.get("/feed")
def get_feed(username: str, category_id: int = None, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cold start check
    interaction_count = db.query(Interaction).filter(Interaction.user_id == user.id).count()
    if interaction_count == 0:
        popular = get_popular_posts(db, category_id)
        return {"posts": [p.id for p, _ in popular]}
    
    # Personalized recommendations
    _, recs = index(tf.constant([user.id], dtype=tf.int32))
    rec_ids = recs[0, :100].numpy().tolist()
    query = db.query(Post).filter(Post.id.in_(rec_ids))
    if category_id is not None:
        query = query.filter(Post.category_id == category_id)
    posts = query.limit(10).all()
    return {"posts": [p.id for p in posts]}