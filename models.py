from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Design(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.String(300), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
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