from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

class Car(db.Model):
    __tablename__ = 'cars'

    id = db.Column(db.Integer, primary_key=True)
    listing_number = db.Column(db.String, nullable=False, index=True)
    brand = db.Column(db.String, nullable=False, index=True)
    model = db.Column(db.String, nullable=False, index=True)
    engine_capacity = db.Column(db.Integer, nullable=False)
    power = db.Column(db.Integer, nullable=False)
    fuel_type = db.Column(db.String, nullable=False, index=True)
    transmission = db.Column(db.String, nullable=False, index=True)
    mileage = db.Column(db.Integer, nullable=False)
    first_registration = db.Column(db.String, nullable=False)
    features = db.Column(db.String, nullable=False)
    eco_badge = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False, index=True)
    vat_deductible = db.Column(db.Boolean, nullable=False)
    seller = db.Column(db.String, nullable=False, server_default='Auto Berndl', index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), index=True)
    in_stock = db.Column(db.Boolean, nullable=False, server_default='1', index=True)  # True = im Bestand, False = verkauft

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
