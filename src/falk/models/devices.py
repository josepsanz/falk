import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import (
    DynamicMapped,
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base


class SmartSwitch(Base):
    __tablename__ = "smart_switch"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    brand: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    location: Mapped[str | None] = mapped_column(String(50))

    __mapper_args__ = {
        "polymorphic_on": device_type,
        "polymorphic_identity": "base",
    }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.brand} {self.model}>"

    metrics: DynamicMapped["SwitchMetric"] = relationship(
        "SwitchMetric",
        back_populates="smart_switch",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TuyaSwitch(SmartSwitch):
    __tablename__ = "tuya_switch"

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("smart_switch.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tuya_id: Mapped[str] = mapped_column(String(50), nullable=False)
    local_key: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(16), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "tuya_switch_type"}


class SwitchMetric(Base):
    __tablename__ = "switch_metric"

    __table_args__ = (
        Index("ix_switch_metric_switch_time", "switch_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    switch_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("smart_switch.id", ondelete="CASCADE"),
        nullable=False,
    )
    current: Mapped[int] = mapped_column(Integer, nullable=False)
    voltage: Mapped[float] = mapped_column(Float(precision=2), nullable=False)
    power: Mapped[float] = mapped_column(Float(precision=2), nullable=False)
    recorded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False
    )

    smart_switch: Mapped["SmartSwitch"] = relationship(
        "SmartSwitch", back_populates="metrics"
    )


class EnergyMeter(Base):
    __tablename__ = "energy_meter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    brand: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    location: Mapped[str | None] = mapped_column(String(50))

    __mapper_args__ = {
        "polymorphic_on": device_type,
        "polymorphic_identity": "base",
    }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.brand} {self.model}>"

    metrics: DynamicMapped["EMMetric"] = relationship(
        "EMMetric",
        back_populates="energy_meter",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ShellyEM(EnergyMeter):
    __tablename__ = "shelly_em"

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("energy_meter.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __mapper_args__ = {"polymorphic_identity": "shelly_em_type"}

    shelly_id: Mapped[str] = mapped_column(String(50), nullable=False)


class EMMetric(Base):
    __tablename__ = "em_metric"

    __table_args__ = (Index("ix_em_metric_time", "em_id", "recorded_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    em_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("energy_meter.id", ondelete="CASCADE"),
        nullable=False,
    )
    total_act_power: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    total_aprt_power: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    total_current: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    total_act_energy: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    total_act_ret_energy: Mapped[float] = mapped_column(
        Float(precision=3), nullable=False
    )
    recorded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False
    )

    energy_meter: Mapped["EnergyMeter"] = relationship(
        "EnergyMeter", back_populates="metrics"
    )
    phases: Mapped[list["Phase"]] = relationship(
        "Phase",
        back_populates="em_metric",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Phase(Base):
    __tablename__ = "energy_phase"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    em_metric_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("em_metric.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(10), nullable=False)
    current: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    voltage: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    act_power: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    aprt_power: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    freq: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    pf: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    total_act_energy: Mapped[float] = mapped_column(Float(precision=3), nullable=False)
    total_act_ret_energy: Mapped[float] = mapped_column(
        Float(precision=3), nullable=False
    )

    em_metric: Mapped["EMMetric"] = relationship(
        "EMMetric", back_populates="phases"
    )
