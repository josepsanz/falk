import datetime

from sqlalchemy import Boolean
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from .base import Base


class SmartSwitch(Base):
    __tablename__ = "smart_switch"

    id = Column(Integer, primary_key=True)
    device_type = Column(String(50), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)

    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    state = Column(Boolean, nullable=False, default=False)
    name = Column(String(50), nullable=False)
    ip = Column(String(50), nullable=True, default=None)
    location = Column(String(50))

    __mapper_args__ = {
        "polymorphic_on": device_type,
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
    version = Column(String(16), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "tuya_switch_type"
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
    current = Column(Integer, nullable=False)
    voltage = Column(Float(precision=2), nullable=False)
    power = Column(Float(precision=2), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=datetime.datetime.now, nullable=False)

    smart_switch = relationship(
        "SmartSwitch",
        back_populates="metrics"
    )


class EnergyMeter(Base):
    __tablename__ = "energy_meter"

    id = Column(Integer, primary_key=True)
    device_type = Column(String(50), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    name = Column(String(50), nullable=False)
    ip = Column(String(50), nullable=True, default=None)
    location = Column(String(50))

    __mapper_args__ = {
        "polymorphic_on": device_type,
        "polymorphic_identity": "base"
    }

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.brand} {self.model}>"

    metrics = relationship(
        "EMMetric",
        back_populates="energy_meter",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class ShellyEM(EnergyMeter):
    __tablename__ = "shelly_em"

    id = Column(
        Integer,
        ForeignKey("energy_meter.id", ondelete="CASCADE"),
        primary_key=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "shelly_em_type"
    }

    shelly_id = Column(String(50), nullable=False)


class EMMetric(Base):
    __tablename__ = "em_metric"

    __table_args__ = (
        Index(
            "ix_em_metric_time",
            "em_id",
            "recorded_at"
        ),
    )

    id = Column(Integer, primary_key=True)
    em_id = Column(
        Integer,
        ForeignKey("energy_meter.id", ondelete="CASCADE"),
        nullable=False
    )
    total_act_power = Column(Float(precision=3), nullable=False)
    total_aprt_power = Column(Float(precision=3), nullable=False)
    total_current = Column(Float(precision=3), nullable=False)
    total_act_energy = Column(Float(precision=3), nullable=False)
    total_act_ret_energy = Column(Float(precision=3), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=datetime.datetime.now, nullable=False)

    energy_meter = relationship(
        "EnergyMeter",
        back_populates="metrics"
    )
    phases = relationship(
        "Phase",
        back_populates="em_metric",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Phase(Base):
    __tablename__ = "energy_phase"

    id = Column(Integer, primary_key=True)
    em_metric_id = Column(
        Integer,
        ForeignKey("em_metric.id", ondelete="CASCADE"),
        nullable=False
    )
    name = Column(String(10), nullable=False)
    current = Column(Float(precision=3), nullable=False)
    voltage = Column(Float(precision=3), nullable=False)
    act_power = Column(Float(precision=3), nullable=False)
    aprt_power = Column(Float(precision=3), nullable=False)
    freq = Column(Float(precision=3), nullable=False)
    pf = Column(Float(precision=3), nullable=False)
    total_act_energy = Column(Float(precision=3), nullable=False)
    total_act_ret_energy = Column(Float(precision=3), nullable=False)

    em_metric = relationship(
        "EMMetric",
        back_populates="phases"
    )
