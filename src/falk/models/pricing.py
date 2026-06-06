"""SQLAlchemy ORM model for ESIOS hourly PVPC electricity price data."""

from __future__ import annotations

import datetime

from sqlalchemy import Date, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class EsiosPrice(Base):
    """Hourly PVPC electricity price breakdown sourced from REE/ESIOS archive 71.

    One row per (date, hour). Monetary components are in €/MWh unless the
    column comment states otherwise. ``price_kwh`` is the consumer-facing
    price in €/kWh derived as ``feu / 1000``.
    """

    __tablename__ = "esios_price"

    __table_args__ = (
        UniqueConstraint("date", "hour", name="uq_esios_price_date_hour"),
        Index("ix_esios_price_date", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
        comment="Pricing date — Hora Día",
    )
    hour: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Hour of day 0–23 — Hora % 24",
    )
    tariff: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="Electricity tariff access type, e.g. '2.0TD' — Peaje",
    )
    period: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Pricing period number — Periodo",
    )

    # PVPC total and top-level split
    feu: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="PVPC final energy price FEU = TEU + TCU (€/MWh consumed) — "
        "Término energía PVPC FEU",
    )
    teu: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Tolls and charges component TEU (€/MWh consumed) — "
        "Peajes y cargos TEU",
    )
    tcu: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Production price adjusted for network losses TCU = CP×(1+PERD/100) "
        "(€/MWh consumed) — Precio producción TCU",
    )

    # Loss coefficients
    perd: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="PVPC loss coefficient % — Coeficiente pérdidas PVPC PERD",
    )
    perd_std: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Standard loss coefficient % — % coeficiente pérdidas estándar",
    )

    # Production cost breakdown
    cp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Total production cost CP (€/MWh bc) — Total Coste producción CP",
    )
    oc: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Other costs total OC (€/MWh bc) — Otros costes Total OC",
    )
    os_fin: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="OS financing cost (€/MWh bc) — Financiación OS",
    )
    om_fin: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="OM financing cost (€/MWh bc) — Financiación OM",
    )
    cap: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Capacity charge (€/MWh bc) — Cargo capacidad",
    )
    interrup: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Interruptibility service cost (€/MWh bc) — Servicio interrumpibilidad",
    )
    renew_bal: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Renewable auctions surplus/deficit (€/MWh bc) — "
        "Excedente o deficit subastas renovables",
    )

    # Commercialization costs (CCVh)
    ccv_rcv: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Commercialization cost RCVtovph (€/MWh bc) — CCVh RCVtovph",
    )
    ccv_rfe: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Commercialization cost RFE (€/MWh bc) — CCVh RFE",
    )
    ccv_rmr: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Commercialization cost RMRv (€/MWh bc) — CCVh RMRv",
    )
    ccv_ru: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Unit commercialization cost Runitaria (€/MWh bc) — CCVh Runitaria",
    )

    # System adjustment markets
    sah: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="System adjustment total SAH (€/MWh bc) — Total SAH",
    )
    adj_other: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="System adjustment other markets (€/MWh bc) — "
        "Mercados ajuste sistema Otros sistema",
    )
    dev_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Deviation cost (€/MWh bc) — Coste desvíos",
    )
    band_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Band service cost (€/MWh bc) — Coste banda",
    )
    dem_resp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Active demand response cost (€/MWh) — Coste respuesta activa demanda",
    )
    tech_rest: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Daily technical restrictions cost (€/MWh bc) — "
        "Coste restricciones técnicas diario",
    )

    # Market prices
    pmh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Daily + intraday markets total PMH (€/MWh bc) — "
        "Mercados diario e intradiario 1 Total PMH",
    )
    intra1: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Intraday market component 1 (€/MWh bc) — Componente intradiario 1",
    )
    spot: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Day-ahead spot market price (€/MWh bc) — Mercado diario",
    )
    tah: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Forward markets total TAH (€/MWh bc) — Mercados a plazo Total TAH",
    )
    futures: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Futures market component (€/MWh) — Componente Mercados a futuro",
    )

    # Correction and profile factors
    fch: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Energy correction factor FCh — Factor corrección por energía FCh",
    )
    profile: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Profile coefficient — Perfil Coeficiente perfilado",
    )

    # Derived
    price_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Final PVPC price in €/kWh — FEU / 1000",
    )
