from sqlalchemy import Boolean
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class SmartSwitch(Base):
    __tablename__ = "smart_switch"

    id = Column(Integer, primary_key=True)
    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    state = Column(Boolean, nullable=False, default=False)
    name = Column(String(50), nullable=False)
    ip = Column(String(50), nullable=True, default=None)
    location = Column(String(50))

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "base"
    }

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.brand} {self.model}>"

    metrics = relationship(
        "SwitchMetric",
        back_populates="smart_switch",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class TuyaSwitch(SmartSwitch):
    __tablename__ = "tuya_switch"

    id = Column(
        Integer, 
        ForeignKey("smart_switch.id", ondelete="CASCADE"), 
        primary_key=True
    )
    tuya_id = Column(String(50), nullable=False)
    local_key = Column(String(50), nullable=False)
    version = Column(Float, nullable=False)
    

    __mapper_args__ = {
        "polymorphic_identity": "tuya"
    }
    

class SwitchMetric(Base):
    __tablename__ = "switch_metric"

    __table_args__ = (
        Index(
            "ix_switch_metric_switch_time",
            "switch_id",
            "recorded_at"
        ),
    )

    id = Column(Integer, primary_key=True)
    switch_id = Column(
        Integer,
        ForeignKey("smart_switch.id", ondelete="CASCADE"),
        nullable=False
    )
    current = Column(Float, nullable=False)
    voltage = Column(Float, nullable=False)
    power = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False)

    smart_switch = relationship(
        "SmartSwitch",
        back_populates="metrics"
    )    
