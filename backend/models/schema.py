from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from core.db import Base
import enum
import uuid

class WaterBodyType(enum.Enum):
    RIVER = "River"
    LAKE = "Lake"
    COASTAL = "Coastal"

class Location(Base):
    __tablename__ = "locations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    geom = Column(Geometry('POINT', srid=4326))
    water_body_type = Column(Enum(WaterBodyType))
    galileo_reference_id = Column(String, nullable=True)

# Add remaining models as discussed in architecture
