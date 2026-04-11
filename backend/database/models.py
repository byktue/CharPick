from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid_str() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Book(TimestampMixin, Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="txt")
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    cover_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_files: Mapped[list["SourceFile"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    chapters: Mapped[list["Chapter"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    chapter_extractions: Mapped[list["ChapterExtraction"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    characters: Mapped[list["Character"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    items: Mapped[list["Item"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    storyline_events: Mapped[list["StorylineEvent"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    world_locations: Mapped[list["WorldLocation"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    character_versions: Mapped[list["CharacterVersion"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    media_assets: Mapped[list["MediaAsset"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    tasks: Mapped[list["ExtractionTask"]] = relationship(back_populates="book", cascade="all, delete-orphan")


class SourceFile(TimestampMixin, Base):
    __tablename__ = "source_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_text_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    ocr_text_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    parse_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    book: Mapped["Book"] = relationship(back_populates="source_files")
    chapters: Mapped[list["Chapter"]] = relationship(back_populates="source_file")


class Chapter(TimestampMixin, Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    source_file_id: Mapped[Optional[str]] = mapped_column(ForeignKey("source_files.id", ondelete="SET NULL"), nullable=True, index=True)
    chapter_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    chapter_title: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter_range: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    story_time: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parser_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    book: Mapped["Book"] = relationship(back_populates="chapters")
    source_file: Mapped[Optional["SourceFile"]] = relationship(back_populates="chapters")
    chapter_extractions: Mapped[list["ChapterExtraction"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
    storyline_events: Mapped[list["StorylineEvent"]] = relationship(back_populates="chapter")


class ChapterExtraction(TimestampMixin, Base):
    __tablename__ = "chapter_extractions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    extractor_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extraction_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    embedding_vector: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_span: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    extractor_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    book: Mapped["Book"] = relationship(back_populates="chapter_extractions")
    chapter: Mapped["Chapter"] = relationship(back_populates="chapter_extractions")


class Character(TimestampMixin, Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    alias: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_appearance_chapter_id: Mapped[Optional[str]] = mapped_column(ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)
    static_profile_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    dynamic_profile_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    prompt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    book: Mapped["Book"] = relationship(back_populates="characters")
    versions: Mapped[list["CharacterVersion"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    media_assets: Mapped[list["MediaAsset"]] = relationship(back_populates="source_character")


class CharacterVersion(TimestampMixin, Base):
    __tablename__ = "character_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    chapter_range: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    profile_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    prompt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    character: Mapped["Character"] = relationship(back_populates="versions")
    book: Mapped["Book"] = relationship(back_populates="character_versions")


class Item(TimestampMixin, Base):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_character_id: Mapped[Optional[str]] = mapped_column(ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)
    first_appearance_chapter_id: Mapped[Optional[str]] = mapped_column(ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)
    item_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    book: Mapped["Book"] = relationship(back_populates="items")


class StorylineEvent(TimestampMixin, Base):
    __tablename__ = "storyline_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id: Mapped[Optional[str]] = mapped_column(ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True, index=True)
    event_title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    participants_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    location_id: Mapped[Optional[str]] = mapped_column(ForeignKey("world_locations.id", ondelete="SET NULL"), nullable=True)
    event_time: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    book: Mapped["Book"] = relationship(back_populates="storyline_events")
    chapter: Mapped[Optional["Chapter"]] = relationship(back_populates="storyline_events")


class WorldLocation(TimestampMixin, Base):
    __tablename__ = "world_locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    related_chapter_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    book: Mapped["Book"] = relationship(back_populates="world_locations")


class MediaAsset(TimestampMixin, Base):
    __tablename__ = "media_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    source_character_id: Mapped[Optional[str]] = mapped_column(ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(100), nullable=False)
    object_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    tags_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    embedding_vector: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    book: Mapped["Book"] = relationship(back_populates="media_assets")
    source_character: Mapped[Optional["Character"]] = relationship(back_populates="media_assets")


class ExtractionTask(TimestampMixin, Base):
    __tablename__ = "extraction_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    book_id: Mapped[Optional[str]] = mapped_column(ForeignKey("books.id", ondelete="SET NULL"), nullable=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_stage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prompt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    filter_noise: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    output_file: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    task_meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    book: Mapped[Optional["Book"]] = relationship(back_populates="tasks")
    logs: Mapped[list["TaskLog"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class TaskLog(TimestampMixin, Base):
    __tablename__ = "task_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    task_id: Mapped[str] = mapped_column(ForeignKey("extraction_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    log_level: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    task: Mapped["ExtractionTask"] = relationship(back_populates="logs")