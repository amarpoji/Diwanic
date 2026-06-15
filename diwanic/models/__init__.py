from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from diwanic.app.database import Base


class Poet(Base):
    __tablename__ = "poets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(255), unique=True, nullable=False)
    name_ar = Column(String(255), nullable=False)
    era = Column(String(255))
    bio_ar = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    poems = relationship("Poem", back_populates="poet", cascade="all, delete-orphan")


class Poem(Base):
    __tablename__ = "poems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poet_id = Column(UUID(as_uuid=True), ForeignKey("poets.id", ondelete="CASCADE"))
    title = Column(String(512), nullable=False)
    title_searchable = Column(String(512))
    original_text = Column(Text, nullable=False)
    searchable_text = Column(Text, nullable=False)
    meter = Column(String(128))
    rhyme = Column(String(128))
    category = Column(String(255))
    source_url = Column(Text, unique=True)
    website = Column(String(50), default="aldiwan")
    scraped_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    poet = relationship("Poet", back_populates="poems")
    verses = relationship("Verse", back_populates="poem", cascade="all, delete-orphan")


class Verse(Base):
    __tablename__ = "verses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poem_id = Column(UUID(as_uuid=True), ForeignKey("poems.id", ondelete="CASCADE"))
    verse_index = Column(Integer, nullable=False)
    original_text = Column(Text, nullable=False)
    searchable_text = Column(Text, nullable=False)

    poem = relationship("Poem", back_populates="verses")