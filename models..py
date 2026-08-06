import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from database import Base

class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=False)
    hourly_rate = Column(Float, nullable=False)  # Ставка в час (сум)
    face_encoding = Column(LargeBinary, nullable=False)  # Вектор лица в байтах

    shifts = relationship("Shift", back_populates="worker")

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    check_in = Column(DateTime, default=datetime.datetime.now)
    check_out = Column(DateTime, nullable=True)
    hours_worked = Column(Float, default=0.0)
    earned_amount = Column(Float, default=0.0)

    worker = relationship("Worker", back_populates="shifts")