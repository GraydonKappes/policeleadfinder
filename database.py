from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Text, String, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import ENUM
from enum import Enum as PyEnum
from sqlalchemy.types import TypeDecorator, Enum as SQLAlchemyEnum

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class EnumAsStr(TypeDecorator):
    impl = SQLAlchemyEnum
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.value

# Enums
class CasePriority(PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class CaseStatus(PyEnum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    LOST = "LOST"

# Define valid injury statuses
INJURY_STATUSES = [
    'No apparent injury',
    'Suspected minor injury',
    'Suspected serious injury',
    'Fatal injury',
    'Not specified'
]

injury_status_enum = ENUM(*INJURY_STATUSES, name='injury_status')

# Models
class CrashReport(Base):
    __tablename__ = "crash_reports"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    incident_summary = Column(Text, nullable=False)
    crash_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    processed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    vehicles = relationship("Vehicle", back_populates="crash_report", cascade="all, delete-orphan")

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'))
    status = Column(EnumAsStr(CaseStatus), default=CaseStatus.NEW)
    priority = Column(EnumAsStr(CasePriority))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="case")

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True)
    crash_report_id = Column(Integer, ForeignKey('crash_reports.id', ondelete='CASCADE'))
    vehicle_number = Column(Integer, nullable=False)
    owner_name = Column(String(255), nullable=False)
    owner_address = Column(Text, nullable=False)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=True)
    damage = Column(Text, nullable=False)
    injuries = Column(injury_status_enum, nullable=False)
    insurance_company = Column(String(255), nullable=True)
    insurance_policy_number = Column(String(100), nullable=True)
    towing_company = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    crash_report = relationship("CrashReport", back_populates="vehicles")
    case = relationship("Case", back_populates="vehicle", uselist=False)

def init_db():
    Base.metadata.create_all(bind=engine)

# Call it immediately when the module is imported
init_db()