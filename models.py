from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=False)
    hourly_rate = Column(Float, nullable=False)
    photo_path = Column(String, nullable=True)

    shifts = relationship("Shift", back_populates="worker")

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    check_in = Column(DateTime, default=datetime.utcnow)
    check_out = Column(DateTime, nullable=True)
    total_hours = Column(Float, default=0.0)
    total_salary = Column(Float, default=0.0)

    worker = relationship("Worker", back_populates="shifts")