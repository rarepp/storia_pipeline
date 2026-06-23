# database.py
import re
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class Property(Base):
    __tablename__ = 'properties'

    storia_id = Column(String(50), primary_key=True)
    title = Column(String(255))
    neighborhood = Column(String(100))
    rooms = Column(Integer)
    surface_m2 = Column(Numeric(6, 2))
    link = Column(String(512), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    prices = relationship("PriceHistory", back_populates="property", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    storia_id = Column(String(50), ForeignKey('properties.storia_id', ondelete="CASCADE"))
    price_eur = Column(Numeric(12, 2))
    price_per_m2 = Column(Numeric(10, 2))
    recorded_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="prices")


# Local SQLite connection string
DATABASE_URL = "sqlite:///storia_market_telemetry.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Generates the .db file and tables automatically if they don't exist."""
    Base.metadata.create_all(bind=engine)


def save_daily_snapshot(properties_list):
    """Saves or updates crawled properties in the SQLite database."""
    if not properties_list:
        print("[-] Database update skipped: No properties collected.")
        return

    init_db()
    session = SessionLocal()

    new_properties_counter = 0
    price_changes_counter = 0
    now = datetime.utcnow()

    try:
        for p in properties_list:
            link = p["Link Proprietate"]

            # Extract the unique Storia ID token (e.g., IDHvsX) from the URL
            match = re.search(r'-([iI][dD][a-zA-Z0-9]+)(?:[\?#&]|$)', link)
            storia_id = match.group(1).upper() if match else link[-15:]

            # Look up if this property exists already
            existing_property = session.query(Property).filter(Property.storia_id == storia_id).first()

            if not existing_property:
                # New entry discovered
                new_prop = Property(
                    storia_id=storia_id,
                    title=p.get("Titlu Anunt", "Apartament"),
                    neighborhood=p["Cartier"],
                    rooms=p["Camere"],
                    surface_m2=p["Suprafata (m2)"],
                    link=link,
                    created_at=now,
                    last_seen_at=now,
                    is_active=True
                )
                session.add(new_prop)

                new_price = PriceHistory(
                    storia_id=storia_id,
                    price_eur=p["Pret Total (EUR)"],
                    price_per_m2=p["Pret/m2 (EUR)"],
                    recorded_at=now
                )
                session.add(new_price)
                new_properties_counter += 1
            else:
                # Property exists; update its tracking heartbeat
                existing_property.last_seen_at = now
                existing_property.is_active = True

                # Check for historical price shifts
                latest_price_record = session.query(PriceHistory) \
                    .filter(PriceHistory.storia_id == storia_id) \
                    .order_by(PriceHistory.recorded_at.desc()).first()

                if latest_price_record and float(latest_price_record.price_eur) != float(p["Pret Total (EUR)"]):
                    updated_price = PriceHistory(
                        storia_id=storia_id,
                        price_eur=p["Pret Total (EUR)"],
                        price_per_m2=p["Pret/m2 (EUR)"],
                        recorded_at=now
                    )
                    session.add(updated_price)
                    price_changes_counter += 1

        session.commit()
        print(
            f"[Database] Sync complete: Added {new_properties_counter} new items. Tracked {price_changes_counter} price drops/increases.")

    except Exception as e:
        session.rollback()
        print(f"[-] Database operation crashed: {e}")
    finally:
        session.close()