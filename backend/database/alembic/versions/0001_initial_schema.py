"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-10 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default=sa.text("'txt'")),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("cover_url", sa.String(length=1024), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_books_title"), "books", ["title"], unique=False)

    op.create_table(
        "source_files",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.String(length=1024), nullable=True),
        sa.Column("file_hash", sa.String(length=128), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("raw_text_url", sa.String(length=1024), nullable=True),
        sa.Column("ocr_text_url", sa.String(length=1024), nullable=True),
        sa.Column("parse_status", sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_source_files_book_id"), "source_files", ["book_id"], unique=False)
    op.create_index(op.f("ix_source_files_file_hash"), "source_files", ["file_hash"], unique=False)

    op.create_table(
        "chapters",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_file_id", sa.String(length=36), sa.ForeignKey("source_files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chapter_no", sa.Integer(), nullable=False),
        sa.Column("chapter_title", sa.String(length=255), nullable=False),
        sa.Column("chapter_range", sa.String(length=128), nullable=True),
        sa.Column("story_time", sa.String(length=128), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("parser_type", sa.String(length=100), nullable=True),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_chapters_book_id"), "chapters", ["book_id"], unique=False)
    op.create_index(op.f("ix_chapters_chapter_no"), "chapters", ["chapter_no"], unique=False)
    op.create_index(op.f("ix_chapters_source_file_id"), "chapters", ["source_file_id"], unique=False)

    op.create_table(
        "characters",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=True),
        sa.Column("role_type", sa.String(length=100), nullable=True),
        sa.Column("first_appearance_chapter_id", sa.String(length=36), sa.ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("static_profile_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("dynamic_profile_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'active'")),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_characters_book_id"), "characters", ["book_id"], unique=False)
    op.create_index(op.f("ix_characters_name"), "characters", ["name"], unique=False)

    op.create_table(
        "world_locations",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location_type", sa.String(length=100), nullable=True),
        sa.Column("related_chapter_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_world_locations_book_id"), "world_locations", ["book_id"], unique=False)
    op.create_index(op.f("ix_world_locations_name"), "world_locations", ["name"], unique=False)

    op.create_table(
        "chapter_extractions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chapter_id", sa.String(length=36), sa.ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("extractor_type", sa.String(length=100), nullable=True),
        sa.Column("extraction_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("embedding_vector", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("prompt_version", sa.String(length=100), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_span", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("extractor_version", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_chapter_extractions_book_id"), "chapter_extractions", ["book_id"], unique=False)
    op.create_index(op.f("ix_chapter_extractions_chapter_id"), "chapter_extractions", ["chapter_id"], unique=False)

    op.create_table(
        "character_versions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("character_id", sa.String(length=36), sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("chapter_range", sa.String(length=128), nullable=True),
        sa.Column("profile_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_character_versions_book_id"), "character_versions", ["book_id"], unique=False)
    op.create_index(op.f("ix_character_versions_character_id"), "character_versions", ["character_id"], unique=False)

    op.create_table(
        "items",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_character_id", sa.String(length=36), sa.ForeignKey("characters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("first_appearance_chapter_id", sa.String(length=36), sa.ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("item_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_items_book_id"), "items", ["book_id"], unique=False)
    op.create_index(op.f("ix_items_name"), "items", ["name"], unique=False)

    op.create_table(
        "storyline_events",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chapter_id", sa.String(length=36), sa.ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_title", sa.String(length=255), nullable=False),
        sa.Column("event_summary", sa.Text(), nullable=True),
        sa.Column("participants_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("location_id", sa.String(length=36), sa.ForeignKey("world_locations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_time", sa.String(length=128), nullable=True),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_storyline_events_book_id"), "storyline_events", ["book_id"], unique=False)
    op.create_index(op.f("ix_storyline_events_chapter_id"), "storyline_events", ["chapter_id"], unique=False)

    op.create_table(
        "media_assets",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_character_id", sa.String(length=36), sa.ForeignKey("characters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("asset_type", sa.String(length=100), nullable=False),
        sa.Column("object_url", sa.String(length=1024), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("tags_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("embedding_vector", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_media_assets_book_id"), "media_assets", ["book_id"], unique=False)

    op.create_table(
        "extraction_tasks",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("progress", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("current_stage", sa.String(length=255), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("filter_noise", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("output_file", sa.String(length=1024), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("task_meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_extraction_tasks_book_id"), "extraction_tasks", ["book_id"], unique=False)

    op.create_table(
        "task_logs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("extraction_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_level", sa.String(length=20), nullable=False, server_default=sa.text("'info'")),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_task_logs_task_id"), "task_logs", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_logs_task_id"), table_name="task_logs")
    op.drop_table("task_logs")

    op.drop_index(op.f("ix_extraction_tasks_book_id"), table_name="extraction_tasks")
    op.drop_table("extraction_tasks")

    op.drop_index(op.f("ix_media_assets_book_id"), table_name="media_assets")
    op.drop_table("media_assets")

    op.drop_index(op.f("ix_storyline_events_chapter_id"), table_name="storyline_events")
    op.drop_index(op.f("ix_storyline_events_book_id"), table_name="storyline_events")
    op.drop_table("storyline_events")

    op.drop_index(op.f("ix_items_name"), table_name="items")
    op.drop_index(op.f("ix_items_book_id"), table_name="items")
    op.drop_table("items")

    op.drop_index(op.f("ix_character_versions_character_id"), table_name="character_versions")
    op.drop_index(op.f("ix_character_versions_book_id"), table_name="character_versions")
    op.drop_table("character_versions")

    op.drop_index(op.f("ix_chapter_extractions_chapter_id"), table_name="chapter_extractions")
    op.drop_index(op.f("ix_chapter_extractions_book_id"), table_name="chapter_extractions")
    op.drop_table("chapter_extractions")

    op.drop_index(op.f("ix_world_locations_name"), table_name="world_locations")
    op.drop_index(op.f("ix_world_locations_book_id"), table_name="world_locations")
    op.drop_table("world_locations")

    op.drop_index(op.f("ix_characters_name"), table_name="characters")
    op.drop_index(op.f("ix_characters_book_id"), table_name="characters")
    op.drop_table("characters")

    op.drop_index(op.f("ix_chapters_source_file_id"), table_name="chapters")
    op.drop_index(op.f("ix_chapters_chapter_no"), table_name="chapters")
    op.drop_index(op.f("ix_chapters_book_id"), table_name="chapters")
    op.drop_table("chapters")

    op.drop_index(op.f("ix_source_files_file_hash"), table_name="source_files")
    op.drop_index(op.f("ix_source_files_book_id"), table_name="source_files")
    op.drop_table("source_files")

    op.drop_index(op.f("ix_books_title"), table_name="books")
    op.drop_table("books")