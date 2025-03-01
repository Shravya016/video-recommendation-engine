from app.utils import fetch_all_users, fetch_all_posts, fetch_interactions
from app.models import User, Post, Interaction
from app.database import SessionLocal

def populate_db():
    db = SessionLocal()
    
    # Users
    users = fetch_all_users()
    for u in users:
        db.merge(User(id=u["id"], username=u["username"]))
    db.commit()
    
    # Posts
    posts = fetch_all_posts()
    for p in posts:
        db.merge(Post(id=p["id"], category_id=p.get("category_id", 0)))
    db.commit()
    
    # Interactions
    for itype in ["view", "like", "inspire", "rate"]:
        interactions = fetch_interactions(itype)
        for i in interactions:
            db.merge(Interaction(
                user_id=i["user_id"],
                post_id=i["post_id"],
                interaction_type=itype,
                rating=i.get("rating") if itype == "rate" else None
            ))
    db.commit()
    db.close()

if __name__ == "__main__":
    populate_db()