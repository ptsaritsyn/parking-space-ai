from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    surname = Column(String)
    car_number = Column(String)
    email = Column(String, unique=True, nullable=True)
    reservations = relationship("Reservation", back_populates="user")


class Spot(Base):
    __tablename__ = "spots"
    id = Column(Integer, primary_key=True)
    number = Column(String, unique=True)
    status = Column(String)  # "free" / "reserved"
    reservations = relationship("Reservation", back_populates="spot")


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    spot_id = Column(Integer, ForeignKey("spots.id"))
    reservation_from = Column(DateTime)
    reservation_to = Column(DateTime)
    user = relationship("User", back_populates="reservations")
    spot = relationship("Spot", back_populates="reservations")
