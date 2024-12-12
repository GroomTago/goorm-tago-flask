from app import db
from datetime import datetime

class TaxiReservation(db.Model):
    __tablename__ = 'taxi_reservations'

    id = db.Column(db.Integer, primary_key=True)
    starting_point = db.Column(db.String(255), nullable=False)
    arrival_point = db.Column(db.String(255), nullable=False)
    reservation_phone_number = db.Column(db.String(255), nullable=False)
    reservation_datetime = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TaxiReservation {self.id}: {self.starting_point} -> {self.arrival_point}>'
