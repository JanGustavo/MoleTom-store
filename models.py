from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class Design(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    prompt = db.Column(db.String(300), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class CommunityDesign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    design_id = db.Column(db.Integer, db.ForeignKey("design.id"), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    caption = db.Column(db.String(280), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    votes_count = db.Column(db.Integer, nullable=False, default=0)
    curator_note = db.Column(db.String(280), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class CommunityVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community_design_id = db.Column(db.Integer, db.ForeignKey("community_design.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint("community_design_id", "user_id", name="ux_vote_design_user"),
    )

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    design_id = db.Column(db.Integer, db.ForeignKey("design.id"), nullable=False)
    preco = db.Column(db.Float)
    status = db.Column(db.String(50), default="Pendente")
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)